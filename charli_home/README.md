# CHARLI Home — Desk Hub (Thin Client)

*A JARVIS-style voice assistant + desk hub with a 7" touchscreen — powered by the real CHARLI*

**Status:** In Progress
**Started:** 2026-02-21
**Team:** Christian Bermeo + Isabella Bermeo
**Hardware:** Raspberry Pi 5 8GB · M.2 HAT+ · 256GB NVMe SSD · Active Cooler · 7" Touchscreen · USB Microphone · Bluetooth Speaker

---

## What This Is

A desk hub that lives on your desk with a 7" touchscreen. Say "Hey Charli" and an animated orb lights up — CHARLI listens, thinks, and answers out loud with real-time visual feedback. The conversation scrolls on screen like a chat log.

The Pi is a **thin client** — it handles only hardware I/O (mic, speaker, screen). All backend processing (speech-to-text, LLM queries, text-to-speech, conversation history) happens on the central **CHARLI Server** running on the Mac Mini.

You can also monitor everything from your Mac terminal using the **TUI companion** — type `charli` and get a live dashboard over SSH showing state, transcript, and system metrics.

---

## Architecture (v3.0 — Thin Client)

```
                         ┌─────────────────┐
                         │  State Manager   │  local state tracking
                         │                  │  (state + metrics)
                         └────────┬────────┘
                    ┌─────────────┼──────────────┬──────────────┐
                    │             │              │              │
            ┌───────▼──────┐ ┌───▼────────┐ ┌───▼──────┐ ┌────▼─────────┐
            │ Wake Word    │ │ Voice      │ │ Static   │ │ System       │
            │ Listener     │ │ Pipeline   │ │ File     │ │ Monitor      │
            │ (Porcupine)  │ │ (server    │ │ Server   │ │ (psutil)     │
            │              │ │  client)   │ │ (http)   │ │              │
            └──────────────┘ └────────────┘ └──┬───┬──┘ └──────────────┘
                                               │   │
                                    ┌──────────▼┐  └──────────┐
                                    │ Chromium  │  │ Mac Link  │
                                    │ Kiosk     │  │ WebSocket │
                                    │ (7" LCD)  │  │ (↔ Mac)   │
                                    └───────────┘  └───────────┘
```

**Voice pipeline flow (v3.0):**
```
"Hey Charli" → Porcupine detects → USB mic records 5s
  → POST /api/pipeline/voice (audio sent to CHARLI Server)
  → Server: transcribe → ask LLM → synthesize speech
  → Server returns WAV audio → Pi plays through Bluetooth speaker
  → JARVIS UI gets real-time updates via Socket.IO from server
```

**State machine:** `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

State changes are broadcast by the CHARLI Server via Socket.IO. The JARVIS UI connects directly to the server's WebSocket gateway at `charli-server:3000/events`.

---

## What Lives Where

| Component | Location | Description |
|-----------|----------|-------------|
| Wake word detection | **Pi** (local) | Porcupine listens for "Hey Charli" on USB mic |
| Audio recording | **Pi** (local) | `arecord` captures from USB mic |
| Audio playback | **Pi** (local) | `aplay`/`afplay` plays through Bluetooth speaker |
| JARVIS web UI | **Pi** (static files) | Python `http.server` serves HTML/CSS/JS to Chromium kiosk |
| System monitoring | **Pi** (local) | `psutil` reads CPU temp, RAM, disk, Tailscale status |
| Speech-to-text | **Server** | faster-whisper via Python sidecar |
| LLM queries | **Server** | OpenClaw on Mac Mini |
| Text-to-speech | **Server** | espeak-ng/Piper via Python sidecar |
| Conversation history | **Server** | Prisma + SQLite |
| Real-time WebSocket | **Server** | Socket.IO gateway broadcasts state + messages |

---

## How It Connects Together

```
  ┌─────────────────────┐   Tailscale    ┌─────────────────────┐
  │    Raspberry Pi 5    │◄─────────────►│     Mac Mini         │
  │    (thin client)     │  private mesh  │                      │
  │                      │               │  CHARLI Server       │
  │  Ears:  USB mic      │  HTTP POST    │    (NestJS :3000)    │
  │  Mouth: BT speaker   │──────────────►│    ├─ Auth           │
  │  Eyes:  7" screen    │  ◄────────── │    ├─ Pipeline        │
  │                      │  WAV audio    │    ├─ WebSocket       │
  │  Web: localhost:8080 │               │    └─ Prisma DB       │
  │                      │               │                      │
  │  JARVIS UI connects  │  Socket.IO    │  Python Sidecar      │
  │  to server WebSocket │◄─────────────│    (FastAPI :3001)    │
  │                      │               │    ├─ Whisper STT     │
  └─────────────────────┘               │    └─ TTS             │
         ▲                               │                      │
         │ SSH + TUI                     │  OpenClaw Brain       │
  ┌──────┴──────────┐                   │    (LLM :18789)       │
  │    Your Mac      │── Tailscale ────►│                      │
  │  `charli` alias  │                  └─────────────────────┘
  └─────────────────┘
