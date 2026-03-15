# CHARLI Server — Orchestration Guide

How to run the full CHARLI stack: server, sidecar, and devices.

## Quick Start (Development)

You need **3 terminals** on the Mac Mini and **1 on the Pi** (optional).

### Terminal 1: Python Sidecar (Mac Mini)

The ML worker must start first — it loads the Whisper model (~3s).

```bash
cd charli_server/sidecar
python3 -m venv .venv           # First time only
source .venv/bin/activate
pip install -r requirements.txt  # First time only

# Also install espeak-ng for TTS:
#   macOS: brew install espeak-ng
#   Linux: sudo apt install espeak-ng

python3 sidecar.py
# → CHARLI Sidecar starting on port 3001
# → Loading faster-whisper model (base, INT8)...
# → faster-whisper is ready!
```

Verify: `curl http://localhost:3001/health`

### Terminal 2: NestJS Server (Mac Mini)

```bash
cd charli_server
npm install                      # First time only
cp .env.example .env             # First time only — fill in OPENCLAW_TOKEN
npx prisma migrate dev           # First time only
npx prisma db seed               # First time only — prints API keys!

npm run start:dev
# → CHARLI Server running on http://localhost:3000
# → Swagger: http://localhost:3000/docs
```

Verify: `curl http://localhost:3000/health`

### Terminal 3: Pi Desk Hub (via SSH)

```bash
ssh charli@charli-home.local
cd ~/charli-home
source .venv/bin/activate

# Set env vars (add to ~/.bashrc for persistence)
export CHARLI_SERVER_URL="http://charli-server:3000"
export CHARLI_API_KEY="chk_your_desk_hub_key"

python3 charli_home.py
# → CHARLI Home v3.0 — Desk Hub (Thin Client)
# → Web UI: http://localhost:8080
```

### iOS App (Glasses)

Set in the app's UserDefaults (or hardcode for now):
- `charli_server_url` = `http://charli-server:3000`
- `charli_api_key` = `chk_your_glasses_key`

Build and run from Xcode.

---

## Startup Order

Order matters — each service depends on the one above it:

```
1. OpenClaw          (already running on Mac Mini:18789)
2. Python Sidecar    (Mac Mini:3001 — loads Whisper model)
3. NestJS Server     (Mac Mini:3000 — connects to sidecar + OpenClaw)
4. Devices           (Pi, iPhone — connect to NestJS server)
```

If the sidecar isn't running, STT and TTS endpoints will fail gracefully (return errors). The server itself stays up.

If OpenClaw isn't running, ask/pipeline endpoints will return a fallback error message. Health check still works.

---

## Production Setup (PM2)

For persistent operation on the Mac Mini, use PM2 to manage both processes.

### Install PM2

```bash
npm install -g pm2
```

### ecosystem.config.js

Create this in the repo root or `charli_server/`:

```js
module.exports = {
  apps: [
    {
      name: 'charli-sidecar',
      cwd: './charli_server/sidecar',
      script: 'sidecar.py',
      interpreter: '.venv/bin/python3',
      env: {
        CHARLI_WHISPER_MODEL: 'base',
        CHARLI_SIDECAR_PORT: '3001',
      },
      // Wait for model to load before starting NestJS
      wait_ready: true,
      listen_timeout: 15000,
    },
    {
      name: 'charli-server',
      cwd: './charli_server',
      script: 'dist/main.js',
      // Start after sidecar is ready
      wait_ready: true,
      env: {
        NODE_ENV: 'production',
        CHARLI_SERVER_PORT: '3000',
        OPENCLAW_URL: 'http://localhost:18789',
        SIDECAR_URL: 'http://localhost:3001',
        DATABASE_URL: 'file:./prisma/charli.db',
      },
    },
  ],
};
```

### Running with PM2

```bash
# Build NestJS first
cd charli_server && npm run build

# Start both processes
pm2 start ecosystem.config.js

# Monitor
pm2 status
pm2 logs

# Auto-start on boot
pm2 save
pm2 startup
```

