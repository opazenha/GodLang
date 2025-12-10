# Epic 2: Audio Processing Pipeline

[← Back to PRD](../PRD.md)

---

## Description

Async file-based audio pipeline that captures audio via FFmpeg, writes chunks to disk, and processes them through a file watcher. No HTTP endpoint required—FFmpeg writes directly to a watched directory.

**Expected Outcome:** System continuously captures audio, chunks it, and queues chunks for transcription via file system events.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        Audio Capture Layer                          │
│  ┌─────────────────┐                                                │
│  │ FFmpeg Process  │  Captures from:                                │
│  │ (continuous)    │  - Mixing board (production)                   │
│  │                 │  - Laptop mic (dev/test)                       │
│  └────────┬────────┘                                                │
│           │ writes 10s chunks                                       │
│           ▼                                                         │
│  /tmp/godlang/pending/                                              │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      File Watcher (watchdog)                        │
│  - Detects new .flac files in pending/                               │
│  - Waits for file to stabilize (not still being written)            │
│  - Moves to processing/ and queues for transcription                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Transcription Worker                           │
│  - Reads chunk from processing/                                     │
│  - Calls Groq API                                                   │
│  - On success: deletes file                                         │
│  - On failure: moves to failed/ with retry logic                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```text
/tmp/godlang/               # Linux (dev)
C:\Temp\godlang\            # Windows (production)

├── pending/                # FFmpeg writes chunks here
├── processing/             # File being transcribed
├── failed/                 # Failed after max retries
└── manifest.json           # Optional: metadata tracking
```

**Filename Convention:** `{YYYYMMDD}_{HHMMSS}.flac`  
Example: `20241210_143052.flac`

---

## Platform Configuration

| Setting | Linux (Arch - Dev) | Windows (Production) |
|---------|-------------------|---------------------|
| Temp dir | `/tmp/godlang/` | `C:\Temp\godlang\` |
| Audio input | `pulse` (PulseAudio) | `dshow` (DirectShow) |
| FFmpeg device | `default` or mic name | Mixing board device |

---

## 2.1 FFmpeg Audio Capture

- [x] **2.1.1** Create FFmpeg capture script with platform detection
- [x] **2.1.2** Configure chunk duration (10 seconds recommended)
- [x] **2.1.3** Define audio format: 16kHz mono FLAC (Groq compatible)
- [x] **2.1.4** Implement graceful start/stop of capture process
- [x] **2.1.5** Add device listing utility for both platforms

> 💬 Notes:
>
> - Groq Whisper accepts: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
> - 16kHz mono FLAC is optimal (lossless compression, smaller than WAV)
> - Max file size: 25MB free tier, 100MB dev tier
> - 10s @ 16kHz mono FLAC ≈ 80-100KB (vs ~320KB for WAV)

### FFmpeg Commands

**Linux (dev - laptop mic):**

```bash
ffmpeg -f pulse -i default \
  -ar 16000 -ac 1 -c:a flac \
  -f segment -segment_time 10 \
  -strftime 1 \
  /tmp/godlang/pending/%Y%m%d_%H%M%S.flac
```

**Windows (production - mixing board):**

```cmd
ffmpeg -f dshow -i audio="Mixing Board Device Name" ^
  -ar 16000 -ac 1 -c:a flac ^
  -f segment -segment_time 10 ^
  -strftime 1 ^
  C:\Temp\godlang\pending\%%Y%%m%%d_%%H%%M%%S.flac
```

**List audio devices:**

```bash
# Linux
pactl list sources short