```

**What costs money?** Only the LLM query step — when the server sends text to OpenClaw. Everything else (wake word, recording, transcription, TTS, WebSocket, monitoring) is 100% local and free.

---

## Hardware Stack

```
┌─────────────────────────────────┐
│  7" Official Touchscreen (HDMI) │  800×480, capacitive touch
├─────────────────────────────────┤
│  USB Microphone                 │  plugged into Pi USB port
├─────────────────────────────────┤
│  M.2 HAT+ with NVMe SSD        │  256GB, connected via FFC cable
├─────────────────────────────────┤
│  Active Cooler (on CPU)         │  clips directly onto the SoC
├─────────────────────────────────┤
│  Raspberry Pi 5 (8GB)           │  the board itself
├─────────────────────────────────┤
│  Bluetooth Speaker              │  paired wirelessly
└─────────────────────────────────┘
```

**RAM budget (8GB total) — much lighter as thin client:**

| Component               | RAM      |
|--------------------------|----------|
| Linux + systemd          | ~300 MB  |
| Chromium kiosk (1 tab)   | ~250 MB  |
| Porcupine wake word      | ~15 MB   |
| Python + libs            | ~50 MB   |
| **Total**                | **~615 MB** |
| **Free**                 | **~7.4 GB** |

No more faster-whisper (~300MB) or FastAPI/uvicorn (~50MB) running locally.

---

## Project Structure

```
charli_home/
├── charli_home.py              # async orchestrator — runs all 4 subsystems
├── requirements.txt            # Python dependencies (much lighter now)
├── README.md                   # you are here
│
├── src/                        # building blocks (each does ONE thing)
│   ├── __init__.py
│   ├── state_manager.py        # local state enum (no WebSocket broadcast)
│   ├── charli_server_client.py # HTTP client for CHARLI Server API
│   ├── wake_word.py            # listens for "Hey Charli" (Porcupine)
│   ├── record.py               # records voice from USB mic (arecord)
│   ├── system_monitor.py       # CPU temp, RAM, Tailscale status
│   └── mac_link.py             # persistent WebSocket to Mac Mini
│
├── web/                        # JARVIS web UI served on the 7" touchscreen
│   └── static/
│       ├── index.html          # JARVIS UI page (orb + transcript)
│       ├── css/
│       │   └── charli.css      # dark JARVIS theme + CRT scanlines
│       └── js/
│           ├── charli.js       # Socket.IO client → connects to CHARLI Server
│           └── orb.js          # animated glowing orb (canvas)
│
├── tui/                        # terminal UI (SSH monitoring dashboard)
│   ├── __init__.py
│   └── charli_tui.py           # Textual TUI — cyberdeck aesthetic
│
├── models/                     # Porcupine .ppn wake word files
└── recordings/                 # temp WAV files (gitignored)
```

**Removed in v3.0** (now handled by CHARLI Server):
- ~~`src/transcribe.py`~~ — speech-to-text (server sidecar)
- ~~`src/ask_charli.py`~~ — LLM queries (server AskService)
- ~~`src/speak.py`~~ — text-to-speech (server sidecar)
- ~~`web/server.py`~~ — FastAPI web server (replaced by `http.server`)

---

## Step-by-Step Setup

> These are the exact commands to run, in order. Everything happens on the Pi unless noted otherwise.

### Prerequisites

Before setting up the Pi, make sure the **CHARLI Server** is running on the Mac Mini:
1. NestJS server at `http://charli-server:3000`
2. Python sidecar at `http://charli-server:3001`
3. Desk hub device registered and API key generated

See `docs/charli_server/orchestration.md` for server setup.

### Step 1 — SSH into the Pi

From your Mac terminal:
```bash
ssh charli@charli-home.local
```

### Step 2 — Install system packages

Only needed once:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv curl wget espeak-ng libportaudio2 ffmpeg
```

> Note: `espeak-ng` is still installed locally as a fallback for push-to-speak from Mac, but the main pipeline uses the server's TTS.

### Step 3 — Clone the repo

```bash
git clone https://github.com/christiancabp/CHARLI.git ~/CHARLI
ln -s ~/CHARLI/charli_home ~/charli-home
```

### Step 4 — Create the Python virtual environment

```bash
cd ~/charli-home
python3 -m venv .venv
source .venv/bin/activate
```

### Step 5 — Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Dependencies are much lighter now — no faster-whisper, no openai, no fastapi:

| Package | What it does |
|---------|--------------|
| `pvporcupine` | Wake word detection ("Hey Charli") |
| `pvrecorder` | Audio capture for Porcupine |
| `soundfile` | Read/write WAV audio files |
| `numpy` | Audio processing (normalize, boost) |
| `requests` | HTTP client for CHARLI Server API |
| `psutil` | System metrics (CPU, RAM, disk) |
| `websocket-client` | WebSocket client for Mac Link |

### Step 6 — Find your USB microphone device

```bash
arecord -l
```

### Step 7 — Set environment variables

Open `~/.bashrc`:
```bash
nano ~/.bashrc
```

Add these lines:
```bash
# ── CHARLI Home (Thin Client) ──────────────────────────
# CHARLI Server connection (Mac Mini via Tailscale)
export CHARLI_SERVER_URL="http://charli-server:3000"
export CHARLI_API_KEY="chk_your_desk_hub_key_here"   # From server seed output

