# GodLang - Real-Time Church Translation Service

## Product Requirements Document

**Version:** 1.0  
**Created:** 2024-12-10  
**Status:** In Progress

---

## Overview

A real-time translation API service for church audio. The system captures audio from a mixing board, transcribes it using Groq API (with built-in English translation), then translates from English to Chinese using Groq Qwen 32B model. Clients connect with a language preference and receive translated text.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| API Framework | Flask |
| Database | MongoDB (Docker) |
| Containerization | Docker + Docker Compose |
| Audio Processing | FFmpeg |
| Validation | Pydantic |
| Transcription | Groq API (with English translation) |
| Translation | Groq Qwen 32B |

---

## Architecture Flow

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Mixing Board│────▶│ Audio Chunk │────▶│  Groq API   │────▶│   English   │
│   (Audio)   │     │  (FFmpeg)   │     │ (Transcribe)│     │    Text     │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                                                                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │◀────│  Response   │◀────│ Groq Qwen   │◀────│  Translate  │
│  (Chinese)  │     │   (Text)    │     │    32B      │     │  to Chinese │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Task Tracking

Each epic has its own tracking file in `docs/epics/`. Use task numbers to reference in conversations.

| Symbol | Meaning |
|--------|--------|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Completed |
| `[!]` | Blocked |
| `[-]` | Cancelled |

**Comment Format:** `> 💬 [DATE]: Comment text`

---

## Epics Overview

| Epic | Name | Description | File |
|------|------|-------------|------|
| 1 | [Project Setup & Infrastructure](epics/epic-1-setup.md) | Docker environment, MongoDB, project structure | `epic-1-setup.md` |
| 2 | [Audio Processing Pipeline](epics/epic-2-audio.md) | Audio input, FFmpeg chunking, temporary storage | `epic-2-audio.md` |
| 3 | [Transcription Service](epics/epic-3-transcription.md) | Groq API integration for speech-to-text | `epic-3-transcription.md` |
| 4 | [Translation Service](epics/epic-4-translation.md) | Groq Qwen 32B for English→Chinese | `epic-4-translation.md` |
| 5 | [Client API Endpoints](epics/epic-5-api.md) | REST endpoints, sessions, real-time delivery | `epic-5-api.md` |
| 6 | [Data Models & Persistence](epics/epic-6-models.md) | Pydantic schemas, MongoDB collections | `epic-6-models.md` |
| 7 | [Testing & Documentation](epics/epic-7-testing.md) | Tests, API docs, setup guides | `epic-7-testing.md` |

---

## Epic Descriptions

### Epic 1: Project Setup & Infrastructure

Establish the development environment with Docker containers for both the Flask application and MongoDB. Configure hot-reload for efficient development workflow. Set up proper project structure with organized folders for routes, models, services, and utilities.

**Expected Outcome:** Running `docker-compose up` starts both the Flask app (with hot-reload) and MongoDB, ready for development.

### Epic 2: Audio Processing Pipeline

Handle audio input from the church mixing board. Use FFmpeg to slice the continuous audio stream into manageable chunks suitable for API processing. Define audio format, chunk duration, and encoding settings.

**Expected Outcome:** System can receive audio input and produce properly formatted chunks ready for transcription API.

### Epic 3: Transcription Service (Groq API)

Integrate with Groq API to transcribe audio chunks. Leverage Groq's built-in translation feature to receive transcriptions directly in English, regardless of source language.

**API Reference:** <https://console.groq.com/docs/overview>

**Expected Outcome:** Audio chunks sent to Groq API return English text transcriptions.

### Epic 4: Translation Service (Groq Qwen 32B)

Use Groq's Qwen 32B model to translate English transcriptions to Chinese. Optimize prompts for translation quality and natural language output.

**Expected Outcome:** English text input produces accurate Chinese translations.

### Epic 5: Client API Endpoints

Build REST API endpoints for clients to create sessions, submit audio, and receive translations. Implement real-time delivery mechanism (SSE, WebSocket, or polling) for translation updates.

**Expected Outcome:** Clients can connect, select language preference, and receive real-time translated text.

### Epic 6: Data Models & Persistence

Define Pydantic schemas for data validation and MongoDB collections for persistence. Create models for sessions, transcriptions, and translations with proper relationships.

**Expected Outcome:** All data is validated on input and properly stored/retrieved from MongoDB.

### Epic 7: Testing & Documentation

Set up pytest for unit and integration testing. Create API documentation and setup guides for future reference and onboarding.

**Expected Outcome:** Comprehensive test coverage and clear documentation for the project.

---

## Quick Reference

### Starting Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | API key for Groq transcription/translation |
| `MONGODB_URI` | MongoDB connection string |
| `FLASK_ENV` | development / production |
| `FLASK_DEBUG` | 1 for hot-reload |

---

## Decisions Log

| ID | Decision | Rationale | Date |
|----|----------|-----------|------|
| D1 | Use Groq API for transcription with English output | Built-in translation feature, single API call | 2024-12-10 |
| D2 | Use Groq Qwen 32B for English→Chinese | Better translation quality from English | 2024-12-10 |
| D3 | No authentication required | Simplicity for initial version | 2024-12-10 |
| D4 | Split PRD into epic files | Easier tracking and management | 2024-12-10 |

---

## Parking Lot

Ideas for future consideration:

- [ ] Support additional languages beyond Chinese
- [ ] Add authentication for production use
- [ ] Implement caching for repeated phrases
- [ ] Add audio quality detection/validation
