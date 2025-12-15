"""MongoDB database service."""

import logging
from typing import Optional

from flask import Flask
from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from app.models.schemas import (
    TranscriptionModel,
    TranslationModel,
    SessionModel,
    LanguageCode,
)

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
        setattr(app, "mongo_client", client)
        setattr(app, "db", client[app.config.get("MONGO_DB_NAME", "godlang")])
        app.logger.info("Connected to MongoDB")
    except ConnectionFailure as e:
        app.logger.error(f"Failed to connect to MongoDB: {e}")
        setattr(app, "mongo_client", None)
        setattr(app, "db", None)


def get_db():
    """Get database instance from current app context.

    Returns:
        MongoDB database instance or None.
    """
    from flask import current_app

    db = getattr(current_app, "db", None)
    return db if db is not None else None


class DatabaseError(Exception):
    """Database operation error."""

    pass


def save_transcription(transcription: TranscriptionModel) -> str:
    """Save transcription to MongoDB.

    Args:
        transcription: TranscriptionModel instance to save.

    Returns:
        The inserted document ID.

    Raises:
        DatabaseError: If save operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        # Convert to dict for MongoDB storage
        transcription_dict = transcription.model_dump(exclude={"id"})
        
        # Convert session_id string to ObjectId for MongoDB schema validation
        if "session_id" in transcription_dict and isinstance(transcription_dict["session_id"], str):
            transcription_dict["session_id"] = ObjectId(transcription_dict["session_id"])

        result = db.transcriptions.insert_one(transcription_dict)
        transcription_id = str(result.inserted_id)

        logger.info(
            f"Saved transcription {transcription_id} for session {transcription.session_id}"
        )
        return transcription_id

    except PyMongoError as e:
        logger.error(f"Failed to save transcription: {e}")
        raise DatabaseError(f"Failed to save transcription: {e}") from e


def get_transcriptions_by_session(
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
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        # Convert session_id to ObjectId for query
        query = {"session_id": ObjectId(session_id) if isinstance(session_id, str) else session_id}
        cursor = db.transcriptions.find(query).sort("created_at", 1)

        if limit:
            cursor = cursor.limit(limit)

        transcriptions = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            if "session_id" in doc and isinstance(doc["session_id"], ObjectId):
                doc["session_id"] = str(doc["session_id"])
            if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()
            transcriptions.append(doc)

        logger.debug(
            f"Found {len(transcriptions)} transcriptions for session {session_id}"
        )
        return transcriptions

    except PyMongoError as e:
        logger.error(f"Failed to get transcriptions for session {session_id}: {e}")
        raise DatabaseError(f"Failed to get transcriptions: {e}") from e


def get_latest_transcription(session_id: str) -> Optional[dict]:
    """Get the latest transcription for a session.

    Args:
        session_id: Session ID to filter by.

    Returns:
        Latest transcription document or None.

    Raises:
        DatabaseError: If query operation fails.
    """
    transcriptions = get_transcriptions_by_session(session_id, limit=1)
    return transcriptions[0] if transcriptions else None


def save_translation(translation: TranslationModel) -> str:
    """Save translation to MongoDB.

    Args:
        translation: TranslationModel instance to save.

    Returns:
        The inserted document ID.

    Raises:
        DatabaseError: If save operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        # Convert to dict for MongoDB storage
        translation_dict = translation.model_dump(exclude={"id"})
        
        # Convert transcription_id string to ObjectId for MongoDB schema validation
        if "transcription_id" in translation_dict and isinstance(translation_dict["transcription_id"], str):
            translation_dict["transcription_id"] = ObjectId(translation_dict["transcription_id"])

        result = db.translations.insert_one(translation_dict)
        translation_id = str(result.inserted_id)

        logger.info(
            f"Saved translation {translation_id} for transcription {translation.transcription_id}"
        )
        return translation_id

    except PyMongoError as e:
        logger.error(f"Failed to save translation: {e}")
        raise DatabaseError(f"Failed to save translation: {e}") from e


