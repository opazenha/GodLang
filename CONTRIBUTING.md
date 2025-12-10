# Contributing to GodLang

## Prerequisites

Before you start, make sure you have these installed:

- [ ] **Python 3.12+** - [Download](https://www.python.org/downloads/)
- [ ] **Conda** - [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (recommended)
- [ ] **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- [ ] **FFmpeg** - See installation below
- [ ] **Git** - [Download](https://git-scm.com/)

---

## Step 1: Install FFmpeg

### Linux (Arch)

```bash
sudo pacman -S ffmpeg
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update && sudo apt install ffmpeg
```

### Windows

```powershell
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

### Verify Installation

```bash
ffmpeg -version
```

---

## Step 2: Clone the Repository

```bash
git clone <repo-url>
cd GodLang
```

---

## Step 3: Create Conda Environment

```bash
# Create environment
conda create -n GodLang python=3.12 -y

# Activate it
conda activate GodLang
```

> ⚠️ **Always activate before working:**
>
> ```bash
> conda activate GodLang
> ```

---

## Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 5: Configure Environment

```bash
# Copy the example file
cp .env.example .env
```

Now edit `.env` and add your Groq API key:

```bash
# Open in your editor
nano .env   # or code .env, vim .env, etc.
```

Find this line and add your key:

```text
GROQ_API_KEY=your-actual-api-key-here
```

> 🔑 Get your API key at: <https://console.groq.com/keys>

---

## Step 6: Start MongoDB

```bash
docker-compose up -d mongodb
```

Verify it's running:

```bash
docker ps
# Should show mongodb container running
```

---

## Step 7: Run the App

```bash
python run.py
```

You should see:

```text
 * Running on http://127.0.0.1:7770
```

---

## Testing the Audio Pipeline

### Quick Test (2 terminals needed)

**Terminal 1** - Start the pipeline:

```bash
conda activate GodLang
python scripts/test_audio_pipeline.py --run
```

**Terminal 2** - Start audio capture:

```bash
ffmpeg -f pulse -i default -ar 16000 -ac 1 -c:a flac \
  -f segment -segment_time 5 -strftime 1 \
  /tmp/godlang/pending/%Y%m%d_%H%M%S.flac
```

Speak into your mic. You should see logs in Terminal 1 showing files being processed.

Press `Ctrl+C` in both terminals to stop.

---

## Useful Commands

| What | Command |
|------|---------|
| Activate environment | `conda activate GodLang` |
| Start MongoDB | `docker-compose up -d mongodb` |
| Stop MongoDB | `docker-compose down` |
| Run app | `python run.py` |
| Run tests | `pytest` |
| List audio devices | `pactl list sources short` |
| Show FFmpeg command | `python scripts/test_audio_pipeline.py --show-command` |

---

## Project Structure (Key Files)

```text
GodLang/
├── app/
│   ├── config.py          ← Configuration settings
│   └── services/
│       ├── audio.py       ← Audio pipeline logic
│       └── groq_client.py ← Groq API integration
├── scripts/
│   └── test_audio_pipeline.py  ← Dev testing
├── docs/
│   ├── PRD.md             ← Product requirements
│   └── epics/             ← Task tracking
├── .env                   ← Your local config (don't commit!)
└── requirements.txt       ← Python dependencies
```

---

## Troubleshooting

### "No module named 'flask'"

You forgot to activate conda:

```bash
conda activate GodLang
```

### "GROQ_API_KEY not configured"

Edit your `.env` file and add your API key.

### "Cannot connect to MongoDB"

Start the container:

```bash
docker-compose up -d mongodb
```

### FFmpeg "Connection refused" or no audio

List your audio devices and pick the right one:

```bash
pactl list sources short
```

Then set `AUDIO_DEVICE` in `.env`:

```text
AUDIO_DEVICE=alsa_input.pci-0000_00_1f.3-platform-skl_hda_dsp_generic.HiFi__Mic1__source
```

---

## Need Help?

1. Check the [docs/PRD.md](docs/PRD.md) for project overview
2. Check [docs/epics/](docs/epics/) for detailed task breakdowns
3. Ask in the team chat
