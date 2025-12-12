# Epic 5: Client API Endpoints

[← Back to PRD](../PRD.md)

---

## Description

Build REST API endpoints for clients to create sessions and receive translations. Audio is handled via file-based pipeline (Epic 2), not HTTP upload.

**Expected Outcome:** Clients can connect, select language preference, and receive real-time translated text.

---

## 5.1 Core Endpoints

- [-] **5.1.1** ~~`POST /api/audio` - Receive audio chunk~~ (replaced by file-based pipeline in Epic 2)
- [x] **5.1.2** `GET /api/translation/{session_id}` - Get latest translation
- [x] **5.1.3** `POST /api/session` - Create new translation session
- [x] **5.1.4** `GET /api/session/{session_id}/status` - Session status
- [x] **5.1.5** `GET /api/health` - Health check endpoint
- [x] **5.1.6** `DELETE /api/session/{session_id}` - Close session
- [x] **5.1.7** `GET /api/translation/{session_id}/all` - Get all translations for session

> 💬 Notes:
>
> - Audio input is file-based (FFmpeg → pending/ → FileWatcher), not via HTTP endpoint
> - See Epic 2 for audio pipeline details

---

## 5.2 Language Selection

- [x] **5.2.1** Define supported languages enum (`LanguageCode` in `schemas.py`)
- [x] **5.2.2** Implement language selection in session creation
- [x] **5.2.3** Create Pydantic schema for language preferences (`SessionCreate` in `schemas.py`)

> 💬 Notes:
>
> - Initially supporting Chinese only, architecture allows future expansion
> - `LanguageCode` enum and `SessionCreate` schema already implemented in Epic 6

---

## 5.3 Real-Time Delivery

- [x] **5.3.1** Research real-time options (SSE, WebSocket, polling)
- [x] **5.3.2** Implement chosen real-time mechanism (SSE)
- [x] **5.3.3** Handle client connection/disconnection

> 💬 Notes:
> - Chose Server-Sent Events (SSE) for real-time delivery
> - SSE endpoints implemented:
>   - `/api/sse/translation/{session_id}` - Streams translation updates
>   - `/api/sse/session/{session_id}` - Streams session status changes
> - Includes heartbeat mechanism and error handling

---

## Progress Log

### Session 2025-12-12

**Focus:** Complete API endpoint implementation for client connectivity  
**Completed:**  
- ✅ All core REST endpoints implemented and tested
- ✅ Session management with MongoDB integration
- ✅ Real-time delivery via Server-Sent Events (SSE)
- ✅ Language selection support (Chinese)
- ✅ Comprehensive error handling and API response standardization
- ✅ Health check endpoint improvements
- ✅ Database connection fixes and Flask app context handling

**Blockers:** None  
**Next Steps:** Epic 5 is complete. Ready for integration testing with audio pipeline (Epic 2) and client applications.  
