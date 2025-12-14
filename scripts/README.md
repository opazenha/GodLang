# Church Service Transcription - Volunteer Guide

## Quick Start

### Starting Transcription

1. **Double-click** `start_transcription.bat`
2. The script will:
   - Connect to the GodLang server
   - Start capturing audio from the mixing board
   - Begin transcribing and translating

3. **Keep the window open** while the service is running
4. Clients can now connect to receive translations

### Stopping Transcription

- **Close the command window**, OR
- **Press Ctrl+C** in the window, OR
- **Double-click** `stop_transcription.bat`

---

## Setup (One-Time)

### 1. Install FFmpeg

FFmpeg is required for audio capture.

1. Download from: <https://ffmpeg.org/download.html>
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH

### 2. Find Your Audio Device Name

1. Connect the mixing board to the computer
2. Double-click `list_audio_devices.bat`
3. Note the exact name of your audio device

### 3. Configure the Script

1. Right-click `start_transcription.bat` → Edit
2. Update these values:

```batch
set SERVER_URL=http://localhost:7770    :: Server address
set LANGUAGE=zh                          :: Target language (zh = Chinese)
set AUDIO_DEVICE=Mixing Board            :: Your audio device name
```

---

## Troubleshooting

### "FFmpeg is not installed"

- Install FFmpeg and add it to PATH (see Setup section)

### "Cannot connect to server"

- Ensure the GodLang server is running
- Check the SERVER_URL is correct

### "No audio being captured"

- Run `list_audio_devices.bat` to verify device name
- Check the mixing board is connected and recognized by Windows
- Try a different audio device name

### Clients not receiving translations

- Verify the broadcast is active: visit `http://localhost:7770/api/broadcast/status`
- Check the server logs for errors

---

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/broadcast/status` | Check broadcast status |
| `POST /api/broadcast/start` | Start broadcast (body: `{"language": "zh"}`) |
| `POST /api/broadcast/stop` | Stop broadcast (body: `{"language": "zh"}`) |
| `GET /api/sse/broadcast/zh` | SSE stream for Chinese translations |

---

## Files

| File | Purpose |
|------|---------|
| `start_transcription.bat` | Start transcription service |
| `stop_transcription.bat` | Stop transcription service |
| `list_audio_devices.bat` | List available audio devices |
