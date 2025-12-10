# Epic 3: Transcription Service (Groq API)

[← Back to PRD](../PRD.md)

---

## Description

Integrate with Groq API to transcribe audio chunks. Leverage Groq's built-in translation feature to receive transcriptions directly in English, regardless of source language.

**Expected Outcome:** Audio chunks sent to Groq API return English text transcriptions.

---

## References

- **Groq API Documentation:** <https://console.groq.com/docs/overview>

---

## 3.1 Groq API Integration

- [x] **3.1.1** Research Groq API documentation for audio transcription
- [x] **3.1.2** Set up Groq API credentials in environment (`GROQ_API_KEY` in `config.py`)
- [x] **3.1.3** Create Groq API client service (`app/services/groq_client.py`)
- [ ] **3.1.4** Implement audio-to-English transcription function
- [x] **3.1.5** Define Pydantic schema for transcription response (`TranscriptionModel` in `schemas.py`)
- [ ] **3.1.6** Add error handling for API failures
- [x] **3.1.7** Implement retry logic with exponential backoff (in `AudioPipeline`)

> 💬 Notes:
>
> - Groq API returns transcription directly in English (translation feature built-in)
> - Supported formats: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
> - Using FLAC format (16kHz mono) for optimal file size

---

## 3.2 Transcription Processing

- [ ] **3.2.1** Parse and validate Groq API response
- [ ] **3.2.2** Store transcription results in MongoDB
- [ ] **3.2.3** Create MongoDB model for transcriptions

> 💬 Notes:
>

---

## Progress Log

### Session 2024-12-10

**Focus:** Groq API setup and integration prep  
**Completed:**

- Groq API credentials configuration
- Groq client service (`init_groq`, `get_groq_client`)
- `TranscriptionModel` Pydantic schema
- Retry logic in `AudioPipeline`

**Blockers:** None  
**Next Steps:** Implement actual transcription function call to Groq Whisper API  
