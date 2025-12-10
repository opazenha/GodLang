# Epic 4: Translation Service (Groq Qwen 32B)

[← Back to PRD](../PRD.md)

---

## Description

Use Groq's Qwen 32B model to translate English transcriptions to Chinese. Optimize prompts for translation quality and natural language output.

**Expected Outcome:** English text input produces accurate Chinese translations.

---

## 4.1 Qwen 32B Integration

- [ ] **4.1.1** Research Groq Qwen 32B API for translation
- [ ] **4.1.2** Create translation service client
- [ ] **4.1.3** Implement English-to-Chinese translation
- [x] **4.1.4** Define Pydantic schema for translation request/response (`TranslationModel` in `schemas.py`)
- [ ] **4.1.5** Add error handling and retry logic
- [ ] **4.1.6** Optimize prompt for translation quality

> 💬 Notes:
>
> - Will reuse Groq client from Epic 3 (`groq_client.py`)
> - `TranslationModel` schema already defined with `transcription_id` link

---

## 4.2 Translation Processing

- [ ] **4.2.1** Link transcription to translation in data model
- [ ] **4.2.2** Store translation results in MongoDB
- [ ] **4.2.3** Create MongoDB model for translations

> 💬 Notes:
>

---

## Progress Log

### Session [DATE]

**Focus:**  
**Completed:**  
**Blockers:**  
**Next Steps:**  
