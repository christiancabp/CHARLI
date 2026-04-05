# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the CHARLI Server.

## What This Is

Central NestJS backend + Python ML sidecar. All CHARLI devices (desk hub, glasses, CLI) talk to this server. It handles auth, LLM queries, STT, TTS, conversation history, and WebSocket events.

## Development

```bash
npm install
cp .env.example .env         # Fill in OPENCLAW_TOKEN from ~/.openclaw/openclaw.json

npx prisma generate          # Generate client → prisma/generated/
npx prisma db push           # Create/sync SQLite DB
npx tsx prisma/seed.ts       # Seed devices (prints API keys — save them!)

npm run start:dev            # Hot-reload → http://localhost:3000
                             # Swagger UI → http://localhost:3000/docs
```

The Python sidecar must be running for STT/TTS to work:
```bash
cd sidecar && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 sidecar.py           # → http://localhost:3001
```

### Docker Compose (server + sidecar together)

```bash
npx prisma generate          # MUST run locally first (see Prisma gotcha below)
docker compose up --build    # Build + start both
docker compose up -d         # Detached
docker compose down -v       # Stop + delete DB volume
```

### Common Commands

| Command | Purpose |
|---------|---------|
| `npm run start:dev` | Dev server with hot-reload |
| `npm run build` | Compile → `dist/src/` (note: not `dist/`) |
| `npm run start:prod` | Run compiled server |
| `npx prisma generate` | Regenerate client after schema changes |
| `npx prisma db push` | Sync schema to SQLite |
| `npx tsx prisma/seed.ts` | Seed/re-seed devices (upsert, safe to repeat) |
| `npx prisma studio` | DB browser GUI |

## Architecture

```
NestJS (:3000)                          Python Sidecar (:3001)
├── auth/         API key guard         ├── POST /transcribe (faster-whisper)
├── device/       Device CRUD           └── POST /tts (espeak-ng/Piper)
├── ask/          LLM via OpenClaw
├── transcribe/   STT proxy → sidecar
├── tts/          TTS proxy → sidecar        OpenClaw (:18789)
├── pipeline/     voice orchestrator ────→   LLM Gateway
├── conversation/ history per device
├── events/       Socket.IO gateway
├── health/       no auth
└── prisma/       DB service (driver adapter)
```

**Request flow (voice):** Device → `POST /api/pipeline/voice` → AuthGuard → TranscribeService (→ sidecar) → AskService (→ OpenClaw) → TtsService (→ sidecar) → WAV response

**Request flow (text):** Device → `POST /api/ask` → AuthGuard → AskService (→ OpenClaw) → JSON response

## Prisma 7 — Key Details

- **No Rust engine.** Uses `@prisma/adapter-better-sqlite3` driver adapter.
- **Two config locations:** `prisma.config.ts` for CLI (`db push`, `migrate`), `src/prisma/prisma.service.ts` for runtime. Both read `DATABASE_URL`.
- **Import pattern:** `from '@prisma/generated'` — a tsconfig path alias pointing to `prisma/generated/prisma/client/client`.
- **Platform gotcha:** `npx prisma generate` produces different output per platform. macOS → CJS-compatible `.ts`. Docker Node 22 Alpine → ESM with `import.meta.url` that breaks the CJS build. Docker copies the locally-generated client; always run `npx prisma generate` locally before `docker compose build`.

## Build Output

TypeScript compiles to `dist/src/` (not `dist/`). This is because `tsconfig.json` includes both `src/` and `prisma/` paths, widening `rootDir` to the project root. The entry point is `dist/src/main.js`.

## Docker Networking

- Sidecar: `http://sidecar:3001` (Docker DNS between containers)
- OpenClaw: `http://host.docker.internal:18789` (host machine, not inside Docker)
- Both overridden in `docker-compose.yml` environment block

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `OPENCLAW_URL` | `http://localhost:18789` | Use `host.docker.internal` in Docker |
| `OPENCLAW_TOKEN` | — | From `~/.openclaw/openclaw.json` → `gateway.auth.token` |
| `SIDECAR_URL` | `http://localhost:3001` | Use `http://sidecar:3001` in Docker |
| `DATABASE_URL` | `file:./prisma/charli.db` | Relative to project root |
| `ADMIN_API_KEY` | `dev-admin-key` | For `POST /api/devices` |
| `CHARLI_SERVER_PORT` | `3000` | NestJS listen port |

## Device Types

| Type | Response Style | Max Tokens | History Turns |
|------|---------------|------------|---------------|
| `desk-hub` | Voice, 1-3 sentences, no markdown | 150 | 3 |
| `smart-glasses` | Voice, concise, no markdown | 150 | 3 |
| `cli` | Text, markdown, code blocks | 1024 | 10 |

## Peer Dep Warning

`@nestjs/swagger@11` expects `@nestjs/common@^11` but the project uses v10. Use `--legacy-peer-deps` for `npm install` and Docker builds.
