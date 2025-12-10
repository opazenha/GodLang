# Epic 2: Audio Processing Pipeline

[← Back to PRD](../PRD.md)

---

## Description

Handle audio input from the church mixing board. Use FFmpeg to slice the continuous audio stream into manageable chunks suitable for API processing. Define audio format, chunk duration, and encoding settings.

**Expected Outcome:** System can receive audio input and produce properly formatted chunks ready for transcription API.

---

## 2.1 Audio Input Handling

- [ ] **2.1.1** Research audio input methods from mixing board
- [ ] **2.1.2** Create endpoint to receive audio stream/chunks
- [ ] **2.1.3** Define Pydantic schema for audio input
- [ ] **2.1.4** Implement audio buffer management

> 💬 Notes:
>

---

## 2.2 FFmpeg Integration

- [ ] **2.2.1** Add FFmpeg to Docker image
- [ ] **2.2.2** Create audio chunking utility using FFmpeg
- [ ] **2.2.3** Define chunk duration and format settings
- [ ] **2.2.4** Implement audio format conversion (if needed)
- [ ] **2.2.5** Handle audio encoding for API compatibility

> 💬 Notes:
>

---

## 2.3 Audio Storage (Optional/Temporary)

- [ ] **2.3.1** Decide on temporary storage strategy for chunks
- [ ] **2.3.2** Implement cleanup mechanism for processed chunks

> 💬 Notes:
>

---

## Progress Log

### Session [DATE]

**Focus:**  
**Completed:**  
**Blockers:**  
**Next Steps:**  
