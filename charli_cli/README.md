# CHARLI CLI

Talk to CHARLI from any terminal on the Tailscale network.

## Quick Start

```bash
npm install
npm run build

node bin/charli.js init                   # Setup wizard
node bin/charli.js status                 # Check connection
node bin/charli.js ask "Hello CHARLI!"    # Talk to CHARLI
```

## Commands

| Command | Description |
|---------|-------------|
| `charli init` | Setup wizard (server URL, API key, Tailscale detection) |
| `charli status` | Show config, Tailscale status, server health |
| `charli ask "question"` | Ask CHARLI a question (text chat) |

## Project Structure

```
charli_cli/
├── bin/charli.js           Entry point (#!/usr/bin/env node)
├── src/
│   ├── cli.ts              Commander program + command routing
│   ├── types.ts            Shared interfaces
│   ├── commands/
│   │   ├── ask.ts          charli ask "question"
│   │   ├── status.ts       charli status
│   │   └── init.ts         charli init (setup wizard)
│   └── lib/
│       ├── api-client.ts   HTTP client (native fetch + X-API-Key)
│       ├── config.ts       Load/save ~/.charli/config.json
│       ├── tailscale.ts    Tailscale detection
│       └── output.ts       Chalk formatting helpers
├── package.json            ES modules, 3 runtime deps
└── tsconfig.json
```

## Documentation

Full docs live in [`docs/charli_cli/`](../docs/charli_cli/):

- [Overview](../docs/charli_cli/README.md) — Architecture, how it differs from voice devices
- [Setup Guide](../docs/charli_cli/setup.md) — Installation, `charli init`, Tailscale, config file, troubleshooting
- [Usage Guide](../docs/charli_cli/usage.md) — All commands, examples, tips, roadmap