# Windows
ffmpeg -list_devices true -f dshow -i dummy
```

---

## 2.2 File Watcher Service

- [x] **2.2.1** Install watchdog library
- [x] **2.2.2** Create async file watcher for pending/ directory
- [x] **2.2.3** Implement file stability check (wait for write completion)
- [x] **2.2.4** Queue files for processing via asyncio.Queue
- [x] **2.2.5** Handle watcher startup (process existing files in pending/)

> 💬 Notes:
>
> - Use `watchdog` library (cross-platform)
> - Check file size stability before processing (2s delay)
> - On startup, scan pending/ for unprocessed files

---

## 2.3 Temp File Management

- [x] **2.3.1** Create directory structure on startup
- [x] **2.3.2** Implement atomic file moves between directories
- [x] **2.3.3** Add TTL-based cleanup (delete files > 30 min old)
- [ ] **2.3.4** Implement disk space monitoring and alerts
- [-] **2.3.5** Create manifest.json for optional metadata tracking (not needed)

> 💬 Notes:
>
> - Use `shutil.move()` for atomic moves
> - Cleanup runs every 5 minutes
> - Alert if disk usage > 90%

---

## 2.4 Failure Handling & Recovery

- [x] **2.4.1** Implement retry logic with exponential backoff
- [x] **2.4.2** Move failed files to failed/ directory
- [x] **2.4.3** Mark files as dead after max retries (3)
- [x] **2.4.4** On process restart: recover files from processing/
- [x] **2.4.5** Log all failures with context for debugging

### Failure Matrix

| Failure Type | Action | Recovery |
|--------------|--------|----------|
| File incomplete | Wait for stability | Auto-retry after 2s |
| Groq API timeout | Move to failed/, retry | Exponential backoff |
| Groq API 4xx | Log error, mark dead | Manual review |
| Groq API 5xx | Move to failed/, retry | Exponential backoff |
| Max retries (3) | Rename to `.dead.flac` | Manual intervention |
| Process crash | Files left in processing/ | On restart: move back to pending/ |
| Disk full | Aggressive cleanup | Delete oldest files first |

---

## 2.5 Development Testing (Laptop Mic)

- [x] **2.5.1** Create dev capture script using PulseAudio
- [x] **2.5.2** Add test mode flag to use shorter chunks (5s)
- [x] **2.5.3** Create mock transcription service for offline testing
- [x] **2.5.4** Add verbose logging for debugging

### Quick Test Commands

```bash
# 1. Create directories
mkdir -p /tmp/godlang/{pending,processing,failed}

# 2. Start capture (in terminal 1)
ffmpeg -f pulse -i default -ar 16000 -ac 1 \
  -f segment -segment_time 5 -strftime 1 \
  /tmp/godlang/pending/%Y%m%d_%H%M%S_0.wav

# 3. Watch for files (in terminal 2)
watch -n 1 'ls -la /tmp/godlang/pending/'

# 4. Start the Flask app with watcher (in terminal 3)
docker-compose up
```

---

## Configuration

```python
# config.py additions
import platform
from pathlib import Path

class AudioConfig:
    CHUNK_DURATION = 10  # seconds
    SAMPLE_RATE = 16000  # Hz
    CHANNELS = 1  # mono
    FORMAT = "flac"  # FLAC for lossless compression
    
    MAX_RETRIES = 3
    STABILITY_WAIT = 2  # seconds
    CLEANUP_INTERVAL = 300  # 5 minutes
    FILE_TTL = 1800  # 30 minutes
    
    @classmethod
    def get_temp_dir(cls) -> Path:
        if platform.system() == "Windows":
            return Path("C:/Temp/godlang")
        return Path("/tmp/godlang")
    
    @classmethod
    def get_audio_input(cls) -> tuple[str, str]:
        """Returns (format, device) for FFmpeg."""
        if platform.system() == "Windows":
            return ("dshow", "audio=Mixing Board")  # Configure in .env
        return ("pulse", "default")
```

---

## Dependencies

Add to `requirements.txt`:

```txt
watchdog>=3.0.0
```

---

## Progress Log

### Session 2024-12-10

**Focus:** Architecture redesign - async file-based pipeline  
**Completed:**

- Documentation update with new approach
- `AudioConfig` class in `app/config.py` with platform detection
- `FFmpegCapture` class for audio capture management
- `FileWatcher` class with stability checks and async queue
- `DirectoryManager` for temp file operations
- `AudioPipeline` orchestrator with retry logic and cleanup
- Test script `scripts/test_audio_pipeline.py`
- Updated to FLAC format for smaller file sizes
- Tested with laptop mic successfully

**Blockers:** None  
**Next Steps:** Implement Epic 3 - Groq transcription integration  
