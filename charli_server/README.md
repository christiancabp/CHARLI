# CHARLI Server — Developer Guide

Central NestJS backend + Python ML sidecar. This is the brain — all devices talk to it.

## Prerequisites

- **Node.js 22+** and **npm**
- **Python 3.11+**
- **espeak-ng** — `brew install espeak-ng` (macOS) or `sudo apt install espeak-ng` (Linux)
- **OpenClaw** running on `localhost:18789` (LLM gateway)

## Dev Setup

### 1. Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `OPENCLAW_TOKEN` — from `~/.openclaw/openclaw.json`
- `ADMIN_API_KEY` — any random string for bootstrapping devices

### 2. NestJS Server (Terminal 1)

```bash
npm install
npx prisma generate          # Generate Prisma client → prisma/generated/
npx prisma db push           # Create SQLite DB → prisma/charli.db
npx ts-node prisma/seed.ts   # Seed default devices (save the API keys!)
npm run start:dev            # → http://localhost:3000 (hot-reload)
```

### 3. Python Sidecar (Terminal 2)

```bash
cd sidecar
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 sidecar.py           # → http://localhost:3001
```

### 4. Verify

```bash
curl http://localhost:3000/health          # Server health
curl http://localhost:3001/health          # Sidecar health
open http://localhost:3000/docs            # Swagger UI
```

## Common Commands

| Command | What it does |
|---------|-------------|
| `npm run start:dev` | Start NestJS with hot-reload |
| `npm run build` | Compile TypeScript → `dist/` |
| `npm run start:prod` | Run compiled server (no hot-reload) |
| `npm run lint` | Lint with ESLint |
| `npm run format` | Format with Prettier |
| `npx prisma generate` | Regenerate Prisma client (after schema changes) |
| `npx prisma db push` | Sync schema to SQLite DB |
| `npx ts-node prisma/seed.ts` | Seed/re-seed devices (upsert, safe to repeat) |
| `npx prisma studio` | Open Prisma Studio (DB browser) |

## Testing Endpoints

```bash
# Ask a question (use API key from seed output)
curl -X POST http://localhost:3000/api/ask \
  -H "X-API-Key: chk_..." \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello CHARLI!"}'

# Voice pipeline (audio in → audio out)
curl -X POST http://localhost:3000/api/pipeline/voice \
  -H "X-API-Key: chk_..." \
  -F "audio=@test.wav" -o response.wav

# Transcribe audio
curl -X POST http://localhost:3000/api/transcribe \
  -H "X-API-Key: chk_..." \
  -F "audio=@test.wav"

# Text-to-speech
curl -X POST http://localhost:3000/api/tts \
  -H "X-API-Key: chk_..." \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from CHARLI"}'  -o response.wav
```

## Docker (Production)

For production, use Docker Compose — one command starts both services:

```bash
docker compose up       # Foreground
docker compose up -d    # Detached (background)
```

See [orchestration docs](../docs/charli_server/orchestration.md#docker-compose) for full Docker details.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_URL` | `http://localhost:18789` | OpenClaw gateway |
| `OPENCLAW_TOKEN` | — | Auth token from `~/.openclaw/openclaw.json` |
| `SIDECAR_URL` | `http://localhost:3001` | Python sidecar URL |
| `CHARLI_SERVER_PORT` | `3000` | NestJS listen port |
| `DATABASE_URL` | `file:./prisma/charli.db` | SQLite path (used by Prisma CLI + runtime) |
| `ADMIN_API_KEY` | — | Admin key for `POST /api/devices` |

## Project Structure

```
charli_server/
├── src/
│   ├── main.ts               Entry point + Swagger setup
│   ├── app.module.ts          Root module
│   ├── auth/                  API key guard + admin key
│   ├── device/                Device registry (CRUD)
│   ├── ask/                   LLM queries (text + vision)
│   │   └── prompts/           Per-device system prompts
│   ├── transcribe/            STT proxy → sidecar
│   ├── tts/                   TTS proxy → sidecar
│   ├── pipeline/              Voice orchestrator (transcribe → ask → tts)
│   ├── conversation/          Conversation history
│   ├── events/                Socket.IO WebSocket gateway
│   ├── health/                Health check (no auth)
│   ├── prisma/                PrismaService (driver adapter)
│   └── common/                Shared decorators (@CurrentDevice)
├── prisma/
│   ├── schema.prisma          DB models (no url — see prisma.config.ts)
│   ├── generated/             Auto-generated client (gitignored)
│   ├── seed.ts                Seed script
│   └── charli.db              SQLite database (gitignored)
├── sidecar/
│   ├── sidecar.py             FastAPI: /transcribe + /tts
│   └── requirements.txt
├── prisma.config.ts           Prisma 7 CLI config
├── docker-compose.yml         Production orchestration
├── Dockerfile                 NestJS container
└── .env.example               Environment template
```

## Further Reading

- [Architecture & Design](../docs/charli_server/architecture.md) — System design, Prisma 7 details, WebSocket design
- [API Reference](../docs/charli_server/api-reference.md) — Full endpoint documentation
- [Orchestration](../docs/charli_server/orchestration.md) — Dev, Docker, and PM2 setup
- [Device Migration](../docs/charli_server/device-migration.md) — Adding new devices
- [Future Improvements](../docs/charli_server/future-improvements.md) — Roadmap
