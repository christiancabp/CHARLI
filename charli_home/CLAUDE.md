# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the CHARLI Desk Hub.

## What This Is

Raspberry Pi 5 thin client. Hardware I/O only — wake word, mic, speaker, touchscreen UI. Zero backend logic. All processing happens on the CHARLI Server (Mac Mini).

## Running

```bash
# On the Pi (via SSH)
ssh charli@charli-home.local
cd ~/charli-home

export CHARLI_SERVER_URL="http://charli-server:3000"
export CHARLI_API_KEY="chk_your_desk_hub_key"
export PICOVOICE_ACCESS_KEY="your_key"

python3 charli_home.py       # → Web UI at http://localhost:8080
```

No virtualenv needed on the Pi — deps are installed system-wide. On macOS for dev, use a venv.

## Architecture

**Four concurrent subsystems** via `asyncio.gather()`:

```
charli_home.py (async orchestrator)
├── Voice Pipeline     → wake word → record → POST /api/pipeline/voice → play audio
├── UI Server          → http.server serving JARVIS static files (:8080)
├── System Monitor     → CPU temp, RAM → broadcast via server WebSocket
└── Mac Link           → persistent WebSocket to Mac Mini for commands
```

**State machine:** `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

## Key Files

| File | Purpose |
|------|---------|
| `charli_home.py` | Main orchestrator, asyncio.gather() |
| `src/charli_server_client.py` | HTTP client → CHARLI Server |
| `src/state_manager.py` | Pipeline state tracking |
| `src/wake_word.py` | Porcupine wake word detection |
| `src/record.py` | USB mic recording via `arecord` |
| `src/system_monitor.py` | System metrics |
| `src/mac_link.py` | Pi↔Mac persistent WebSocket |
| `web/static/` | JARVIS UI (HTML/CSS/JS, no build step) |

## What Does NOT Live Here

No FastAPI, no REST API, no local transcription, no local LLM calls, no local TTS. All of that is on the CHARLI Server. This is a pure client.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CHARLI_SERVER_URL` | Central server URL (e.g., `http://charli-server:3000`) |
| `CHARLI_API_KEY` | API key for this device |
| `PICOVOICE_ACCESS_KEY` | Wake word detection license key |
| `CHARLI_MIC_DEVICE` | ALSA mic device (default: `hw:0,0`) |

## Hardware Notes

- **Mic:** USB microphone, recorded via `arecord` at 16kHz mono WAV
- **Speaker:** Bluetooth speaker via `aplay` (Linux) or `afplay` (macOS dev)
- **Display:** Chromium in kiosk mode pointing at `http://localhost:8080`
- **No GPIO or sudo needed**
