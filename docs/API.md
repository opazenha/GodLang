# GodLang API Documentation

## Overview

GodLang provides a REST API for real-time church translation services. The API allows clients to create translation sessions, receive translated text, and monitor system health.

**Base URL:** `http://localhost:7770` (development)  
**Content-Type:** `application/json`  
**Authentication:** None (initial version)

---

## Response Format

All API responses follow a standard format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  }
}
```

- `success`: Boolean indicating if the request succeeded
- `message`: Optional descriptive message
- `data`: Response payload (null for some endpoints)

---

## Endpoints

### Health Check

#### GET /health

Check the health status of all system components.

**Response:**

```json
{
  "status": "healthy",
  "mongo_connected": true,
  "ffmpeg_installed": true
}
```

**Status Values:**

- `healthy`: All components operational
- `degraded`: Some components unavailable

---

### Session Management

#### POST /api/session

Create a new translation session.

**Request Body:**

```json
{
  "language": "zh"
}
```

**Parameters:**

- `language` (string, optional): Target language code. Default: `"zh"` (Chinese)

**Response:**

```json
{
  "success": true,
  "message": "Session created successfully",
  "data": {
    "id": "693c389b6ecb646aed53c132",
    "language": "zh",
    "status": "active",
    "created_at": "2025-12-12T15:45:31Z"
  }
}
```

#### GET /api/session/{session_id}/status

Get the current status of a session.

**Path Parameters:**

- `session_id` (string): Session identifier

**Response:**

```json
{
  "success": true,
  "message": "Session status retrieved",
  "data": {
    "session_id": "693c389b6ecb646aed53c132",
    "status": "active",
    "language": "zh",
    "created_at": "2025-12-12T15:45:31Z"
  }
}
```

**Status Values:**

- `active`: Session is active and processing
- `closed`: Session has been closed

#### DELETE /api/session/{session_id}

Close a translation session.

**Path Parameters:**

- `session_id` (string): Session identifier

**Response:**

```json
{
  "success": true,
  "message": "Session closed successfully",
  "data": {
    "session_id": "693c389b6ecb646aed53c132",
    "status": "closed"
  }
}
```

---

### Broadcast Management

#### GET /api/broadcast/status

Get broadcast status for all languages or a specific language.

**Query Parameters:**

- `language` (string, optional): Language code (e.g., `zh`)

**Response (specific language):**

```json
{
  "success": true,
  "message": "Broadcast status retrieved",
  "data": {
    "language": "zh",
    "session_id": "693c389b6ecb646aed53c132",
    "status": "active",
    "client_count": 3,
    "started_at": "2025-12-14T10:30:00Z",
    "audio_active": true
  }
}
```

**Response (no active broadcast):**

```json
{
  "success": true,
  "message": "Broadcast status retrieved",
  "data": {
    "language": "zh",
    "status": "idle",
    "session_id": null,
    "client_count": 0
  }
}
```

**Status Values:**

- `idle`: No active broadcast
- `starting`: Broadcast is starting up
- `active`: Broadcast is running
- `stopping`: Broadcast is shutting down

#### POST /api/broadcast/start

Start a broadcast session for a language.

**Request Body:**

```json
{
  "language": "zh"
}
```

**Parameters:**

- `language` (string, optional): Target language code. Default: `"zh"` (Chinese)

**Response:**

```json
{
  "success": true,
  "message": "Broadcast started successfully",
  "data": {
    "language": "zh",
    "session_id": "693c389b6ecb646aed53c132",
    "status": "active",
    "client_count": 0,
    "started_at": "2025-12-14T10:30:00Z",
    "audio_active": false
  }
}
```

#### POST /api/broadcast/stop

Stop a broadcast session for a language.

**Request Body:**

```json
{
  "language": "zh"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Broadcast stopped successfully",
  "data": {
    "language": "zh"
  }
}
```

---

### Translations

#### GET /api/translation/{session_id}

Get the latest translation for a session.

**Path Parameters:**

- `session_id` (string): Session identifier

**Response (with translation):**

```json
{
  "success": true,
  "message": "Translation retrieved successfully",
  "data": {
    "transcription": {
      "_id": "transcription-id",
      "session_id": "session-id",
      "transcript": "Hello, this is a test.",
      "created_at": "2025-12-12T15:45:31Z"
    },
    "translation": {
      "_id": "translation-id",
      "transcription_id": "transcription-id",
      "transcript": "Hello, this is a test.",
      "translation": "你好，这是一个测试。",
      "language": "zh",
      "created_at": "2025-12-12T15:45:35Z"
    }
  }
}
```

**Response (no translation yet):**

```json
{
  "success": true,
  "message": "No translations found yet",
  "data": {
    "transcription": {
      "_id": "transcription-id",
      "session_id": "session-id",
      "transcript": "Hello, this is a test.",
      "created_at": "2025-12-12T15:45:31Z"
    },
    "translation": null
  }
}
```

#### GET /api/translation/{session_id}/all

Get all translations for a session.

**Path Parameters:**

- `session_id` (string): Session identifier

**Query Parameters:**

- `limit` (integer, optional): Maximum number of results to return

**Response:**

```json
{
  "success": true,
  "message": "Retrieved 2 translations",
  "data": {
    "session_id": "session-id",
    "translations": [
      {
        "_id": "translation-id-1",
        "transcription_id": "transcription-id-1",
        "transcript": "Hello world.",
        "translation": "你好世界。",
        "language": "zh",
        "created_at": "2025-12-12T15:45:31Z"
      },
      {
        "_id": "translation-id-2",
        "transcription_id": "transcription-id-2",
        "transcript": "How are you?",
        "translation": "你好吗？",
        "language": "zh",
        "created_at": "2025-12-12T15:45:35Z"
      }
    ],
    "count": 2
  }
}
```

---

## Real-Time Updates (Server-Sent Events)

For real-time updates, use Server-Sent Events (SSE) endpoints.

### Translation Stream

#### GET /api/sse/translation/{session_id}

Stream real-time translation updates for a session.

**Path Parameters:**

- `session_id` (string): Session identifier

**Client Setup:**

```javascript
const eventSource = new EventSource('/api/sse/translation/session-id');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connected':
      console.log('Connected to translation stream');
      break;
    case 'translation':
      console.log('New translation:', data.translation);
      break;
    case 'heartbeat':
      console.log('Heartbeat received');
      break;
    case 'error':
      console.error('Stream error:', data.message);
      break;
  }
};
```

**Event Types:**

- `connected`: Initial connection established
- `translation`: New translation available
- `heartbeat`: Periodic heartbeat (every 2 seconds)
- `error`: Error occurred

### Session Status Stream

#### GET /api/sse/session/{session_id}

Stream real-time session status updates.

**Path Parameters:**

- `session_id` (string): Session identifier

**Event Types:**

- `connected`: Initial connection established
- `status_change`: Session status changed
- `heartbeat`: Periodic heartbeat (every 5 seconds)
- `error`: Error occurred

### Broadcast Stream (Recommended)

#### GET /api/sse/broadcast/{language}

Stream real-time translation updates for a language broadcast. **This is the recommended endpoint for clients.**

Automatically creates a session if none exists when the first client connects.

**Path Parameters:**

- `language` (string): Language code (e.g., `zh` for Chinese)

**Client Setup:**

```javascript
const eventSource = new EventSource('/api/sse/broadcast/zh');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'connected':
      console.log('Connected to broadcast, session:', data.session_id);
      break;
    case 'translation':
      console.log('New translation:', data.translation);
      break;
    case 'broadcast_ended':
      console.log('Broadcast has ended');
      eventSource.close();
      break;
    case 'heartbeat':
      // Keep-alive signal
      break;
    case 'error':
      console.error('Stream error:', data.message);
      break;
  }
};
```

**Event Types:**

- `connected`: Initial connection established (includes `language` and `session_id`)
- `translation`: New translation available (includes `transcription` and `translation`)
- `broadcast_ended`: Broadcast has been stopped by volunteer
- `heartbeat`: Periodic heartbeat (every 2 seconds)
- `error`: Error occurred

**Translation Event Data:**

```json
{
  "type": "translation",
  "language": "zh",
  "session_id": "693c389b6ecb646aed53c132",
  "transcription": {
    "_id": "transcription-id",
    "transcript": "Hello, welcome to the service."
  },
  "translation": {
    "_id": "translation-id",
    "translation": "你好，欢迎参加礼拜。"
  },
  "timestamp": 1702551234.567
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error occurred

### Error Response Format

```json
{
  "success": false,
  "message": "Error description",
  "data": null
}
```

---

## Language Support

Currently supported languages:

| Code | Language | Status |
|-------|----------|--------|
| `zh` | Chinese | ✅ Supported |

Future languages can be added by extending the `LanguageCode` enum.

---

## Rate Limiting

No rate limiting is currently implemented. This may be added in future versions.

---

## Examples

### Complete Workflow

1. **Create a session:**

```bash
curl -X POST http://localhost:7770/api/session \
  -H "Content-Type: application/json" \
  -d '{"language": "zh"}'
```

2. **Get session status:**

```bash
curl http://localhost:7770/api/session/{session_id}/status
```

3. **Get latest translation:**

```bash
curl http://localhost:7770/api/translation/{session_id}
```

4. **Stream real-time updates:**

```bash
curl -N -H "Accept: text/event-stream" \
  http://localhost:7770/api/sse/translation/{session_id}
```

5. **Close session:**

```bash
curl -X DELETE http://localhost:7770/api/session/{session_id}
```

### Broadcast Workflow (Simplified)

For church volunteers, use the broadcast API:

1. **Start broadcast:**

```bash
curl -X POST http://localhost:7770/api/broadcast/start \
  -H "Content-Type: application/json" \
  -d '{"language": "zh"}'
```

2. **Check broadcast status:**

```bash
curl http://localhost:7770/api/broadcast/status?language=zh
```

3. **Clients connect to stream:**

```bash
curl -N -H "Accept: text/event-stream" \
  http://localhost:7770/api/sse/broadcast/zh
```

4. **Stop broadcast:**

```bash
curl -X POST http://localhost:7770/api/broadcast/stop \
  -H "Content-Type: application/json" \
  -d '{"language": "zh"}'
```

### Windows Volunteer Scripts

For volunteers on Windows, use the provided batch scripts in `scripts/`:

- `start_transcription.bat` - Double-click to start transcription
- `stop_transcription.bat` - Stop the transcription service
- `list_audio_devices.bat` - Find audio device names

See `scripts/README.md` for detailed instructions.

---

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-mock pytest-asyncio

# Run all tests
pytest

# Run specific test file
pytest tests/test_sessions.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=app
```

### Test Database

Tests use a separate MongoDB database (`test_godlang`) to avoid interfering with development data.

---

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running: `docker-compose up mongodb`
   - Check connection string in `.env` file

2. **FFmpeg Not Found**
   - Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu/Debian)
   - Verify installation: `ffmpeg -version`

3. **No Translations Available**
   - Check if audio pipeline is running
   - Verify Groq API key is set in `.env`

4. **SSE Connection Issues**
   - Ensure proper headers: `Accept: text/event-stream`
   - Check for firewall/proxy interference

### Debug Mode

Enable debug logging by setting `FLASK_DEBUG=1` in environment variables.

---

## Changelog

### v1.1.0 (2025-12-14)

- Added Broadcast API for simplified volunteer workflow
- New `/api/broadcast/start`, `/api/broadcast/stop`, `/api/broadcast/status` endpoints
- New `/api/sse/broadcast/{language}` SSE endpoint with auto-session creation
- Windows batch scripts for volunteers
- Session auto-creates when first client connects

### v1.0.0 (2025-12-12)

- Initial API release
- Session management endpoints
- Translation retrieval endpoints
- Server-Sent Events for real-time updates
- Health check endpoint
- Chinese language support
