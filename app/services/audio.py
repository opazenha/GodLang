"""Audio processing pipeline service.

Async file-based pipeline:
- FFmpeg captures audio and writes chunks to pending/
- File watcher detects new files and queues for processing
- Worker processes chunks through transcription
- Failure handling with retries and recovery
"""

import asyncio
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from app.config import AudioConfig
from app.services.database import save_transcription, save_translation, DatabaseError
from app.services.groq_client import (
    transcribe_audio,
    translate_text,
    RetryableTranscriptionError,
    RetryableTranslationError,
    TranscriptionError,
    TranslationError,
)
from app.models.schemas import LanguageCode

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class AudioChunk:
    """Represents an audio chunk file."""

    path: Path
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def is_dead(self) -> bool:
        return self.retry_count >= AudioConfig.MAX_RETRIES

    def increment_retry(self) -> "AudioChunk":
        """Return new chunk with incremented retry count."""
        return AudioChunk(
            path=self.path,
            created_at=self.created_at,
            retry_count=self.retry_count + 1,
        )


class AudioPipelineError(Exception):
    """Base exception for audio pipeline errors."""

    pass


class RetryableError(AudioPipelineError):
    """Error that can be retried."""

    pass


class MaxRetriesExceeded(AudioPipelineError):
    """Max retries exceeded for a chunk."""

    pass


# =============================================================================
# Directory Management
# =============================================================================


class DirectoryManager:
    """Manages audio processing directories."""

    def __init__(self):
        self.dirs = AudioConfig.get_all_dirs()

    def setup(self) -> None:
        """Create all required directories."""
        for name, path in self.dirs.items():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {path}")

    def get_pending(self) -> Path:
        return self.dirs["pending"]

    def get_processing(self) -> Path:
        return self.dirs["processing"]

    def get_failed(self) -> Path:
        return self.dirs["failed"]

    def move_to_processing(self, chunk: AudioChunk) -> AudioChunk:
        """Atomically move chunk from pending to processing."""
        dest = self.get_processing() / chunk.filename
        shutil.move(str(chunk.path), str(dest))
        logger.debug(f"Moved to processing: {chunk.filename}")
        return AudioChunk(
            path=dest, created_at=chunk.created_at, retry_count=chunk.retry_count
        )

    def move_to_failed(self, chunk: AudioChunk) -> AudioChunk:
        """Move chunk to failed directory with retry count in filename."""
        stem = chunk.path.stem
        suffix = chunk.path.suffix

        if chunk.is_dead:
            new_name = f"{stem}.dead{suffix}"
        else:
            new_name = f"{stem}_retry{chunk.retry_count}{suffix}"

        dest = self.get_failed() / new_name
        shutil.move(str(chunk.path), str(dest))
        logger.warning(f"Moved to failed: {new_name}")
        return AudioChunk(
            path=dest, created_at=chunk.created_at, retry_count=chunk.retry_count
        )

    def move_to_pending(self, chunk: AudioChunk) -> AudioChunk:
        """Move chunk back to pending for retry."""
        new_chunk = chunk.increment_retry()
        stem = chunk.path.stem.rsplit("_retry", 1)[0]  # Remove old retry suffix
        suffix = chunk.path.suffix
        new_name = f"{stem}_retry{new_chunk.retry_count}{suffix}"

        dest = self.get_pending() / new_name
        shutil.move(str(chunk.path), str(dest))
        logger.info(f"Moved back to pending for retry: {new_name}")
        return AudioChunk(
            path=dest, created_at=chunk.created_at, retry_count=new_chunk.retry_count
        )

    def delete_chunk(self, chunk: AudioChunk) -> None:
        """Delete a processed chunk."""
        if chunk.path.exists():
            chunk.path.unlink()
            logger.debug(f"Deleted chunk: {chunk.filename}")

    def recover_processing(self) -> list[AudioChunk]:
        """Recover files left in processing/ after crash."""
        recovered = []
        for path in self.get_processing().glob(f"*.{AudioConfig.FORMAT}"):
            chunk = AudioChunk(path=path)
            moved = self.move_to_pending(chunk)
            recovered.append(moved)
        if recovered:
            logger.info(f"Recovered {len(recovered)} chunks from processing/")
        return recovered

    def scan_pending(self) -> list[AudioChunk]:
        """Scan pending/ for existing files."""
        chunks = []
        for path in sorted(self.get_pending().glob(f"*.{AudioConfig.FORMAT}")):
            chunks.append(AudioChunk(path=path))
        return chunks

    def cleanup_old_files(self) -> int:
        """Delete files older than TTL. Returns count of deleted files."""
        deleted = 0
        cutoff = time.time() - AudioConfig.FILE_TTL

        for dir_path in self.dirs.values():
            for path in dir_path.glob("*"):
                if path.is_file() and path.stat().st_mtime < cutoff:
                    path.unlink()
                    deleted += 1
                    logger.debug(f"Cleaned up old file: {path.name}")

        if deleted:
            logger.info(f"Cleanup: deleted {deleted} old files")
        return deleted


