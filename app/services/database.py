"""MongoDB database service."""

import logging
from typing import Optional

from flask import Flask
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from app.models.schemas import TranscriptionModel

logger = logging.getLogger(__name__)


def init_db(app: Flask) -> None:
    """Initialize MongoDB connection.

    Args:
        app: Flask application instance.
    """
    mongo_uri = app.config.get("MONGO_URI")

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # Verify connection
        client.admin.command("ping")
        app.mongo_client = client
        app.db = client[app.config.get("MONGO_DB_NAME", "godlang")]
        app.logger.info("Connected to MongoDB")
    except ConnectionFailure as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        app.mongo_client = None
        app.db = None


def get_db():
    """Get database instance from current app context.

    Returns:
        MongoDB database instance or None.
    """
    from flask import current_app

    return getattr(current_app, "db", None)


class DatabaseError(Exception):
    """Database operation error."""

    pass


async def save_transcription(transcription: TranscriptionModel) -> str:
    """Save transcription to MongoDB.

    Args:
        transcription: TranscriptionModel instance to save.

    Returns:
        The inserted document ID.

    Raises:
        DatabaseError: If save operation fails.
    """
    db = get_db()
    if not db:
        raise DatabaseError("Database not connected")

    try:
        # Convert to dict for MongoDB storage
        transcription_dict = transcription.model_dump(exclude={"id"})

        result = db.transcriptions.insert_one(transcription_dict)
        transcription_id = str(result.inserted_id)

        logger.info(
            f"Saved transcription {transcription_id} for session {transcription.session_id}"
        )
        return transcription_id

    except PyMongoError as e:
        logger.error(f"Failed to save transcription: {e}")
        raise DatabaseError(f"Failed to save transcription: {e}") from e


async def get_transcriptions_by_session(
    session_id: str, limit: Optional[int] = None
) -> list[dict]:
    """Get transcriptions for a specific session.

    Args:
        session_id: Session ID to filter by.
        limit: Optional maximum number of results.

    Returns:
        List of transcription documents.

    Raises:
        DatabaseError: If query operation fails.
    """
    db = get_db()
    if not db:
        raise DatabaseError("Database not connected")

    try:
        query = {"session_id": session_id}
        cursor = db.transcriptions.find(query).sort("created_at", 1)

        if limit:
            cursor = cursor.limit(limit)

        transcriptions = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            transcriptions.append(doc)

        logger.debug(
            f"Found {len(transcriptions)} transcriptions for session {session_id}"
        )
        return transcriptions

    except PyMongoError as e:
        logger.error(f"Failed to get transcriptions for session {session_id}: {e}")
        raise DatabaseError(f"Failed to get transcriptions: {e}") from e


async def get_latest_transcription(session_id: str) -> Optional[dict]:
    """Get the latest transcription for a session.

    Args:
        session_id: Session ID to filter by.

    Returns:
        Latest transcription document or None.

    Raises:
        DatabaseError: If query operation fails.
    """
    transcriptions = await get_transcriptions_by_session(session_id, limit=1)
    return transcriptions[0] if transcriptions else None
