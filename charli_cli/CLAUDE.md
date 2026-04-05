# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the CHARLI CLI.

## What This Is

Terminal client for talking to CHARLI from any machine on the Tailscale network. Pure Node.js/TypeScript — no framework, uses native `fetch`, Commander.js for CLI parsing.

## Development

```bash
npm install
npm run build          # tsc → dist/
npm run dev            # tsc --watch

node bin/charli.js init          # Setup wizard (server URL, API key)
node bin/charli.js status        # Health + config check
node bin/charli.js ask "Hello!"  # Text chat
```

Requires a running CHARLI Server. Config stored at `~/.charli/config.json`.

## Architecture

```
bin/charli.js             → Entry point (#!/usr/bin/env node)
src/cli.ts                → Commander program, routes to commands
src/commands/
  ├── init.ts             → Setup wizard (Tailscale detection, save config)
  ├── ask.ts              → POST /api/ask, render markdown response
  └── status.ts           → GET /health + config display
src/lib/
  ├── api-client.ts       → HTTP wrapper (fetch → CHARLI Server)
  ├── config.ts           → ~/.charli/config.json load/save
  ├── tailscale.ts        → Auto-detect Tailscale, suggest server URL
  └── output.ts           → Chalk-based terminal formatting
src/types.ts              → Shared TypeScript interfaces
```

## Key Patterns

- **ESM project** (`"type": "module"` in package.json) — imports use `.js` extensions
- **TypeScript target:** ES2022, Node16 module resolution
- **Config cascade:** `~/.charli/config.json` → overridden by `CHARLI_SERVER_URL` / `CHARLI_API_KEY` env vars
- **No runtime deps** besides chalk (formatting), commander (CLI), ora (spinners)
- **Device type `cli`** — gets markdown responses, code blocks, 1024 max tokens, 10-turn history

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CHARLI_SERVER_URL` | Override server URL from config |
| `CHARLI_API_KEY` | Override API key from config |