# Picovoice wake word (get key at https://console.picovoice.ai)
export PICOVOICE_ACCESS_KEY="paste-your-key-here"

# USB mic (use the device string from Step 6)
export CHARLI_MIC_DEVICE="hw:0,0"
export CHARLI_MIC_CHANNELS="1"

# Optional: custom wake word model
# export CHARLI_KEYWORD_PATH="/home/charli/charli-home/models/hey-charli_en_raspberry-pi.ppn"
```

Save and apply:
```bash
source ~/.bashrc
```

> **Note:** The old `CHARLI_HOST` and `CHARLI_TOKEN` env vars are no longer needed. The Pi talks to the CHARLI Server, which talks to OpenClaw.

### Step 8 — Set up the wake word

Same as before — see the [Picovoice Console](https://console.picovoice.ai) to create a custom "Hey Charli" keyword, or use the built-in "Jarvis" fallback.

### Step 9 — Test the connection

```bash
cd ~/charli-home
source .venv/bin/activate
python3 src/charli_server_client.py
# Should print: "✅ Server is reachable!" and a response from CHARLI
```

Also test individual building blocks:
```bash
python3 src/record.py           # test USB mic
python3 src/wake_word.py        # test wake word
python3 src/system_monitor.py   # test system metrics
```

### Step 10 — Run the full system

```bash
python3 charli_home.py
```

You should see:
```
CHARLI Home v3.0 — Desk Hub (Thin Client)
Web UI: http://localhost:8080
Waiting for wake word... (Ctrl+C to quit)
```

Open Chromium on the Pi and go to `http://localhost:8080`. The JARVIS UI connects to the CHARLI Server's WebSocket gateway for real-time updates.

### Step 11 — Set up autostart

Once everything works, make it start on boot. Create a systemd service:

```bash
sudo nano /etc/systemd/system/charli-home.service
```

```ini
[Unit]
Description=CHARLI Home Desk Hub (Thin Client)
After=network-online.target sound.target
Wants=network-online.target

[Service]
Type=simple
User=charli
WorkingDirectory=/home/charli/charli-home
EnvironmentFile=/home/charli/charli-home/.env
ExecStart=/home/charli/charli-home/.venv/bin/python3 charli_home.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable charli-home
sudo systemctl start charli-home
```

For Chromium kiosk autostart and screen settings, see the detailed instructions in `docs/raspberry_pi/README.md`.

---

## TUI Companion

The TUI is a terminal monitoring dashboard. Run it on your Mac and it connects over the network to show live state, conversation transcript, and system metrics.

```bash
# From your Mac
charli    # if you have the alias set up
# or:
python3 tui/charli_tui.py --host charli-home.local
```

---

## JARVIS Web UI

The 7" touchscreen runs Chromium in kiosk mode pointing at `http://localhost:8080`.

The UI connects to the CHARLI Server via Socket.IO (`charli-server:3000/events`) for real-time state and message updates. Static HTML/CSS/JS files are served locally by Python's built-in `http.server` — no FastAPI dependency needed.

**Orb states:**

| State | Color | Behavior |
|-------|-------|----------|
| IDLE | Blue (#0088cc) | Slow pulse, gentle wobble |
| LISTENING | Cyan (#00d4ff) | Faster wobble, more particles |
| THINKING | Orange (#ff8c00) | Rapid deformation, energetic |
| SPEAKING | Gold (#ffc845) | Smooth pulse, warm glow |

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| "Cannot connect to CHARLI Server" | Is the server running? `curl http://charli-server:3000/health`. Is Tailscale connected? `tailscale status` |
| Wake word not detecting | Verify: `echo $PICOVOICE_ACCESS_KEY`. Try "jarvis" fallback. |
| No sound from speaker | Re-pair Bluetooth. Test: `espeak-ng "test"` |
| JARVIS UI blank/disconnected | Check Socket.IO connection in browser console. Is `CHARLI_SERVER_URL` set correctly in `charli.js`? |
| `CHARLI_API_KEY: unbound variable` | Run `source ~/.bashrc`. Verify: `echo $CHARLI_API_KEY` |
| `ModuleNotFoundError` | Activate venv: `source ~/charli-home/.venv/bin/activate` |

---

## Roadmap

### Done
- [x] Wake word detection ("Hey Charli")
- [x] Voice pipeline via central server
- [x] JARVIS animated orb UI with live transcript
- [x] System monitoring (CPU, RAM, Tailscale)
- [x] Thin client architecture (v3.0)
- [x] Conversation history on server (Prisma/SQLite)

### Next
- [ ] Piper TTS upgrade (natural voice — server-side)
- [ ] Voice Activity Detection (stop recording on silence)
- [ ] Pi camera for vision queries ("what's on my desk?")
- [ ] Cyberdeck full dashboard UI (stats + log + orb)
- [ ] Touch-swipeable pages
- [ ] Home automation (smart lights, MQTT)

---

*Built with love by Christian and Isabella Bermeo, 2026*
