<div align="center">

# C.H.A.R.L.I.

### Christian's Home Artificial Reasoning & Learning Intelligence

*A personal AI assistant ecosystem — one brain, many devices.*

---

**Desk Hub** · **Smart Glasses** · **Future Devices**
all connected to one central brain

[![NestJS](https://img.shields.io/badge/NestJS-E0234E?style=flat&logo=nestjs&logoColor=white)](https://nestjs.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Swift](https://img.shields.io/badge/Swift-F05138?style=flat&logo=swift&logoColor=white)](https://swift.org/)
[![Prisma](https://img.shields.io/badge/Prisma_7-2D3748?style=flat&logo=prisma&logoColor=white)](https://prisma.io/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi_5-C51A4A?style=flat&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-010101?style=flat&logo=socket.io&logoColor=white)](https://socket.io/)

</div>

---

## What is CHARLI?

CHARLI is a personal AI assistant that lives across multiple devices — a desk hub with a touchscreen, smart glasses, and whatever comes next. Say **"Hey Charli"** and get a spoken response, ask about what you're looking at through the glasses camera, or just type a question.

All devices are **thin clients**. They handle hardware (mic, speaker, screen, camera) and nothing else. One central server does all the thinking.

> This is a father-daughter learning project. Code comments are educational and explanatory — written so an 11-year-old can follow along.

---

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │             Mac Mini (the brain)            │
                    │                                             │
 Pi Desk Hub ──────►│  CHARLI Server    Python Sidecar   OpenClaw │
 iPhone Glasses ───►│  (NestJS :3000)   (FastAPI :3001)  (:18789) │
 Future Device ────►│                                             │
                    │  Auth · Pipeline   Whisper STT     LLM      │
                    │  WebSocket · DB    TTS (Piper)     Gateway  │
                    └─────────────────────────────────────────────┘
```

**One request, fully orchestrated:**

```
Device sends audio ──► Server transcribes (Whisper)
                       Server asks the LLM (OpenClaw)
                       Server generates speech (Piper/espeak)
                  ◄── Device plays the audio response
```

Real-time state updates flow to all connected clients via Socket.IO — the desk hub UI shows glasses activity and vice versa.

---

## The Devices

### CHARLI Home — Desk Hub

A JARVIS-style assistant on a Raspberry Pi 5 with a 7" touchscreen.

- **Wake word** — Say "Hey Charli" and the animated orb lights up
- **Voice pipeline** — Record → server processes → play response
- **JARVIS UI** — Animated glowing orb + live conversation transcript
- **Hardware** — Pi 5, USB mic, Bluetooth speaker, 7" touchscreen

```
┌──────────────────────────────────────────────────────────────────┐
│ C.H.A.R.L.I.                                       ● 17:42:03    │
├────────────────────────┬─────────────────────────────────────────┤
│                        │ TRANSCRIPT                              │
│     ╭────────────╮     │                                         │
│    ╱  ┌────────┐  ╲    │ ┌─YOU──────────────────────────────┐    │
│   │   │ ░░░░░░ │   │   │ │ What's the weather like today?   │    │
│   │   │ ░ORB ░ │   │   │ └──────────────────────────────────┘    │
│    ╲  └────────┘  ╱    │ ┌─CHARLI───────────────────────────┐    │
│     ╰────────────╯     │ │ It's 72 degrees and sunny.       │    │
│      [ SPEAKING ]      │ └──────────────────────────────────┘    │
├────────────────────────┴─────────────────────────────────────────┤
└──────────────────────────────────────────────────────────────────┘
```

### CHARLI Glasses — Smart Glasses

Meta Ray-Ban Display smart glasses as a wearable CHARLI interface.

- **iPhone companion app** — Swift/SwiftUI, Bluetooth audio bridge
- **Voice + Vision** — Ask questions about what you see through the camera
- **On the go** — CHARLI in your ear, wherever you are

> *"Hey Charli, what am I looking at?"*
> *"That's the Rockefeller Center, sir."*

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Server** | NestJS + TypeScript | API gateway, auth, orchestration, WebSockets |
| **Database** | Prisma 7 + SQLite | Device registry, conversation history |
| **Speech-to-Text** | faster-whisper (Python sidecar) | Local, free, fast transcription |
| **Text-to-Speech** | espeak-ng / Piper (Python sidecar) | Local, free voice synthesis |
| **LLM** | OpenClaw gateway | Routes to Claude, Gemini, local models |
| **Desk Hub** | Raspberry Pi 5 + Python | Wake word, mic, speaker, touchscreen |
| **Glasses** | Swift / SwiftUI (iOS) | Bluetooth audio, camera capture |
| **Real-time** | Socket.IO | Live state + message broadcasting |
| **Network** | Tailscale | Private mesh VPN connecting all devices |
| **API Docs** | Swagger / OpenAPI | Interactive docs at `/docs` |

---

## Quick Start

### 1. Start the Brain (Mac Mini)

```bash
# Python sidecar (ML worker)
cd charli_server/sidecar
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 sidecar.py                          # → localhost:3001

# NestJS server
cd charli_server
npm install
cp .env.example .env                        # Add your OpenClaw token
npx prisma generate && npx prisma db push   # Set up database
npx ts-node prisma/seed.ts                  # Create devices (save the API keys!)
npm run start:dev                           # → localhost:3000
```

### 2. Start a Device

**Desk Hub (Pi):**
```bash
ssh charli@charli-home.local
export CHARLI_SERVER_URL="http://charli-server:3000"
export CHARLI_API_KEY="chk_your_key_here"
python3 charli_home.py
```

**Glasses (iOS):**
Set server URL and API key in the app, build from Xcode, and go.

### 3. Talk to CHARLI

Say **"Hey Charli"** at the desk hub, or use the API:

```bash
# Text query
curl -X POST http://localhost:3000/api/ask \
  -H "X-API-Key: chk_..." \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello CHARLI!"}'

# Voice query (audio in → audio out)
curl -X POST http://localhost:3000/api/pipeline/voice \
  -H "X-API-Key: chk_..." \
  -F "audio=@recording.wav" -o response.wav
```

---

## Project Structure

```
CHARLI/
├── charli_server/           Central NestJS backend (the brain)
│   ├── src/
│   │   ├── pipeline/        Voice orchestrator (transcribe → ask → TTS)
│   │   ├── ask/             LLM queries + per-device system prompts
│   │   ├── transcribe/      STT proxy to Python sidecar
│   │   ├── tts/             TTS proxy to Python sidecar
│   │   ├── conversation/    Conversation history (Prisma)
│   │   ├── device/          Device registry + API key auth
│   │   ├── events/          Socket.IO WebSocket gateway
│   │   └── auth/            API key guard
│   ├── sidecar/             Python ML sidecar (Whisper + TTS)
│   └── prisma/              Database schema + migrations
│
├── charli_home/             Pi desk hub (thin client)
│   ├── charli_home.py       Async orchestrator
│   ├── src/                 Building blocks (wake word, record, etc.)
│   └── web/static/          JARVIS touchscreen UI
│
├── charli_glasses/          Smart glasses (thin client)
│   └── ios/                 Swift/SwiftUI companion app
│
└── docs/                    Documentation
    ├── charli_server/       Server docs (architecture, API, setup)
    ├── charli_glasses/      Glasses proposal + design
    └── raspberry_pi/        Pi setup guides + cheat sheets
```

---

## API at a Glance

All `/api/*` endpoints require `X-API-Key` header. Full interactive docs at `/docs` (Swagger).

| Endpoint | What it does |
|----------|-------------|
| `POST /api/pipeline/voice` | Send audio, get audio back (full pipeline) |
| `POST /api/pipeline/voice-text` | Send audio, get JSON back |
| `POST /api/ask` | Text question → text answer |
| `POST /api/ask/vision` | Text + image → text answer |
| `POST /api/transcribe` | Audio → text |
| `POST /api/tts` | Text → audio |
| `GET /api/conversation` | Get device's conversation history |
| `GET /api/devices` | List registered devices |
| `GET /health` | Health check (no auth) |
| `ws://server:3000/events` | Real-time state + message stream |

---

## Documentation

| Doc | Description |
|-----|-------------|
| [`docs/charli_server/README.md`](docs/charli_server/README.md) | Server quick start |
| [`docs/charli_server/architecture.md`](docs/charli_server/architecture.md) | System design + Prisma 7 details |
| [`docs/charli_server/api-reference.md`](docs/charli_server/api-reference.md) | Full API reference |
| [`docs/charli_server/orchestration.md`](docs/charli_server/orchestration.md) | Running the full stack (dev + prod) |
| [`docs/charli_server/device-migration.md`](docs/charli_server/device-migration.md) | Migrating devices to central server |
| [`docs/charli_server/future-improvements.md`](docs/charli_server/future-improvements.md) | Roadmap + 20 improvement ideas |
| [`charli_home/README.md`](charli_home/README.md) | Desk hub setup (Pi) |
| [`charli_glasses/README.md`](charli_glasses/README.md) | Glasses setup (iOS) |

---

## Roadmap

- [x] Central NestJS backend with auth, pipeline, WebSockets
- [x] Python sidecar for local STT + TTS (zero API costs)
- [x] Prisma 7 + SQLite database (devices, conversations, messages)
- [x] Pi desk hub as thin client with JARVIS UI
- [x] iOS glasses app with vision support
- [x] Swagger API documentation
- [x] Socket.IO real-time cross-device updates
- [ ] Piper TTS for natural voice
- [ ] Voice Activity Detection (stop recording on silence)
- [ ] Streaming LLM responses
- [ ] Pi camera for desk hub vision
- [ ] Smart home integration
- [ ] Admin dashboard

---

<div align="center">

*Built with love by Christian and Isabella Bermeo, 2026*

**One brain. Many devices. Zero cloud dependency.**

</div>
