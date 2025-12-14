"""Broadcast state management for live transcription sessions.

Manages active broadcast sessions per language, tracking:
- Active session IDs
- Connected client counts
- Audio pipeline state
"""

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
from enum import Enum

from app.models.schemas import LanguageCode, SessionStatus, SessionModel
from app.services.database import save_session, update_session_status, get_session

logger = logging.getLogger(__name__)


class BroadcastStatus(str, Enum):
    """Broadcast status values."""
    IDLE = "idle"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPING = "stopping"


@dataclass
class BroadcastSession:
    """Represents an active broadcast for a language."""
    
    language: LanguageCode
    session_id: str
    status: BroadcastStatus = BroadcastStatus.IDLE
    client_count: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    audio_pid: Optional[int] = None  # FFmpeg process ID if running
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "language": self.language.value,
            "session_id": self.session_id,
            "status": self.status.value,
            "client_count": self.client_count,
            "started_at": self.started_at.isoformat(),
            "audio_active": self.audio_pid is not None,
        }


class BroadcastManager:
    """Singleton manager for broadcast sessions.
    
    Thread-safe management of active broadcasts per language.
    """
    
    _instance: Optional["BroadcastManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "BroadcastManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._broadcasts: Dict[LanguageCode, BroadcastSession] = {}
        self._client_locks: Dict[LanguageCode, threading.Lock] = {}
        self._initialized = True
        logger.info("BroadcastManager initialized")
    
    def _get_lock(self, language: LanguageCode) -> threading.Lock:
        """Get or create lock for a language."""
        if language not in self._client_locks:
            self._client_locks[language] = threading.Lock()
        return self._client_locks[language]
    
    def get_broadcast(self, language: LanguageCode) -> Optional[BroadcastSession]:
        """Get active broadcast for a language."""
        return self._broadcasts.get(language)
    
    def is_active(self, language: LanguageCode) -> bool:
        """Check if broadcast is active for a language."""
        broadcast = self._broadcasts.get(language)
        return broadcast is not None and broadcast.status == BroadcastStatus.ACTIVE
    
    def start_broadcast(self, language: LanguageCode) -> BroadcastSession:
        """Start a new broadcast session for a language.
        
        Creates a new database session and registers the broadcast.
        
        Args:
            language: Target language for the broadcast.
            
        Returns:
            The created BroadcastSession.
            
        Raises:
            ValueError: If broadcast already active for this language.
        """
        with self._get_lock(language):
            existing = self._broadcasts.get(language)
            if existing and existing.status == BroadcastStatus.ACTIVE:
                raise ValueError(f"Broadcast already active for {language.value}")
            
            # Create database session
            session_model = SessionModel(
                language=language,
                status=SessionStatus.ACTIVE,
            )
            session_id = save_session(session_model)
            
            # Create broadcast session
            broadcast = BroadcastSession(
                language=language,
                session_id=session_id,
                status=BroadcastStatus.ACTIVE,
            )
            self._broadcasts[language] = broadcast
            
            logger.info(f"Started broadcast for {language.value}, session_id={session_id}")
            return broadcast
    
    def stop_broadcast(self, language: LanguageCode) -> bool:
        """Stop broadcast for a language.
        
        Args:
            language: Language to stop broadcast for.
            
        Returns:
            True if broadcast was stopped, False if not active.
        """
        with self._get_lock(language):
            broadcast = self._broadcasts.get(language)
            if not broadcast:
                return False
            
            # Update database session status
            try:
                update_session_status(broadcast.session_id, SessionStatus.CLOSED.value)
            except Exception as e:
                logger.error(f"Failed to update session status: {e}")
            
            # Remove from active broadcasts
            del self._broadcasts[language]
            
            logger.info(f"Stopped broadcast for {language.value}")
            return True
    
    def add_client(self, language: LanguageCode) -> Optional[str]:
        """Register a new client connection.
        
        If no broadcast exists, one will be created automatically.
        
        Args:
            language: Language the client is connecting to.
            
        Returns:
            Session ID for the broadcast, or None if failed.
        """
        with self._get_lock(language):
            broadcast = self._broadcasts.get(language)
            
            if not broadcast or broadcast.status != BroadcastStatus.ACTIVE:
                # Auto-start broadcast on first client
                try:
                    broadcast = self.start_broadcast(language)
                except Exception as e:
                    logger.error(f"Failed to auto-start broadcast: {e}")
                    return None
            
            broadcast.client_count += 1
            logger.debug(f"Client connected to {language.value}, count={broadcast.client_count}")
            return broadcast.session_id
    
    def remove_client(self, language: LanguageCode) -> int:
        """Unregister a client connection.
        
        Note: Does NOT auto-stop broadcast when clients reach 0.
        Manual stop is required.
        
        Args:
            language: Language the client was connected to.
            
        Returns:
            Remaining client count.
        """
        with self._get_lock(language):
            broadcast = self._broadcasts.get(language)
            if not broadcast:
                return 0
            
            broadcast.client_count = max(0, broadcast.client_count - 1)
            logger.debug(f"Client disconnected from {language.value}, count={broadcast.client_count}")
            return broadcast.client_count
    
    def get_status(self, language: Optional[LanguageCode] = None) -> dict:
        """Get broadcast status.
        
        Args:
            language: Specific language to check, or None for all.
            
        Returns:
            Status dictionary.
        """
        if language:
            broadcast = self._broadcasts.get(language)
            if broadcast:
                return broadcast.to_dict()
            return {
                "language": language.value,
                "status": BroadcastStatus.IDLE.value,
                "session_id": None,
                "client_count": 0,
            }
        
        # Return all broadcasts
        return {
            "broadcasts": [b.to_dict() for b in self._broadcasts.values()],
            "active_count": sum(1 for b in self._broadcasts.values() 
                               if b.status == BroadcastStatus.ACTIVE),
        }
    
    def set_audio_pid(self, language: LanguageCode, pid: Optional[int]) -> None:
        """Set the FFmpeg process ID for a broadcast.
        
        Args:
            language: Language broadcast.
            pid: Process ID, or None to clear.
        """
        broadcast = self._broadcasts.get(language)
        if broadcast:
            broadcast.audio_pid = pid
            logger.debug(f"Set audio PID for {language.value}: {pid}")


# Global instance accessor
def get_broadcast_manager() -> BroadcastManager:
    """Get the singleton BroadcastManager instance."""
    return BroadcastManager()
