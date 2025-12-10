# Epic 5: Client API Endpoints

[← Back to PRD](../PRD.md)

---

## Description

Build REST API endpoints for clients to create sessions and receive translations. Audio is handled via file-based pipeline (Epic 2), not HTTP upload.

**Expected Outcome:** Clients can connect, select language preference, and receive real-time translated text.

---

## 5.1 Core Endpoints

- [-] **5.1.1** ~~`POST /api/audio` - Receive audio chunk~~ (replaced by file-based pipeline in Epic 2)
- [ ] **5.1.2** `GET /api/translation/{session_id}` - Get latest translation
- [ ] **5.1.3** `POST /api/session` - Create new translation session
- [ ] **5.1.4** `GET /api/session/{session_id}/status` - Session status
- [ ] **5.1.5** `GET /api/health` - Health check endpoint

> 💬 Notes:
>
> - Audio input is file-based (FFmpeg → pending/ → FileWatcher), not via HTTP endpoint
> - See Epic 2 for audio pipeline details

---

## 5.2 Language Selection

- [x] **5.2.1** Define supported languages enum (`LanguageCode` in `schemas.py`)
- [ ] **5.2.2** Implement language selection in session creation
- [x] **5.2.3** Create Pydantic schema for language preferences (`SessionCreate` in `schemas.py`)

> 💬 Notes:
>
> - Initially supporting Chinese only, architecture allows future expansion
> - `LanguageCode` enum and `SessionCreate` schema already implemented in Epic 6

---

## 5.3 Real-Time Delivery

- [ ] **5.3.1** Research real-time options (SSE, WebSocket, polling)
- [ ] **5.3.2** Implement chosen real-time mechanism
- [ ] **5.3.3** Handle client connection/disconnection

> 💬 Notes:
>

---

## Progress Log

### Session [DATE]

**Focus:**  
**Completed:**  
**Blockers:**  
**Next Steps:**  
