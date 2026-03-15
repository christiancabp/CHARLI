# CHARLI Glasses

**Meta Ray-Ban Smart Glasses integration for CHARLI** — extending CHARLI's reach from the desk into the real world.

> *"Hey Charli, what am I looking at?"*
> *"That's the Rockefeller Center, sir. Want directions or more info?"*

## What Is This?

CHARLI Glasses turns Meta Ray-Ban Display smart glasses into a wearable CHARLI interface. The glasses become CHARLI's eyes, ears, and mouth — connected to CHARLI's brain (OpenClaw on Mac Mini) through an iPhone companion app.

Think Tony Stark talking to FRIDAY through his glasses.

## Architecture

```
Meta Ray-Ban Glasses
    │
    ├── Bluetooth Audio ──→ iPhone Mic Input (voice)
    ├── SDK Camera API ───→ iPhone App (image capture)
    └── Bluetooth Audio ←── iPhone Speaker Output (response)
                              │
                    iPhone Companion App
                    (Swift/SwiftUI)
                              │
                    WiFi / Tailscale
                              │
                    CHARLI Glasses API Server
                    (FastAPI on Pi or Mac Mini)
                              │
                    Mac Mini (OpenClaw Brain)
```

## Project Structure

```
charli_glasses/
├── README.md                       ← You are here
├── api/                            ← Backend API server
│   ├── server.py                   ← FastAPI server (voice + vision endpoints)
│   ├── requirements.txt            ← Python dependencies
│   └── src/
│       ├── ask_charli_vision.py    ← Vision-capable ask (text + images)
│       ├── transcribe.py           ← Whisper speech-to-text
│       └── tts.py                  ← Text-to-speech (espeak-ng / Piper)
├── ios/                            ← iOS companion app
│   └── CHARLIGlasses/
│       ├── CHARLIGlassesApp.swift  ← App entry point
│       ├── ContentView.swift       ← Main UI (orb, status, transcript)
│       ├── AudioManager.swift      ← Bluetooth audio + wake word
│       └── CHARLIAPIClient.swift   ← HTTP client for CHARLI API
└── docs/
    └── PROPOSAL.md                 ← Full proposal and architecture details
```

## Quick Start — API Server

```bash
# From the charli_glasses/api/ directory
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables (same as desk hub)
export CHARLI_HOST="http://100.91.206.1:18789"   # Mac Mini OpenClaw URL
export CHARLI_TOKEN="your-openclaw-token"          # Auth token

# Optional: install espeak-ng for TTS
# macOS: brew install espeak-ng
# Linux: sudo apt install espeak-ng

# Start the server
python3 server.py
# → http://localhost:8090/docs (interactive API docs)
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/voice-query` | Audio in → Audio out (full pipeline) |
| `POST` | `/api/voice-query-text` | Audio in → Text out (for debugging) |
| `POST` | `/api/ask-vision` | Text + optional image → Text out |
| `POST` | `/api/ask` | Text in → Text out |
| `GET` | `/api/conversation` | Get glasses conversation history |
| `DELETE` | `/api/conversation` | Clear conversation history |
| `GET` | `/health` | Health check |

### Example: Voice Query

```bash
# Send audio, get audio back
curl -X POST http://localhost:8090/api/voice-query \
     -F "audio=@recording.wav" \
     -o response.wav

# Send audio, get text back
curl -X POST http://localhost:8090/api/voice-query-text \
     -F "audio=@recording.wav"
# → {"transcription": "What time is it?", "answer": "It's 5:42 PM."}
```

### Example: Vision Query

```bash
# Text + image → text
curl -X POST http://localhost:8090/api/ask-vision \
     -H 'Content-Type: application/json' \
     -d '{
       "question": "What am I looking at?",
       "image_base64": "<base64-encoded-jpeg>",
       "image_mime": "image/jpeg"
     }'
```

## Roadmap

### Phase 1 — Bluetooth Audio Bridge (now)
- [x] API server with voice-query endpoint
- [x] Vision-capable ask_charli (text + images)
- [x] iOS companion app scaffold
- [ ] Purchase Meta Ray-Ban Display glasses
- [ ] Pair glasses and verify Bluetooth audio routing
- [ ] Integrate Porcupine wake word on iOS

### Phase 2 — Camera Vision
- [ ] Register for Meta Wearables Device Access Toolkit
- [ ] Integrate camera capture in iOS app
- [ ] "What am I looking at?" with real POV photos

### Phase 3 — HUD Display
- [ ] When Meta's display APIs become available
- [ ] Show CHARLI responses as text overlay in glasses
- [ ] Contextual information overlays

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHARLI_HOST` | OpenClaw gateway URL | `http://100.91.206.1:18789` |
| `CHARLI_TOKEN` | OpenClaw auth token | (required) |
| `CHARLI_GLASSES_PORT` | API server port | `8090` |
| `CHARLI_WHISPER_MODEL` | Whisper model size | `base` |
| `CHARLI_PIPER_MODEL` | Path to Piper TTS model | (empty = use espeak-ng) |

## Hardware

| Item | Status |
|------|--------|
| Meta Ray-Ban Display (Shiny Sand + Neural Band) | Need to purchase ($799) |
| iPhone | Already have |
| Mac Mini (OpenClaw brain) | Already have |
| Tailscale network | Already configured |
| Picovoice access key | Already have |