# =============================================================================
# FFmpeg Capture
# =============================================================================


class FFmpegCapture:
    """Manages FFmpeg audio capture process."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.process: Optional[subprocess.Popen] = None
        self._running = False

    def _build_command(self) -> list[str]:
        """Build FFmpeg command for current platform."""
        fmt, device = AudioConfig.get_audio_input()
        output_pattern = str(self.output_dir / f"%Y%m%d_%H%M%S.{AudioConfig.FORMAT}")

        cmd = [
            "ffmpeg",
            "-f",
            fmt,
            "-i",
            device,
            "-ar",
            str(AudioConfig.SAMPLE_RATE),
            "-ac",
            str(AudioConfig.CHANNELS),
            "-c:a",
            "flac",  # FLAC codec for lossless compression since WAV file was being too large
            "-f",
            "segment",
            "-segment_time",
            str(AudioConfig.CHUNK_DURATION),
            "-strftime",
            "1",
            "-y",  # Overwrite without asking for possible asynchronous processing
            output_pattern,
        ]
        return cmd

    def start(self) -> None:
        """Start FFmpeg capture process."""
        if self._running:
            logger.warning("FFmpeg capture already running")
            return

        cmd = self._build_command()
        logger.info(f"Starting FFmpeg capture: {' '.join(cmd)}")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._running = True
        logger.info(f"FFmpeg capture started (PID: {self.process.pid})")

    def stop(self) -> None:
        """Stop FFmpeg capture process gracefully."""
        if not self._running or not self.process:
            return

        logger.info("Stopping FFmpeg capture...")
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning("FFmpeg did not terminate, killing...")
            self.process.kill()
            self.process.wait()

        self._running = False
        logger.info("FFmpeg capture stopped")

    def is_running(self) -> bool:
        """Check if FFmpeg is still running."""
        if not self.process:
            return False
        return self.process.poll() is None

    def get_command_string(self) -> str:
        """Get the FFmpeg command as a string (for manual execution)."""
        return " ".join(self._build_command())


# =============================================================================
# File Watcher
# =============================================================================


class FileWatcher:
    """Watches pending/ directory for new audio chunks."""

    def __init__(
        self,
        watch_dir: Path,
        queue: asyncio.Queue,
        stability_wait: float = AudioConfig.STABILITY_WAIT,
    ):
        self.watch_dir = watch_dir
        self.queue = queue
        self.stability_wait = stability_wait
        self._running = False
        self._known_files: set[Path] = set()

    async def _wait_for_stable(self, path: Path) -> bool:
        """Wait for file to stop being written to."""
        if not path.exists():
            return False

        prev_size = -1
        stable_count = 0

        while stable_count < 2:  # Need 2 consecutive stable checks
            await asyncio.sleep(self.stability_wait / 2)
            if not path.exists():
                return False

            current_size = path.stat().st_size
            if current_size == prev_size and current_size > 0:
                stable_count += 1
            else:
                stable_count = 0
            prev_size = current_size

        return True

    async def _scan_once(self) -> None:
        """Scan directory once for new files."""
        current_files = set(self.watch_dir.glob(f"*.{AudioConfig.FORMAT}"))
        new_files = current_files - self._known_files

        for path in sorted(new_files):
            if await self._wait_for_stable(path):
                chunk = AudioChunk(path=path)
                await self.queue.put(chunk)
                logger.debug(f"Queued new chunk: {chunk.filename}")
            self._known_files.add(path)

        # Clean up known files that no longer exist
        self._known_files = self._known_files & current_files

    async def start(self, poll_interval: float = 1.0) -> None:
        """Start watching for new files."""
        self._running = True
        logger.info(f"File watcher started: {self.watch_dir}")

        while self._running:
            try:
                await self._scan_once()
                await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"File watcher error: {e}")
                await asyncio.sleep(poll_interval)

        logger.info("File watcher stopped")

    def stop(self) -> None:
        """Stop the file watcher."""
        self._running = False


# =============================================================================
# Audio Pipeline
# =============================================================================


class AudioPipeline:
    """Main audio processing pipeline orchestrator."""

    def __init__(
        self,
        process_fn: Optional[Callable[[AudioChunk], asyncio.Future]] = None,
    ):
        self.dir_manager = DirectoryManager()
        self.queue: asyncio.Queue[AudioChunk] = asyncio.Queue()
        self.watcher: Optional[FileWatcher] = None
        self.capture: Optional[FFmpegCapture] = None
        self.process_fn = process_fn
        self._running = False
        self._tasks: list[asyncio.Task] = []

    def setup(self) -> None:
        """Initialize directories and recover any crashed state."""
        self.dir_manager.setup()
        self.dir_manager.recover_processing()

        # Queue existing pending files
        for chunk in self.dir_manager.scan_pending():
            self.queue.put_nowait(chunk)
            logger.info(f"Queued existing chunk: {chunk.filename}")

    async def _process_worker(self) -> None:
        """Worker that processes chunks from the queue."""
        while self._running:
            try:
                chunk = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                # Move to processing
                chunk = self.dir_manager.move_to_processing(chunk)

                # Process the chunk
                if self.process_fn:
                    await self.process_fn(chunk)
                else:
                    # Mock processing for testing
                    logger.info(f"Processing chunk (mock): {chunk.filename}")
                    await asyncio.sleep(0.5)

                # Success: delete the chunk
                self.dir_manager.delete_chunk(chunk)
                logger.info(f"Successfully processed: {chunk.filename}")

            except RetryableError as e:
                logger.warning(f"Retryable error for {chunk.filename}: {e}")
                if chunk.retry_count < AudioConfig.MAX_RETRIES:
                    self.dir_manager.move_to_pending(chunk)
                else:
                    self.dir_manager.move_to_failed(chunk)
                    logger.error(f"Max retries exceeded: {chunk.filename}")

            except Exception as e:
                logger.error(f"Error processing {chunk.filename}: {e}")
                self.dir_manager.move_to_failed(chunk)

            finally:
                self.queue.task_done()

    async def _cleanup_worker(self) -> None:
        """Periodic cleanup of old files."""
        while self._running:
            try:
                await asyncio.sleep(AudioConfig.CLEANUP_INTERVAL)
                self.dir_manager.cleanup_old_files()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def start(self, start_capture: bool = False) -> None:
        """Start the audio pipeline.

        Args:
            start_capture: If True, also start FFmpeg capture.
                          Set to False if running FFmpeg externally.
        """
        self.setup()
        self._running = True

        # Start file watcher
        self.watcher = FileWatcher(self.dir_manager.get_pending(), self.queue)
        watcher_task = asyncio.create_task(self.watcher.start())
        self._tasks.append(watcher_task)

        # Start process worker
        worker_task = asyncio.create_task(self._process_worker())
        self._tasks.append(worker_task)

        # Start cleanup worker
        cleanup_task = asyncio.create_task(self._cleanup_worker())
        self._tasks.append(cleanup_task)

        # Optionally start FFmpeg capture
        if start_capture:
            self.capture = FFmpegCapture(self.dir_manager.get_pending())
            self.capture.start()

        logger.info("Audio pipeline started")

    async def stop(self) -> None:
        """Stop the audio pipeline."""
        self._running = False

        if self.watcher:
            self.watcher.stop()

        if self.capture:
            self.capture.stop()

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

        logger.info("Audio pipeline stopped")

    def get_ffmpeg_command(self) -> str:
        """Get FFmpeg command for manual execution."""
        capture = FFmpegCapture(self.dir_manager.get_pending())
        return capture.get_command_string()


# =============================================================================
# Transcription Processing
# =============================================================================


async def process_audio_chunk_transcription(chunk: AudioChunk, session_id: str) -> None:
    """Process an audio chunk through transcription pipeline.

    Args:
        chunk: AudioChunk to process.
        session_id: Session ID for the transcription.

    Raises:
        RetryableError: If transcription failed but can be retried.
        AudioPipelineError: If transcription failed permanently.
    """
    try:
        # Transcribe the audio chunk
        transcription = await transcribe_audio(chunk.path, session_id)

        # Save to database
        transcription_id = await save_transcription(transcription)

        logger.info(
            f"Successfully processed {chunk.filename} -> transcription {transcription_id}"
        )

    except RetryableTranscriptionError as e:
        logger.warning(f"Retryable transcription error for {chunk.filename}: {e}")
        raise RetryableError(f"Transcription retryable: {e}") from e

    except TranscriptionError as e:
        logger.error(f"Transcription failed for {chunk.filename}: {e}")
        raise AudioPipelineError(f"Transcription failed: {e}") from e

    except DatabaseError as e:
        logger.error(f"Database error for {chunk.filename}: {e}")
        # Database errors are typically retryable
        raise RetryableError(f"Database error: {e}") from e

    except Exception as e:
        logger.error(f"Unexpected error processing {chunk.filename}: {e}")
        raise AudioPipelineError(f"Unexpected error: {e}") from e


async def process_translation_pipeline(
    transcription_text: str,
    transcription_id: str,
    target_language: LanguageCode = LanguageCode.CHINESE,
) -> None:
    """Process translation pipeline for a transcription.

    Args:
        transcription_text: English text to translate.
        transcription_id: ID of the source transcription.
        target_language: Target language for translation.

    Raises:
        RetryableError: If translation failed but can be retried.
        AudioPipelineError: If translation failed permanently.
    """
    try:
        # Translate the transcription
        translation = await translate_text(
            transcription_text, transcription_id, target_language
        )

        # Save to database
        translation_id = await save_translation(translation)

        logger.info(
            f"Successfully translated transcription {transcription_id} -> translation {translation_id}"
        )

    except RetryableTranslationError as e:
        logger.warning(f"Retryable translation error: {e}")
        raise RetryableError(f"Translation retryable: {e}") from e

    except TranslationError as e:
        logger.error(f"Translation failed: {e}")
        raise AudioPipelineError(f"Translation failed: {e}") from e

    except DatabaseError as e:
        logger.error(f"Database error during translation: {e}")
        # Database errors are typically retryable
        raise RetryableError(f"Database error: {e}") from e

    except Exception as e:
        logger.error(f"Unexpected error during translation: {e}")
        raise AudioPipelineError(f"Unexpected error: {e}") from e


# =============================================================================
# Convenience Functions
# =============================================================================


def get_ffmpeg_command() -> str:
    """Get the FFmpeg command for the current platform."""
    dir_manager = DirectoryManager()
    dir_manager.setup()
    capture = FFmpegCapture(dir_manager.get_pending())
    return capture.get_command_string()


def list_audio_devices() -> str:
    """Get command to list audio devices for current platform."""
    import platform as plat

    if plat.system() == "Windows":
        return "ffmpeg -list_devices true -f dshow -i dummy"
    return "pactl list sources short"
