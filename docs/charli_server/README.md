# CHARLI Server

Central NestJS backend for all CHARLI devices. Runs on the Mac Mini alongside OpenClaw.

## Architecture

```
Pi Desk Hub ─────┐                                                    ┌→ OpenClaw (Mac Mini:18789)
iPhone (Glasses) ─┼──→ CHARLI Server (NestJS, Mac Mini:3000) ────────┤
CLI (Terminal) ───┤         │                                         └→ Python Sidecar (Mac Mini:3001)
Future Devices ───┘     SQLite DB                                         faster-whisper + espeak-ng/Piper
```

**Two processes:**
- **NestJS (port 3000)** — API gateway: auth, routing, database, WebSockets, orchestration
- **Python sidecar (port 3001)** — ML worker: `/transcribe` and `/tts` endpoints

Devices are thin clients — they capture input and play output. The server handles ALL processing.

## Quick Start

### Option A: Docker Compose (Recommended)

One command starts both the NestJS server and Python sidecar:

```bash
cd charli_server
cp .env.example .env       # Edit with your OpenClaw token
                           # Set OPENCLAW_URL=http://host.docker.internal:18789

docker compose up
# → charli-sidecar loads Whisper model...
# → charli-server runs migrations, seeds DB, starts on :3000
```

The database is auto-created and seeded on first run. Save the API keys from the logs.

### Option B: Bare-Metal

### 1. NestJS Server

```bash
cd charli_server
cp .env.example .env       # Edit with your OpenClaw token
npm install

# Prisma 7 uses a driver adapter (better-sqlite3) instead of the Rust engine.
# The DB connection is configured in prisma.config.ts and .env, NOT in schema.prisma.
npx prisma generate         # Generate the Prisma client into prisma/generated/
npx prisma db push          # Create/sync the SQLite database
npx ts-node prisma/seed.ts  # Create default devices (prints API keys — save them!)

npm run start:dev           # → http://localhost:3000
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

# Interactive API docs
open http://localhost:3000/docs
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_URL` | `http://localhost:18789` | OpenClaw gateway URL |
| `OPENCLAW_TOKEN` | | Auth token from `~/.openclaw/openclaw.json` |
| `SIDECAR_URL` | `http://localhost:3001` | Python sidecar URL |
| `CHARLI_SERVER_PORT` | `3000` | NestJS server port |
| `DATABASE_URL` | `file:./prisma/charli.db` | SQLite database path (used by both prisma.config.ts and PrismaService) |
| `ADMIN_API_KEY` | | Admin key for device registration |

## Naming Conventions

| Context | Convention | Examples |
|---------|-----------|----------|
| Directory / module names | `snake_case` | `charli_server`, `charli_home`, `charli_glasses` |
| Device names (DB, API) | `kebab-case` | `charli-home`, `charli-glasses`, `charli-cli` |
| Device types (DB, prompts) | `kebab-case` | `desk-hub`, `smart-glasses`, `phone`, `cli` |

## Project Structure

```
charli_server/
├── prisma/                    ← Database schema + generated client
│   ├── schema.prisma          ← Models only (no url — that's in prisma.config.ts)
│   ├── generated/             ← Auto-generated Prisma client (gitignored)
│   ├── seed.ts                ← Seed script for default devices
│   └── charli.db              ← SQLite database (gitignored)
├── prisma.config.ts           ← Prisma 7 CLI config (DB url, migrations, seed)
├── sidecar/                   ← Python ML sidecar (STT + TTS)
│   ├── sidecar.py             ← FastAPI: /transcribe + /tts
│   └── requirements.txt
├── src/
│   ├── main.ts                ← Bootstrap + Swagger setup
│   ├── app.module.ts          ← Root module
│   ├── ask/                   ← LLM queries (text + vision)
│   │   └── prompts/           ← Default per-device system prompts
│   ├── transcribe/            ← Speech-to-text (proxies to sidecar)
│   ├── tts/                   ← Text-to-speech (proxies to sidecar)
│   ├── pipeline/              ← Full voice pipeline orchestrator
│   ├── conversation/          ← Conversation history (Prisma CRUD)
│   ├── device/                ← Device registry (API keys NOT exposed on GET)
│   ├── auth/                  ← API key guard + admin key support
│   ├── events/                ← Socket.IO WebSocket gateway
│   ├── health/                ← Health check (no auth)
│   ├── prisma/                ← PrismaService (driver adapter setup)
│   └── common/                ← Shared decorators (@CurrentDevice)
└── .env.example
```

## Key Design Decisions

- **Prisma 7 driver adapter:** No Rust engine — uses `@prisma/adapter-better-sqlite3` directly. Connection URL lives in `.env` and is read by both `prisma.config.ts` (CLI) and `prisma.service.ts` (runtime).
- **API keys not leaked:** `GET /api/devices` strips `apiKey` from responses. Keys are only shown once on `POST /api/devices` (creation).
- **System prompts per device type:** Defaults in `src/ask/prompts/system-prompts.ts`, overridable per device via the DB `systemPrompt` field. Voice device types (`desk-hub`, `smart-glasses`, `phone`) get short spoken responses; the `cli` type gets longer markdown-formatted responses with 10 turns of conversation context (vs 3 for voice).
