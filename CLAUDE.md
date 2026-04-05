# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CHARLI (C.H.A.R.L.I.) is a personal AI assistant ecosystem with multiple devices that all connect to one central backend. The project is a father-daughter learning project — code comments tend to be educational and explanatory.

### Components

1. **CHARLI Server** (`charli_server/`) — Central NestJS backend on Mac Mini. THE brain. Handles auth, LLM queries, STT, TTS, conversation history, WebSockets. Swagger docs at `/docs`.
2. **Python Sidecar** (`charli_server/sidecar/`) — FastAPI ML worker (faster-whisper STT + espeak-ng/Piper TTS). Runs alongside NestJS on Mac Mini.
3. **Desk Hub** (`charli_home/`) — Raspberry Pi 5 thin client. Hardware I/O only: wake word, mic, speaker, touchscreen UI. Zero backend logic.
4. **Glasses** (`charli_glasses/ios/`) — iOS companion app for Meta Ray-Ban glasses. Pure client: records audio, sends to server, plays response.
5. **CLI** (`charli_cli/`) — Terminal client (Node.js). Text chat with CHARLI from any machine on the Tailscale network. Inspired by claude-code patterns.

## Architecture

```
Pi Desk Hub ─────┐                                                    ┌→ OpenClaw (Mac Mini:18789)
iPhone (Glasses) ─┼──→ CHARLI Server (NestJS, Mac Mini:3000) ────────┤
CLI (any machine) ┤         │                                         └→ Python Sidecar (Mac Mini:3001)
Future Devices ───┘     SQLite DB                                         faster-whisper + espeak-ng/Piper
```

**Devices are thin clients** — they capture input (audio, images, text) and play/display output. ALL processing lives on the Mac Mini. No server code runs on devices.

**State machine** (voice devices): `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

### CHARLI Server (`charli_server/`)

NestJS (TypeScript) with Prisma 7 + SQLite. Key details:

- **Prisma 7:** No Rust engine. Uses `@prisma/adapter-better-sqlite3` driver adapter.
  - `prisma.config.ts` — CLI config (migrations, db push). Reads `DATABASE_URL` from env.
  - `src/prisma/prisma.service.ts` — Runtime adapter setup. Also reads `DATABASE_URL`.
  - `prisma/generated/` — Auto-generated client (gitignored). Run `npx prisma generate` after schema changes.
  - Import types with `from '@prisma/generated'` (tsconfig path alias).
- **API keys:** `GET /api/devices` strips `apiKey` from responses. Keys only visible on `POST /api/devices` (creation).

Modules:
- `auth/` — API key guard (`X-API-Key` header) + admin key support
- `device/` — Device registry (Prisma + SQLite)
- `ask/` — LLM queries to OpenClaw (text + vision), per-device system prompts
- `transcribe/` — STT proxy to Python sidecar
- `tts/` — TTS proxy to Python sidecar
- `pipeline/` — Full voice orchestrator (transcribe → ask → tts)
- `conversation/` — Conversation history per device
- `events/` — Socket.IO WebSocket gateway for real-time state
- `health/` — Health check (no auth)

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

### CLI (`charli_cli/`)

Terminal client (Node.js/TypeScript). Uses native `fetch` + Commander.js:
- `src/cli.ts` — Commander program, command routing
- `src/commands/ask.ts` — `charli ask "question"` text chat
- `src/commands/status.ts` — `charli status` health/config check
- `src/commands/init.ts` — `charli init` setup wizard (server URL, API key, Tailscale detection)
- `src/lib/api-client.ts` — HTTP client wrapping `/api/ask` and `/health`
- `src/lib/config.ts` — Loads/saves `~/.charli/config.json`, env var overrides
- `src/lib/tailscale.ts` — Tailscale detection for auto-suggesting server URL
- `src/lib/output.ts` — Chalk-based formatting helpers
- `bin/charli.js` — Entry point (`#!/usr/bin/env node`)

Config: `~/.charli/config.json` with `CHARLI_SERVER_URL` / `CHARLI_API_KEY` env var overrides.

CLI device type gets markdown-formatted responses, code blocks, longer answers (1024 max tokens), and 10 turns of conversation history (vs 3 for voice devices).

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

# Terminal 4: CLI (any machine on Tailscale)
cd charli_cli && npm run build
node bin/charli.js init                                # → setup wizard
node bin/charli.js ask "Hello CHARLI!"                 # → text chat
```

### CHARLI Server Development

```bash
cd charli_server
npm install
cp .env.example .env         # Fill in OPENCLAW_TOKEN

# Prisma 7 setup:
npx prisma generate          # Generate client to prisma/generated/
npx prisma db push           # Create/sync SQLite DB at prisma/charli.db
npx ts-node prisma/seed.ts   # Seed devices (prints API keys — save them!)

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
- `DATABASE_URL` — SQLite path (default: `file:./prisma/charli.db`). Read by both `prisma.config.ts` and `prisma.service.ts`.
- `ADMIN_API_KEY` — Admin key for device registration

#### Pi Desk Hub (`~/.bashrc`)
- `CHARLI_SERVER_URL` — Central server URL (e.g., `http://charli-server:3000`)
- `CHARLI_API_KEY` — API key for this device
- `PICOVOICE_ACCESS_KEY` — Wake word detection key
- `CHARLI_MIC_DEVICE` — ALSA mic device (default: `hw:0,0`)

#### iOS App (UserDefaults)
- `charli_server_url` — Central server URL
- `charli_api_key` — API key for glasses device

#### CLI (`~/.charli/config.json` or env vars)
- `CHARLI_SERVER_URL` — Central server URL (e.g., `http://charli-server:3000`)
- `CHARLI_API_KEY` — API key for this CLI device

## Naming Conventions

| Context | Convention | Examples |
|---------|-----------|----------|
| Directory / module names | `snake_case` | `charli_server`, `charli_home`, `charli_glasses`, `charli_cli` |
| Device names (DB, API) | `kebab-case` | `charli-home`, `charli-glasses`, `charli-cli` |
| Device types (DB, prompts) | `kebab-case` | `desk-hub`, `smart-glasses`, `phone`, `cli` |

## Conventions

- Devices are pure clients — no backend logic, no server code
- All backend logic lives in charli_server (NestJS + Python sidecar)
- NestJS modules follow standard patterns (module/service/controller)
- The JARVIS UI is vanilla HTML/CSS/JS (no build step), connects to server via Socket.IO
- Responses from CHARLI are 1-3 sentences for voice devices (no markdown, natural spoken style); CLI gets longer markdown-formatted responses
- Audio format: 16kHz mono WAV for recording, WAV for TTS responses
- Auth: API key per device via `X-API-Key` header
- Database: SQLite via Prisma 7 driver adapter (swap adapter + provider for Postgres)
- Code comments are educational — this is a father-daughter learning project

## Documentation

Detailed docs live in `docs/charli_server/`:
- `README.md` — Quick start guide
- `api-reference.md` — Full endpoint documentation
- `architecture.md` — System design, Prisma 7 migration details, WebSocket design
- `device-migration.md` — How to migrate devices to the central server
- `orchestration.md` — How to run the full stack (dev + production)
- `future-improvements.md` — Roadmap and upgrade paths

CLI docs live in `docs/charli_cli/`:
- `README.md` — Overview and architecture
- `setup.md` — Installation, `charli init`, Tailscale, config
- `usage.md` — Command reference and examples
