# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CHARLI (C.H.A.R.L.I.) is a personal AI assistant ecosystem with multiple devices that all connect to one central backend. The project is a father-daughter learning project — code comments tend to be educational and explanatory.

### Components

1. **CHARLI Server** (`charli_server/`) — Central NestJS backend on Mac Mini. THE brain. Handles auth, LLM queries, STT, TTS, conversation history, WebSockets. Swagger docs at `/docs`.
2. **Python Sidecar** (`charli_server/sidecar/`) — FastAPI ML worker (faster-whisper STT + espeak-ng/Piper TTS). Runs alongside NestJS on Mac Mini.
3. **Desk Hub** (`charli_home/`) — Raspberry Pi 5 thin client. Hardware I/O only: wake word, mic, speaker, touchscreen UI. Zero backend logic.
4. **Glasses** (`charli_glasses/ios/`) — iOS companion app for Meta Ray-Ban glasses. Pure client: records audio, sends to server, plays response.

## Architecture

```
Pi Desk Hub ─────┐                                                    ┌→ OpenClaw (Mac Mini:18789)
iPhone (Glasses) ─┼──→ CHARLI Server (NestJS, Mac Mini:3000) ────────┤
Future Devices ───┘         │                                         └→ Python Sidecar (Mac Mini:3001)
                        SQLite DB                                         faster-whisper + espeak-ng/Piper
```

**Devices are thin clients** — they capture input (audio, images) and play output (audio). ALL processing lives on the Mac Mini. No server code runs on devices.

**State machine** (same across all devices): `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

### CHARLI Server (`charli_server/`)

NestJS (TypeScript) with these modules:
- `auth/` — API key guard (`X-API-Key` header)
- `device/` — Device registry (Prisma + SQLite)
- `ask/` — LLM queries to OpenClaw (text + vision)
- `transcribe/` — STT proxy to Python sidecar
- `tts/` — TTS proxy to Python sidecar
- `pipeline/` — Full voice orchestrator (transcribe → ask → tts)
- `conversation/` — Conversation history per device
- `events/` — Socket.IO WebSocket gateway for real-time state
- `health/` — Health check

Key endpoints:
- `POST /api/pipeline/voice` — Audio in → audio out (full pipeline)
- `POST /api/ask` — Text question → text answer
- `POST /api/ask/vision` — Text + image → text answer
- `POST /api/transcribe` — Audio → text
- `POST /api/tts` — Text → audio
- Swagger: `GET /docs`

### Desk Hub (`charli_home/`)

Pure thin client. Four concurrent subsystems via `asyncio.gather()`:
1. **Voice Pipeline** — wake word → record → POST to server → play returned audio
2. **UI Server** — minimal `http.server` serving JARVIS static files (port 8080)
3. **System Monitor** — CPU temp, RAM, Tailscale status
4. **Mac Link** — Persistent WebSocket to Mac Mini

Key files:
- **`charli_home.py`** — Async orchestrator (thin client, no FastAPI)
- **`src/charli_server_client.py`** — HTTP client for CHARLI Server
- **`src/state_manager.py`** — Local state tracking for pipeline coordination
- **`src/wake_word.py`** — Porcupine wake word detection
- **`src/record.py`** — USB mic recording via `arecord`
- **`src/system_monitor.py`** — System metrics collector
- **`src/mac_link.py`** — Pi↔Mac persistent WebSocket
- **`web/static/`** — JARVIS UI (HTML/CSS/JS). Socket.IO connects to charli_server.

No backend code: no FastAPI, no REST API, no local transcription, no local LLM calls, no local TTS pipeline.

### Glasses (`charli_glasses/ios/`)

iOS companion app (Swift/SwiftUI):
- `CHARLIAPIClient.swift` — HTTP client pointing to CHARLI Server with `X-API-Key`
- `AudioManager.swift` — Bluetooth audio routing, recording, playback
- `ContentView.swift` — UI with animated status orb
- `CHARLIGlassesApp.swift` — App entry point

No Python backend — the old `charli_glasses/api/` has been removed.

## Development

### Running the Full Stack

```bash
# Terminal 1: Python sidecar (Mac Mini)
cd charli_server/sidecar && python3 sidecar.py        # → localhost:3001

# Terminal 2: NestJS server (Mac Mini)
cd charli_server && npm run start:dev                   # → localhost:3000

# Terminal 3: Desk Hub (Pi, via SSH)
ssh charli@charli-home.local
cd ~/charli-home && python3 charli_home.py              # → localhost:8080
```

### CHARLI Server Development

```bash
cd charli_server
npm install
cp .env.example .env         # Fill in OPENCLAW_TOKEN
npx prisma migrate dev       # Create/update DB
npx prisma db seed            # Seed devices (prints API keys)
npm run start:dev             # Hot-reload dev server — Swagger at /docs
```

### Testing

```bash
# Health check
curl http://localhost:3000/health

# Ask (with API key from seed)
curl -X POST http://localhost:3000/api/ask \
  -H "X-API-Key: chk_..." -H "Content-Type: application/json" \
  -d '{"question": "Hello!"}'

# Voice pipeline
curl -X POST http://localhost:3000/api/pipeline/voice \
  -H "X-API-Key: chk_..." -F "audio=@test.wav" -o response.wav

# Test Pi's server client
python3 charli_home/src/charli_server_client.py
```

### Environment Variables

#### CHARLI Server (`charli_server/.env`)
- `OPENCLAW_URL` — OpenClaw gateway (default: `http://localhost:18789`)
- `OPENCLAW_TOKEN` — Auth token from `~/.openclaw/openclaw.json`
- `SIDECAR_URL` — Python sidecar (default: `http://localhost:3001`)
- `DATABASE_URL` — SQLite path (default: `file:./charli.db`)
- `ADMIN_API_KEY` — Admin key for device registration

#### Pi Desk Hub (`~/.bashrc`)
- `CHARLI_SERVER_URL` — Central server URL (e.g., `http://charli-server:3000`)
- `CHARLI_API_KEY` — API key for this device
- `PICOVOICE_ACCESS_KEY` — Wake word detection key
- `CHARLI_MIC_DEVICE` — ALSA mic device (default: `hw:0,0`)

#### iOS App (UserDefaults)
- `charli_server_url` — Central server URL
- `charli_api_key` — API key for glasses device

## Conventions

- Devices are pure clients — no backend logic, no server code
- All backend logic lives in charli_server (NestJS + Python sidecar)
- NestJS modules follow standard patterns (module/service/controller)
- The JARVIS UI is vanilla HTML/CSS/JS (no build step), connects to server via Socket.IO
- Responses from CHARLI are 1-3 sentences, no markdown, natural spoken style
- Audio format: 16kHz mono WAV for recording, WAV for TTS responses
- Auth: API key per device via `X-API-Key` header
- Database: SQLite via Prisma (one-line change to Postgres later)

## Documentation

Detailed docs live in `docs/charli_server/`:
- `README.md` — Quick start guide
- `api-reference.md` — Full endpoint documentation
- `architecture.md` — System design and rationale
- `device-migration.md` — How to migrate devices to the central server
- `orchestration.md` — How to run the full stack (dev + production)
- `future-improvements.md` — Roadmap and upgrade paths
