# CHARLI CLI

Terminal client for talking to CHARLI from any machine on the Tailscale network.

## What Is It?

The CLI is a **thin client** — like the Pi desk hub and iOS glasses, it sends requests to the CHARLI Server and displays the response. The difference is that it uses text instead of voice, so CHARLI responds with longer, markdown-formatted answers.

```
┌──────────────┐        ┌──────────────────────┐
│  charli ask  │───────►│  CHARLI Server       │
│  "question"  │        │  POST /api/ask       │
│              │◄───────│  → OpenClaw → answer │
│  Display     │        │  (conversation saved)│
└──────────────┘        └──────────────────────┘
```

## Quick Start

```bash
cd charli_cli
npm install && npm run build

node bin/charli.js init                   # Setup wizard
node bin/charli.js status                 # Check connection
node bin/charli.js ask "Hello CHARLI!"    # Talk to CHARLI
```

See [Setup Guide](setup.md) for detailed configuration and [Usage Guide](usage.md) for all commands.

## How It Differs from Voice Devices

| Feature | Voice devices (desk hub, glasses) | CLI |
|---------|----------------------------------|-----|
| Input | Audio (wake word → mic recording) | Text (typed in terminal) |
| Output | Spoken audio (WAV) | Printed text (markdown) |
| Response style | 1-3 sentences, no markdown | Detailed, with code blocks |
| Max tokens | 150 | 1024 |
| Conversation history | 3 turns | 10 turns |
| Server endpoint | `POST /api/pipeline/voice` | `POST /api/ask` |
| Sidecar needed? | Yes (STT + TTS) | No (text only) |

## Architecture

The CLI follows the same thin-client pattern as all CHARLI devices:

1. **No backend logic** — all processing happens on the CHARLI Server
2. **API key auth** — same `X-API-Key` header as other devices
3. **Conversation tracking** — server maintains history per device, enabling follow-up questions
4. **Device-specific prompt** — the `cli` device type uses a system prompt that allows markdown and longer responses

## Dependencies

Minimal — 3 runtime deps, zero heavy packages:

| Package | Purpose |
|---------|---------|
| `commander` | CLI argument parsing and command routing |
| `chalk` | Terminal colors and formatting |
| `ora` | Spinner animation while waiting for responses |

API calls use Node 18+ native `fetch` — no axios or node-fetch needed.

## Further Reading

- [Setup Guide](setup.md) — Installation, `charli init`, Tailscale, config file
- [Usage Guide](usage.md) — All commands, examples, tips
- [Server API Reference](../charli_server/api-reference.md) — Full endpoint docs
- [Server Architecture](../charli_server/architecture.md) — How the server processes requests
