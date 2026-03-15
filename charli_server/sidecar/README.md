# CHARLI Sidecar — Python ML Worker

Minimal FastAPI server that handles speech-to-text and text-to-speech.
Runs alongside the NestJS server on the Mac Mini.

## Why a Sidecar?

The faster-whisper model takes ~3s to load into memory (~200MB). By running it as a persistent process, we load once and keep it hot. Every transcription request then takes ~1-3s instead of ~6s.

## Setup

```bash
cd charli_server/sidecar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Also need espeak-ng for TTS:
# macOS: brew install espeak-ng
# Linux: sudo apt install espeak-ng
```

## Run

```bash
python3 sidecar.py
# → Listening on http://localhost:3001
```

## Endpoints

### POST /transcribe
Accepts audio file (multipart), returns transcription.
```bash
curl -X POST http://localhost:3001/transcribe -F "audio=@test.wav"
# → {"text": "Hello world", "language": "en"}
```

### POST /tts
Accepts JSON, returns WAV audio.
```bash
curl -X POST http://localhost:3001/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!", "language": "en"}' \
  -o output.wav
```

### GET /health
```bash
curl http://localhost:3001/health
# → {"status": "ok", "model": "base", "piper": false}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHARLI_WHISPER_MODEL` | `base` | Whisper model size (base/small/medium) |
| `CHARLI_PIPER_MODEL` | | Path to Piper TTS model (optional) |
| `CHARLI_SIDECAR_PORT` | `3001` | Port to listen on |
