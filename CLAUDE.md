# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CHARLI (C.H.A.R.L.I.) is a personal AI assistant ecosystem. The primary subproject is **charli-home** — a JARVIS-style desk hub voice assistant running on a Raspberry Pi 5 with a 7" touchscreen, USB mic, and Bluetooth speaker. It connects to an OpenClaw gateway on a Mac Mini via Tailscale.

## Architecture

### Desk Hub (`raspberry_pi/charli-home/`)

Three concurrent subsystems sharing a state manager:

1. **Wake Word Listener** — Porcupine detects "Hey Charli" via USB mic
2. **Voice Pipeline** — record → transcribe → ask → speak (the original building blocks)
3. **Web Server** — FastAPI serves a JARVIS UI on the 7" touchscreen via Chromium kiosk

```
Wake word detected → record_audio() → transcribe() → ask_charli() → speak()
                     [state broadcasts to UI via WebSocket at each step]
```

**State machine:** `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

### Key Files

- **`charli_home.py`** — Async orchestrator. Runs FastAPI (uvicorn) + voice pipeline concurrently with `asyncio.gather()`. No GPIO, no sudo needed.
- **`src/state_manager.py`** — Central state enum + WebSocket broadcast. Holds conversation history. Thread-safe `set_state_sync()` for voice pipeline thread.
- **`src/wake_word.py`** — Porcupine wake word detection using `pvrecorder`. Blocks until "Hey Charli" detected.
- **`src/record.py`** — Records via `arecord` with configurable device (`CHARLI_MIC_DEVICE` env var, default `plughw:1,0`). Mono USB mic. Normalizes + boosts volume.
- **`src/transcribe.py`** — Whisper `base` model, runs locally on Pi CPU. Returns `(text, language)`.
- **`src/ask_charli.py`** — Sends question to OpenClaw gateway (`openclaw:main` model) via OpenAI-compatible API. Uses `CHARLI_HOST` and `CHARLI_TOKEN` env vars.
- **`src/speak.py`** — Text-to-speech via espeak-ng (upgradeable to Piper TTS).
- **`web/server.py`** — FastAPI app serving static JARVIS UI + WebSocket endpoint at `/ws`.
- **`web/static/`** — JARVIS touchscreen UI (HTML/CSS/JS). Animated orb, conversation transcript, WebSocket client.

### Key Infrastructure

- **OpenClaw Gateway**: Runs on Mac Mini, exposed via Tailscale Serve on port 18789. The Pi is just ears/mouth/display — the brain lives on the Mac Mini.
- **Tailscale**: Private network connecting Pi (`charli-home`) and Mac Mini.
- **Hardware stack**: Pi 5 → Active Cooler → M.2 HAT+ (NVMe SSD) → 7" Touchscreen (HDMI) → USB Mic → Bluetooth Speaker.

## Development

### Running on the Pi

```bash
ssh charli@charli-home.local
cd ~/charli-home
source .venv/bin/activate
python3 charli_home.py    # no sudo needed (no GPIO)
```

Web UI available at `http://localhost:8080`

### Testing individual building blocks

Each `src/*.py` file has an `if __name__ == "__main__"` block for standalone testing:

```bash
python3 src/record.py        # test USB mic recording
python3 src/transcribe.py    # test speech-to-text
python3 src/ask_charli.py    # test gateway connection
python3 src/wake_word.py     # test wake word detection
```

### Environment Variables (set in Pi's `~/.bashrc` or `.env` file)

- `CHARLI_HOST` — OpenClaw gateway URL (Tailscale Serve HTTPS URL or direct IP:port)
- `CHARLI_TOKEN` — Auth token from `~/.openclaw/openclaw.json` on Mac Mini
- `PICOVOICE_ACCESS_KEY` — Picovoice Console access key for wake word
- `CHARLI_MIC_DEVICE` — ALSA device string (default: `plughw:1,0`)
- `CHARLI_MIC_CHANNELS` — Number of mic channels (default: `1`)
- `CHARLI_KEYWORD_PATH` — Path to custom `.ppn` wake word model
- `CHARLI_AUDIO_DEVICE_INDEX` — Audio device index for Porcupine (default: `-1`)

## Conventions

- Python modules in `src/` follow a single-responsibility pattern — each does ONE thing and exposes a simple function
- The main app stays minimal; complexity lives inside building blocks
- Audio recordings are saved to `recordings/` directory (gitignored)
- The Pi targets Python 3 with a venv at `.venv/`
- Responses from CHARLI via Pi are constrained to 1-3 sentences, no markdown formatting, natural spoken style
- The project is a father-daughter learning project — code comments tend to be educational and explanatory
- The JARVIS UI is vanilla HTML/CSS/JS (no build step) served by FastAPI as static files
