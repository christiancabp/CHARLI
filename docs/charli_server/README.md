# CHARLI Server

Central NestJS backend for all CHARLI devices. Runs on the Mac Mini alongside OpenClaw.

## Architecture

```
Pi Desk Hub ─────┐                                                    ┌→ OpenClaw (Mac Mini:18789)
iPhone (Glasses) ─┼──→ CHARLI Server (NestJS, Mac Mini:3000) ────────┤
Future Devices ───┘         │                                         └→ Python Sidecar (Mac Mini:3001)
                        SQLite DB                                         faster-whisper + espeak-ng/Piper
```

**Two processes:**
- **NestJS (port 3000)** — API gateway: auth, routing, database, WebSockets, orchestration
- **Python sidecar (port 3001)** — ML worker: `/transcribe` and `/tts` endpoints

Devices are thin clients — they capture input and play output. The server handles ALL processing.

## Quick Start

### 1. NestJS Server

```bash
cd charli_server
cp .env.example .env       # Edit with your OpenClaw token
npm install
npx prisma migrate dev     # Create/update database
npx prisma db seed         # Create default devices (prints API keys!)
npm run start:dev          # → http://localhost:3000
```

### 2. Python Sidecar

```bash
cd charli_server/sidecar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sidecar.py         # → http://localhost:3001
```

### 3. Verify

```bash
# Health check
curl http://localhost:3000/health

# Ask a question (use API key from seed output)
curl -X POST http://localhost:3000/api/ask \
  -H "X-API-Key: chk_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello CHARLI!"}'

# Voice pipeline (send audio, get audio back)
curl -X POST http://localhost:3000/api/pipeline/voice \
  -H "X-API-Key: chk_your_key_here" \
  -F "audio=@recording.wav" \
  -o response.wav
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_URL` | `http://localhost:18789` | OpenClaw gateway URL |
| `OPENCLAW_TOKEN` | | Auth token from `~/.openclaw/openclaw.json` |
| `SIDECAR_URL` | `http://localhost:3001` | Python sidecar URL |
| `CHARLI_SERVER_PORT` | `3000` | NestJS server port |
| `DATABASE_URL` | `file:./prisma/charli.db` | SQLite database path |
| `ADMIN_API_KEY` | | Admin key for device registration |

## Project Structure

```
charli_server/
├── prisma/              ← Database schema + migrations
├── sidecar/             ← Python ML sidecar (STT + TTS)
│   ├── sidecar.py       ← FastAPI: /transcribe + /tts
│   └── requirements.txt
├── src/
│   ├── main.ts          ← Bootstrap
│   ├── app.module.ts    ← Root module
│   ├── ask/             ← LLM queries (text + vision)
│   ├── transcribe/      ← Speech-to-text (via sidecar)
│   ├── tts/             ← Text-to-speech (via sidecar)
│   ├── pipeline/        ← Full voice pipeline orchestrator
│   ├── conversation/    ← Conversation history (Prisma)
│   ├── device/          ← Device registry
│   ├── auth/            ← API key guard
│   ├── events/          ← WebSocket gateway
│   ├── health/          ← Health check
│   ├── prisma/          ← Prisma service
│   └── common/          ← Shared decorators
└── .env.example
```
