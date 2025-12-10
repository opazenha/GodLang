# Epic 6: Data Models & Persistence

[← Back to PRD](../PRD.md)

---

## Description

Define Pydantic schemas for data validation and MongoDB collections for persistence. Create models for sessions, transcriptions, and translations with proper relationships.

**Expected Outcome:** All data is validated on input and properly stored/retrieved from MongoDB.

---

## 6.1 Pydantic Schemas

- [-] **6.1.1** `AudioChunkSchema` - Input audio validation (handled by `AudioChunk` dataclass in `audio.py`)
- [x] **6.1.2** `TranscriptionSchema` - Transcription data (`TranscriptionModel`)
- [x] **6.1.3** `TranslationSchema` - Translation data (`TranslationModel`)
- [x] **6.1.4** `SessionSchema` - Client session data (`SessionCreate`, `SessionResponse`, `SessionStatus`)
- [x] **6.1.5** `APIResponseSchema` - Standard API responses (`APIResponse`, `HealthResponse`)

> 💬 Notes:
>
> - `BaseSchema` provides common config (enum values, validation, whitespace stripping)
> - `LanguageCode` enum supports Chinese, extensible for future languages
> - Audio chunk validation moved to `app/services/audio.py` as `AudioChunk` dataclass

---

## 6.2 MongoDB Collections

- [ ] **6.2.1** `sessions` - Client session tracking
- [ ] **6.2.2** `transcriptions` - Raw transcription storage
- [ ] **6.2.3** `translations` - Translation results
- [ ] **6.2.4** Define indexes for query optimization

> 💬 Notes:
>

---

## Progress Log

### Session 2024-12-10

**Focus:** Pydantic schemas implementation  
**Completed:**

- `BaseSchema` with common Pydantic config
- `LanguageCode` and `SessionStatus` enums
- `HealthResponse` and `APIResponse` schemas
- `SessionCreate` and `SessionResponse` schemas
- `TranscriptionModel` and `TranslationModel` schemas

**Blockers:** None  
**Next Steps:** Implement MongoDB collections and indexes  
