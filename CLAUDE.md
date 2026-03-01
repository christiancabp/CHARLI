# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CHARLI (C.H.A.R.L.I.) is a personal AI assistant ecosystem. The primary subproject is **charli-home** — a JARVIS-style voice assistant running on a Raspberry Pi 5 that connects to an OpenClaw gateway on a Mac Mini via Tailscale.

## Architecture

### Voice Pipeline (`raspberry_pi/charli-home/`)

The assistant uses a modular "building block" pattern — each `src/` module handles one step, and `charli_home.py` connects them in sequence:

```
Button press → record_audio() → transcribe() → ask_charli() → speak()
```

- **`charli_home.py`** — Main loop. Uses `gpiozero.Button` on GPIO pin 5 (Pirate Audio HAT Button A). Imports and orchestrates the building blocks.
- **`src/record.py`** — Records via `arecord` (hw:2,0, stereo). Converts to mono, normalizes, and boosts volume. Saves to `recordings/charli_recording.wav`.
- **`src/transcribe.py`** — Whisper `base` model, runs locally on Pi CPU with `fp16=False`. Returns `(text, language)`.
- **`src/ask_charli.py`** — Sends question to OpenClaw gateway (`openclaw:main` model) via OpenAI-compatible API. Uses `CHARLI_HOST` and `CHARLI_TOKEN` env vars. Includes a system prompt that enforces short, spoken-style responses.
- **`src/speak.py`** — Text-to-speech (espeak-ng initially, upgradeable to Piper TTS).

### Key Infrastructure

- **OpenClaw Gateway**: Runs on Mac Mini, exposed via Tailscale Serve on port 18789. The Pi is just ears/mouth — the brain lives on the Mac Mini.
- **Tailscale**: Private network connecting Pi (`charli-home`) and Mac Mini.
- **Hardware stack** (bottom to top): Pi 5 → Active Cooler → M.2 HAT+ (NVMe SSD) → GPIO Extender → Pirate Audio Dual Mic HAT.

## Development

### Running on the Pi

```bash
ssh charli@charli-home.local
cd ~/charli-home
source .venv/bin/activate
sudo -E python3 charli_home.py    # sudo for GPIO, -E to pass env vars
```

### Testing individual building blocks

Each `src/*.py` file has an `if __name__ == "__main__"` block for standalone testing:

```bash
python3 src/record.py        # test mic recording
python3 src/transcribe.py    # test speech-to-text
python3 src/ask_charli.py    # test gateway connection
```

### Environment Variables (set in Pi's `~/.bashrc`)

- `CHARLI_HOST` — OpenClaw gateway URL (Tailscale Serve HTTPS URL or direct IP:port)
- `CHARLI_TOKEN` — Auth token from `~/.openclaw/openclaw.json` on Mac Mini

## Conventions

- Python modules in `src/` follow a single-responsibility pattern — each does ONE thing and exposes a simple function
- The main app stays minimal; complexity lives inside building blocks
- Audio recordings are saved to `recordings/` directory (gitignored)
- The Pi targets Python 3 with a venv at `.venv/`
- Responses from CHARLI via Pi are constrained to 1-3 sentences, no markdown formatting, natural spoken style
- The project is a father-daughter learning project — code comments tend to be educational and explanatory
