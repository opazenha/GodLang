# Epic 4: Translation Service (Groq Qwen 32B)

[← Back to PRD](../PRD.md)

---

## Description

Use Groq's Qwen 32B model to translate English transcriptions to Chinese. Optimize prompts for translation quality and natural language output.

**Expected Outcome:** English text input produces accurate Chinese translations.

---

## 4.1 Qwen 32B Integration

- [x] **4.1.1** Research Groq Qwen 32B API for translation
- [x] **4.1.2** Create translation service client
- [x] **4.1.3** Implement English-to-Chinese translation
- [x] **4.1.4** Define Pydantic schema for translation request/response (`TranslationModel` in `schemas.py`)
- [x] **4.1.5** Add error handling and retry logic
- [x] **4.1.6** Optimize prompt for translation quality

> 💬 Notes:
>
> - Will reuse Groq client from Epic 3 (`groq_client.py`)
> - `TranslationModel` schema already defined with `transcription_id` link

---

## 4.2 Translation Processing

- [x] **4.2.1** Link transcription to translation in data model
- [x] **4.2.2** Store translation results in MongoDB
- [x] **4.2.3** Create MongoDB model for translations

> 💬 Notes:
>

---

## Progress Log

### Session 2024-12-12

**Focus:** Qwen 32B translation service implementation  
**Completed:**

- Groq Qwen 3 32B API integration (updated from deprecated qwen-2.5-32b)
- English-to-Chinese translation function with optimized prompts
- Translation error handling with retryable vs permanent failures
- MongoDB storage for translation results
- Database query functions for translations by transcription and session
- Integration with existing audio pipeline architecture
- Comprehensive testing with sample translations

**Blockers:** None  
**Next Steps:** Epic 4-Translation is complete. Ready for Epic 5-API development.  
