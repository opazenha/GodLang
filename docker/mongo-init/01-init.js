// MongoDB initialization script
// This runs automatically when the container starts for the first time

// Switch to the godlang database
db = db.getSiblingDB('godlang');

// Create collections with schema validation
db.createCollection('sessions', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['created_at', 'language'],
            properties: {
                created_at: {
                    bsonType: 'date',
                    description: 'Session creation timestamp'
                },
                language: {
                    bsonType: 'string',
                    description: 'Target translation language'
                },
                status: {
                    bsonType: 'string',
                    enum: ['active', 'closed'],
                    description: 'Session status'
                }
            }
        }
    }
});

db.createCollection('transcriptions', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['session_id', 'transcript', 'created_at'],
            properties: {
                session_id: {
                    bsonType: 'objectId',
                    description: 'Reference to session'
                },
                transcript: {
                    bsonType: 'string',
                    description: 'English transcription text'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Transcription timestamp'
                }
            }
        }
    }
});

db.createCollection('translations', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['transcription_id', 'translation', 'language', 'created_at'],
            properties: {
                transcription_id: {
                    bsonType: 'objectId',
                    description: 'Reference to transcription'
                },
                translation: {
                    bsonType: 'string',
                    description: 'Translated text'
                },
                language: {
                    bsonType: 'string',
                    description: 'Target language code'
                },
                created_at: {
                    bsonType: 'date',
                    description: 'Translation timestamp'
                }
            }
        }
    }
});

// Create indexes for query optimization
db.sessions.createIndex({ created_at: -1 });
db.sessions.createIndex({ status: 1 });

db.transcriptions.createIndex({ session_id: 1 });
db.transcriptions.createIndex({ created_at: -1 });

db.translations.createIndex({ transcription_id: 1 });
db.translations.createIndex({ created_at: -1 });

print('MongoDB initialized: collections and indexes created');