### Alternative: systemd (Linux)

If the Mac Mini runs Linux, create two systemd services:

```ini
# /etc/systemd/system/charli-sidecar.service
[Unit]
Description=CHARLI Python Sidecar
After=network.target

[Service]
Type=simple
User=charli
WorkingDirectory=/home/charli/CHARLI/charli_server/sidecar
ExecStart=/home/charli/CHARLI/charli_server/sidecar/.venv/bin/python3 sidecar.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/charli-server.service
[Unit]
Description=CHARLI NestJS Server
After=charli-sidecar.service
Requires=charli-sidecar.service

[Service]
Type=simple
User=charli
WorkingDirectory=/home/charli/CHARLI/charli_server
ExecStart=/usr/bin/node dist/main.js
Restart=always
RestartSec=5
EnvironmentFile=/home/charli/CHARLI/charli_server/.env

[Install]
WantedBy=multi-user.target
```

---

## Tailscale Configuration

All devices communicate over Tailscale (private mesh VPN). The Mac Mini hostname is `charli-server` on the Tailscale network.

### Tailscale Serve (Optional)

Expose the server with HTTPS via Tailscale Serve:

```bash
# On Mac Mini
tailscale serve --bg 3000
# → https://charli-server.<tailnet>.ts.net → localhost:3000
```

Devices can then use `https://charli-server.<tailnet>.ts.net` instead of `http://charli-server:3000`.

---

## Health Monitoring

### Manual Checks

```bash
# Server health
curl http://charli-server:3000/health

# Sidecar health
curl http://localhost:3001/health

# List devices and their lastSeen timestamps
curl -H "X-API-Key: your-admin-key" http://charli-server:3000/api/devices
```

### Automated Health Check Script

```bash
#!/bin/bash
# save as check_charli.sh

echo "=== CHARLI Stack Health ==="

# Sidecar
if curl -sf http://localhost:3001/health > /dev/null 2>&1; then
  echo "✅ Sidecar (port 3001)"
else
  echo "❌ Sidecar (port 3001) — DOWN"
fi

# NestJS Server
if curl -sf http://localhost:3000/health > /dev/null 2>&1; then
  echo "✅ Server  (port 3000)"
else
  echo "❌ Server  (port 3000) — DOWN"
fi

# OpenClaw
if curl -sf http://localhost:18789/health > /dev/null 2>&1; then
  echo "✅ OpenClaw (port 18789)"
else
  echo "❌ OpenClaw (port 18789) — DOWN"
fi

# Pi (over Tailscale)
if curl -sf http://charli-home:8080/health > /dev/null 2>&1; then
  echo "✅ Pi Desk Hub (port 8080)"
else
  echo "⚠️ Pi Desk Hub — not reachable"
fi
```

---

## Troubleshooting

### "Cannot connect to CHARLI Server"

- Is the NestJS server running? Check `curl http://localhost:3000/health`
- Is the device on the Tailscale network? Check `tailscale status`
- Is the API key correct? Check with `curl -H "X-API-Key: chk_..." http://charli-server:3000/api/devices`

### "Transcription failed" or empty transcription

- Is the sidecar running? Check `curl http://localhost:3001/health`
- Is the audio file valid? Test directly: `curl -X POST http://localhost:3001/transcribe -F "audio=@test.wav"`
- Is the Whisper model loaded? Check sidecar terminal for "faster-whisper is ready!"

### "TTS failed"

- Is espeak-ng installed? Test: `espeak-ng "hello"`
- macOS: `brew install espeak-ng`
- Linux: `sudo apt install espeak-ng`

### "Error asking CHARLI" (LLM errors)

- Is OpenClaw running? Check `curl http://localhost:18789/health`
- Is the OPENCLAW_TOKEN correct? Check `~/.openclaw/openclaw.json` on Mac Mini
- Check the NestJS terminal for detailed error messages

### WebSocket not connecting

- Check the API key in the connection URL: `ws://server:3000/events?apiKey=chk_...`
- Check CORS — the server allows all origins by default