def get_translations_by_transcription(
    transcription_id: str, limit: Optional[int] = None
) -> list[dict]:
    """Get translations for a specific transcription.

    Args:
        transcription_id: Transcription ID to filter by.
        limit: Optional maximum number of results.

    Returns:
        List of translation documents.

    Raises:
        DatabaseError: If query operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        query = {"transcription_id": transcription_id}
        cursor = db.translations.find(query).sort("created_at", 1)

        if limit:
            cursor = cursor.limit(limit)

        translations = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
            translations.append(doc)

        logger.debug(
            f"Found {len(translations)} translations for transcription {transcription_id}"
        )
        return translations

    except PyMongoError as e:
        logger.error(
            f"Failed to get translations for transcription {transcription_id}: {e}"
        )
        raise DatabaseError(f"Failed to get translations: {e}") from e


def get_translations_by_session(
    session_id: str,
    limit: Optional[int] = None,
    language: Optional[LanguageCode] = None,
) -> list[dict]:
    """Get all translations for a session, optionally filtered by language.

    Args:
        session_id: Session ID to filter by.
        language: Optional language filter.

    Returns:
        List of translation documents.

    Raises:
        DatabaseError: If query operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        # Build query
        query = {}
        # Join with transcriptions to filter by session_id
        pipeline = [
            {
                "$lookup": {
                    "from": "transcriptions",
                    "localField": "transcription_id",
                    "foreignField": "_id",
                    "as": "transcription",
                }
            },
            {"$unwind": "$transcription"},
            {"$match": {"transcription.session_id": ObjectId(session_id) if isinstance(session_id, str) else session_id}},
            {"$sort": {"created_at": 1}},
        ]

        if language:
            pipeline.append({"$match": {"language": language.value}})

        cursor = db.translations.aggregate(pipeline)

        translations = []
        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "transcription_id" in doc and isinstance(doc["transcription_id"], ObjectId):
                doc["transcription_id"] = str(doc["transcription_id"])
            if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                doc["created_at"] = doc["created_at"].isoformat()
            # Convert nested transcription ObjectIds and datetime if present
            if "transcription" in doc and isinstance(doc["transcription"], dict):
                if "_id" in doc["transcription"]:
                    doc["transcription"]["_id"] = str(doc["transcription"]["_id"])
                if "session_id" in doc["transcription"] and isinstance(doc["transcription"]["session_id"], ObjectId):
                    doc["transcription"]["session_id"] = str(doc["transcription"]["session_id"])
                if "created_at" in doc["transcription"] and hasattr(doc["transcription"]["created_at"], "isoformat"):
                    doc["transcription"]["created_at"] = doc["transcription"]["created_at"].isoformat()
            translations.append(doc)

        logger.debug(f"Found {len(translations)} translations for session {session_id}")
        return translations

    except PyMongoError as e:
        logger.error(f"Failed to get translations for session {session_id}: {e}")
        raise DatabaseError(f"Failed to get translations: {e}") from e


def save_session(session: SessionModel) -> str:
    """Save session to MongoDB.

    Args:
        session: SessionModel instance to save.

    Returns:
        The inserted document ID.

    Raises:
        DatabaseError: If save operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        # Convert to dict for MongoDB storage
        session_dict = session.model_dump(exclude={"id"})

        result = db.sessions.insert_one(session_dict)
        session_id = str(result.inserted_id)

        logger.info(f"Saved session {session_id} with language {session.language}")
        return session_id

    except PyMongoError as e:
        logger.error(f"Failed to save session: {e}")
        raise DatabaseError(f"Failed to save session: {e}") from e


def get_session(session_id: str) -> Optional[dict]:
    """Get session by ID.

    Args:
        session_id: Session ID to retrieve.

    Returns:
        Session document or None.

    Raises:
        DatabaseError: If query operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        from bson import ObjectId

        object_id = ObjectId(session_id)
        doc = db.sessions.find_one({"_id": object_id})

        if doc:
            doc["_id"] = str(doc["_id"])
            return doc
        return None

    except PyMongoError as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise DatabaseError(f"Failed to get session: {e}") from e


def update_session_status(session_id: str, status: str) -> bool:
    """Update session status.

    Args:
        session_id: Session ID to update.
        status: New status value.

    Returns:
        True if update succeeded, False otherwise.

    Raises:
        DatabaseError: If update operation fails.
    """
    db = get_db()
    if db is None:
        raise DatabaseError("Database not connected")

    try:
        from bson import ObjectId

        object_id = ObjectId(session_id)
        result = db.sessions.update_one(
            {"_id": object_id}, {"$set": {"status": status}}
        )

        success = result.modified_count > 0
        if success:
            logger.info(f"Updated session {session_id} status to {status}")
        return success

    except PyMongoError as e:
        logger.error(f"Failed to update session {session_id} status: {e}")
        raise DatabaseError(f"Failed to update session status: {e}") from e
