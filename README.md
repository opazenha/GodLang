# GodLang

Real-time church translation service. Captures audio from a mixing board, transcribes to English using Groq Whisper, then translates to Chinese using Groq Qwen 32B.

## Architecture

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Mixing Board│────▶│   FFmpeg    │────▶│  pending/   │
│   (Audio)   │     │ (chunking)  │     │  (files)    │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │ File Watcher
                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │◀────│  Groq Qwen  │◀────│  Groq API   │◀────│ processing/ │
│  (Chinese)  │     │ (Translate) │     │ (Transcribe)│     │  (files)    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| API Framework | Flask |
| Database | MongoDB (Docker) |
| Audio Processing | FFmpeg |
| Transcription | Groq Whisper API |
| Translation | Groq Qwen 32B |

## Quick Start

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- FFmpeg
- Conda (recommended)

### Setup

```bash
# Clone and enter directory
git clone <repo-url>
cd GodLang

# Create conda environment
conda create -n GodLang python=3.12
conda activate GodLang

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start MongoDB
docker-compose up -d mongodb

# Run the app
python run.py
```

### Testing Audio Pipeline

```bash
# Terminal 1: Start the pipeline watcher
conda activate GodLang
python scripts/test_audio_pipeline.py --run

# Terminal 2: Start FFmpeg capture (from laptop mic)
ffmpeg -f pulse -i default -ar 16000 -ac 1 -c:a flac \
  -f segment -segment_time 5 -strftime 1 \
  /tmp/godlang/pending/%Y%m%d_%H%M%S.flac
```

## Project Structure

```text
GodLang/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py             # Configuration (AudioConfig, Config)
│   ├── models/               # Pydantic schemas
│   ├── routes/
│   │   ├── broadcast.py      # Broadcast management API
│   │   ├── session.py        # Session management API
│   │   ├── sse.py            # Server-Sent Events endpoints
│   │   └── translation.py    # Translation retrieval API
│   ├── services/
│   │   ├── audio.py          # Audio pipeline (FFmpeg, FileWatcher)
│   │   ├── broadcast.py      # Broadcast state manager
│   │   ├── database.py       # MongoDB client
│   │   └── groq_client.py    # Groq API client
│   └── utils/
├── scripts/
│   ├── start_transcription.bat  # Windows: Start transcription
│   ├── stop_transcription.bat   # Windows: Stop transcription
│   ├── list_audio_devices.bat   # Windows: List audio devices
│   └── README.md                 # Volunteer guide
├── docs/
│   ├── API.md                # API documentation
│   ├── PRD.md                # Product Requirements
│   └── epics/                # Task tracking
├── docker-compose.yaml
├── requirements.txt
└── run.py
```

## Configuration

Environment variables (`.env`):

```bash
# Flask
FLASK_ENV=development
FLASK_DEBUG=1
FLASK_PORT=7770

# MongoDB
MONGO_URI=mongodb://mongodb:27017/
MONGO_DB_NAME=godlang

# Groq API
GROQ_API_KEY=your-api-key-here

# Audio Processing
AUDIO_CHUNK_DURATION=10      # seconds
AUDIO_SAMPLE_RATE=16000      # Hz
AUDIO_MAX_RETRIES=3
AUDIO_DEVICE=default         # PulseAudio source (Linux)
```

## Audio Pipeline

The audio pipeline uses a file-based approach:

1. **FFmpeg** captures audio and writes 10-second FLAC chunks to `pending/`
2. **FileWatcher** detects new files, waits for stability, queues for processing
3. **Worker** moves to `processing/`, calls Groq API, deletes on success
4. **Failure handling**: retries with backoff, moves to `failed/` after 3 attempts

### Directories

| Directory | Purpose |
|-----------|---------|
| `/tmp/godlang/pending/` | FFmpeg writes chunks here |
| `/tmp/godlang/processing/` | Currently being transcribed |
| `/tmp/godlang/failed/` | Failed after max retries |

### Platform Support

| Platform | Audio Input | Device |
|----------|-------------|--------|
| Linux (dev) | PulseAudio/PipeWire | `default` or mic name |
| Windows (prod) | DirectShow | Mixing board device |

## Development

```bash
# List audio devices
pactl list sources short          # Linux
ffmpeg -list_devices true -f dshow -i dummy  # Windows

# Run tests
pytest

# Show FFmpeg command for current platform
python scripts/test_audio_pipeline.py --show-command
```

## Volunteer Usage (Windows)

For church volunteers running transcription on Windows:

1. **First-time setup**: Run `scripts/list_audio_devices.bat` to find your mixing board device name
2. **Edit configuration**: Update `AUDIO_DEVICE` in `scripts/start_transcription.bat`
3. **Start transcription**: Double-click `scripts/start_transcription.bat`
4. **Stop transcription**: Close the window or run `scripts/stop_transcription.bat`

See `scripts/README.md` for detailed instructions.

## Documentation

- [API Documentation](docs/API.md)
- [Product Requirements (PRD)](docs/PRD.md)
- [Volunteer Guide](scripts/README.md)
- [Epic 1: Setup](docs/epics/epic-1-setup.md)
- [Epic 2: Audio Pipeline](docs/epics/epic-2-audio.md)
- [Epic 3: Transcription](docs/epics/epic-3-transcription.md)
- [Epic 4: Translation](docs/epics/epic-4-translation.md)

## License

Private - Church use only.
