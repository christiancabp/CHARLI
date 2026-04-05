# CHARLI CLI — Setup Guide

## Prerequisites

- **Node.js 18+** (for native `fetch`)
- **CHARLI Server** running and reachable (see [orchestration guide](../charli_server/orchestration.md))
- **Tailscale** (optional but recommended — for automatic server discovery)

## Installation

```bash
cd charli_cli
npm install
npm run build
```

To make `charli` available globally:

```bash
sudo npm link
# Now you can run `charli` from anywhere
```

Or just use `node bin/charli.js` directly.

## Setup Wizard

The fastest way to configure the CLI:

```bash
charli init
# or: node bin/charli.js init
```

The wizard:

1. **Checks Tailscale** — if connected, lists your Tailscale hostname and peers
2. **Finds the server** — looks for peers named `charli-server`, `mac-mini`, etc., and auto-suggests the URL
3. **Validates the server** — hits `GET /health` to confirm it's reachable
4. **Gets your API key** — paste an existing key, or register a new device (needs the admin key)
5. **Saves config** — writes to `~/.charli/config.json`

### Example Init Session

```
CHARLI Setup

✔ Tailscale: connected as macbook-pro
✔ Found CHARLI server: charli-server (100.64.0.1)
Server URL (http://charli-server:3000):
✔ Server is reachable

You need an API key for your CLI device.
Option 1: Paste an existing key (from seed output or admin)
Option 2: Register a new device (requires admin key)

Paste API key, or type "new" to register: chk_abc123...
Device name (for display) (charli-cli):

✔ Config saved to /Users/you/.charli/config.json
Try: charli status or charli ask "Hello!"
```

## Config File

Location: `~/.charli/config.json`

```json
{
  "serverUrl": "http://charli-server:3000",
  "apiKey": "chk_abc123...",
  "deviceName": "charli-cli"
}
```

| Field | Description |
|-------|-------------|
| `serverUrl` | Full URL to the CHARLI Server (include port) |
| `apiKey` | Device API key (from seed output or `charli init`) |
| `deviceName` | Display name (used in status output) |

### Environment Variable Overrides

Env vars take precedence over the config file — useful for temporary overrides or CI:

| Env Var | Overrides |
|---------|-----------|
| `CHARLI_SERVER_URL` | `serverUrl` |
| `CHARLI_API_KEY` | `apiKey` |

```bash
# Temporarily point to a different server
CHARLI_SERVER_URL=http://localhost:3000 charli ask "Hello"
```

## Getting an API Key

Three ways to get an API key for the CLI:

### Option 1: From the Seed Script (Easiest)

The seed script creates a `charli-cli` device automatically:

```bash
cd charli_server
npx tsx prisma/seed.ts
# Output:
#   CLI:      charli-cli (key: chk_abc123...)
```

### Option 2: Register via `charli init`

During `charli init`, type `new` when asked for the API key. You'll need the admin key (`ADMIN_API_KEY` from the server's `.env`).

### Option 3: Register via the API

```bash
curl -X POST http://charli-server:3000/api/devices \
  -H "X-API-Key: your-admin-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-laptop-cli", "type": "cli"}'
```

The response includes the API key — save it, it's only shown once.

## Tailscale Integration

The CLI uses Tailscale for automatic server discovery. During `charli init`:

1. Runs `tailscale status --json` to check connection
2. If connected, shows your Tailscale hostname and IP
3. Scans peers for known server hostnames (`charli-server`, `mac-mini`, `macmini`)
4. If found, suggests the URL automatically (e.g., `http://charli-server:3000`)

If Tailscale isn't installed or isn't running, the wizard just asks you to type the URL manually. Everything still works — Tailscale is a convenience, not a requirement.

## Troubleshooting

### "Not configured. Run charli init first."

No config file found and no env vars set. Run `charli init` or create `~/.charli/config.json` manually.

### "Invalid API key — run charli init to reconfigure"

The server returned 401. Your API key is wrong or the device was deleted. Re-run `charli init` with a valid key.

### "Server: unreachable"

The CLI can't reach the server. Check:
- Is the server running? `curl http://charli-server:3000/health`
- Are you on the Tailscale network? `tailscale status`
- Is the URL correct in your config? `cat ~/.charli/config.json`
