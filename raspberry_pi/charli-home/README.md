# CHARLI Home — Desk Hub

*A JARVIS-style voice assistant + desk hub with a 7" touchscreen — powered by the real CHARLI*

**Status:** In Progress
**Started:** 2026-02-21
**Team:** Christian Bermeo + Isabella Bermeo
**Hardware:** Raspberry Pi 5 8GB · M.2 HAT+ · 256GB NVMe SSD · Active Cooler · 7" Touchscreen · USB Microphone · Bluetooth Speaker

---

## What This Is

A desk hub that lives on your desk with a 7" touchscreen. Say "Hey Charli" and an animated orb lights up — CHARLI listens, thinks, and answers out loud with real-time visual feedback. The conversation scrolls on screen like a chat log.

The Pi is just the **ears, mouth, and display**. The brain lives on the Mac Mini via OpenClaw + Tailscale.

You can also monitor everything from your Mac terminal using the **TUI companion** — type `charli` and get a live dashboard over SSH showing state, transcript, and system metrics.

---

## Architecture

Five concurrent subsystems sharing a state manager:

```
                         ┌─────────────────┐
                         │  State Manager   │  single source of truth
                         │                  │  (state + conversation + metrics)
                         └────────┬────────┘
                    ┌─────────────┼──────────────┬──────────────┐
                    │             │              │              │
            ┌───────▼──────┐ ┌───▼────────┐ ┌───▼──────┐ ┌────▼─────────┐
            │ Wake Word    │ │ Voice      │ │ FastAPI  │ │ System       │
            │ Listener     │ │ Pipeline   │ │ Web      │ │ Monitor      │
            │ (Porcupine)  │ │ (building  │ │ Server   │ │ (psutil)     │
            │              │ │  blocks)   │ │          │ │              │
            └──────────────┘ └────────────┘ └──┬───┬──┘ └──────────────┘
                                               │   │
                                    ┌──────────▼┐  └──────────┐
                                    │ Chromium  │  │ Mac Link  │
                                    │ Kiosk     │  │ WebSocket │
                                    │ (7" LCD)  │  │ (↔ Mac)   │
                                    └───────────┘  └───────────┘
```

**Voice pipeline flow:**
```
"Hey Charli" → Porcupine detects → USB mic records 5s
  → faster-whisper (speech→text, local, free)
  → OpenClaw on Mac Mini (LLM response, costs tokens)
  → espeak-ng speaks answer → 7" screen shows orb + transcript
```

**State machine:** `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

Each state change broadcasts via WebSocket to all connected clients (touchscreen browser, TUI, Mac).

---

## How It Connects Together

```
  ┌─────────────────────┐   Tailscale    ┌─────────────────────┐
  │    Raspberry Pi 5    │◄─────────────►│     Mac Mini         │
  │                      │  private mesh  │                      │
  │  Ears:  USB mic      │               │  Brain: OpenClaw     │
  │  Mouth: BT speaker   │  HTTP POST    │    └─ LLM (tokens)   │
  │  Eyes:  7" screen    │──────────────►│                      │
  │  Nerve: faster-whisper│  ◄────────── │  REST response       │
  │                      │               │                      │
  │  Web: localhost:8080 │               │                      │
  │  TUI:  SSH terminal  │               │                      │
  └─────────────────────┘               └─────────────────────┘
         ▲                                         ▲
         │ SSH + TUI                               │
  ┌──────┴──────────┐                              │
  │    Your Mac      │────── Tailscale ────────────┘
  │  `charli` alias  │
  │  (TUI companion) │
  └─────────────────┘
```

**What costs money?** Only the `ask_charli()` step — when the Pi sends text to the LLM via OpenClaw. Everything else (wake word, recording, transcription, TTS, WebSocket, system monitoring) is 100% local and free.

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

**RAM budget (8GB total):**

| Component               | RAM      |
|--------------------------|----------|
| Linux + systemd          | ~300 MB  |
| Chromium kiosk (1 tab)   | ~250 MB  |
| faster-whisper (base, INT8) | ~300 MB |
| FastAPI + uvicorn        | ~50 MB   |
| Porcupine                | ~15 MB   |
| Python + libs            | ~80 MB   |
| **Total**                | **~1 GB**|
| **Free**                 | **~7 GB**|

---

## Project Structure

```
charli-home/
├── charli_home.py              # async orchestrator — runs everything
├── requirements.txt            # Python dependencies
├── README.md                   # you are here
│
├── src/                        # building blocks (each does ONE thing)
│   ├── __init__.py
│   ├── state_manager.py        # state enum + WebSocket broadcast
│   ├── wake_word.py            # listens for "Hey Charli" (Porcupine)
│   ├── record.py               # records voice from USB mic (arecord)
│   ├── transcribe.py           # speech → text (faster-whisper, local)
│   ├── ask_charli.py           # sends question to Mac Mini (OpenClaw)
│   ├── speak.py                # text → speech (espeak-ng)
│   ├── system_monitor.py       # CPU temp, RAM, Tailscale status
│   └── mac_link.py             # persistent WebSocket to Mac Mini
│
├── web/                        # web UI served on the 7" touchscreen
│   ├── __init__.py
│   ├── server.py               # FastAPI + WebSocket + REST API
│   └── static/
│       ├── index.html          # JARVIS UI page (orb + transcript)
│       ├── css/
│       │   └── charli.css      # dark JARVIS theme + CRT scanlines
│       └── js/
│           ├── charli.js       # WebSocket client + UI state logic
│           └── orb.js          # animated glowing orb (canvas)
│
├── tui/                        # terminal UI (SSH monitoring dashboard)
│   ├── __init__.py
│   └── charli_tui.py           # Textual TUI — cyberdeck aesthetic
│
├── models/                     # Porcupine .ppn wake word files
└── recordings/                 # temp WAV files (gitignored)
```

---

## Step-by-Step Setup

> These are the exact commands to run, in order. Everything happens on the Pi unless noted otherwise.

### Step 1 — SSH into the Pi

From your Mac terminal:
```bash
ssh charli@charli-home.local
```

If `charli-home.local` doesn't resolve, use the IP address:
```bash
ssh charli@192.168.x.x
```

### Step 2 — Install system packages

These are OS-level tools. Only needed once:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv curl wget espeak-ng libportaudio2 ffmpeg
```

### Step 3 — Clone the repo

```bash
# Clone the full CHARLI repo
git clone https://github.com/christiancabp/CHARLI.git ~/CHARLI

# Create a shortcut (symlink) so ~/charli-home points to the project folder
ln -s ~/CHARLI/raspberry_pi/charli-home ~/charli-home
```

Verify:
```bash
ls ~/charli-home/charli_home.py
# Should print: /home/charli/charli-home/charli_home.py
```

> **Why a symlink?** The code lives inside the repo at `raspberry_pi/charli-home/`, but scripts expect `~/charli-home`. The symlink bridges them — `git pull` in `~/CHARLI` updates the code and `~/charli-home` still works.

### Step 4 — Create the Python virtual environment

```bash
cd ~/charli-home
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your prompt. This means you're in the virtual environment.

> **What's a venv?** It's like an isolated `node_modules` for Python. Packages you install here don't affect the rest of the system. Every time you open a new terminal, run `source .venv/bin/activate` to enter it.

### Step 5 — Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs:

| Package | What it does |
|---------|--------------|
| `faster-whisper` | Speech-to-text AI (runs locally, 4x faster than openai-whisper) |
| `openai` | API client for talking to OpenClaw on Mac Mini |
| `fastapi` | Web framework (like Express.js for Python) |
| `uvicorn` | HTTP server that runs FastAPI |
| `websockets` | WebSocket support |
| `pvporcupine` | Wake word detection engine ("Hey Charli") |
| `pvrecorder` | Audio capture for Porcupine |
| `soundfile` | Read/write WAV audio files |
| `numpy` | Math toolkit for audio processing |
| `psutil` | System metrics (CPU, RAM, disk) |
| `textual` | Terminal UI framework (for the TUI companion) |
| `websocket-client` | WebSocket client (for Mac Link) |

> **First-time note:** faster-whisper downloads a ~150MB model on first run. This is normal and only happens once.

### Step 6 — Find your USB microphone device

```bash
arecord -l
```

Look for your USB mic. Example output:
```
card 0: Microphone [USB Microphone], device 0: USB Audio [USB Audio]
```

The device string for `card 0, device 0` is `hw:0,0`.

> **Tip:** If you see `card 1`, the device string is `hw:1,0`. The first number is the card, the second is the device.

### Step 7 — Set environment variables

Open `~/.bashrc`:
```bash
nano ~/.bashrc
```

Add these lines at the bottom (replace placeholders with your real values):
```bash
# ── CHARLI Home ──────────────────────────────────────
# Gateway connection (get token from Mac Mini: cat ~/.openclaw/openclaw.json)
export CHARLI_HOST="https://your-mac-mini.tail1234.ts.net"
export CHARLI_TOKEN="paste-your-token-here"

# Picovoice wake word (get key at https://console.picovoice.ai)
export PICOVOICE_ACCESS_KEY="paste-your-key-here"

# USB mic (use the device string from Step 6)
export CHARLI_MIC_DEVICE="hw:0,0"
export CHARLI_MIC_CHANNELS="1"
```

Save and exit: **Ctrl+X → Y → Enter**

Apply the changes:
```bash
source ~/.bashrc
```

**Where to get each value:**

| Variable | How to get it |
|----------|---------------|
| `CHARLI_HOST` | On Mac Mini: `tailscale status` shows the hostname. Or set up Tailscale Serve: `tailscale serve --bg 18789` |
| `CHARLI_TOKEN` | On Mac Mini: `cat ~/.openclaw/openclaw.json` and copy the token value |
| `PICOVOICE_ACCESS_KEY` | Sign up at https://console.picovoice.ai → copy your Access Key |
| `CHARLI_MIC_DEVICE` | From `arecord -l` output (Step 6) |

### Step 8 — Set up the wake word

**Option A — Custom "Hey Charli" keyword** (recommended):

1. Go to https://console.picovoice.ai
2. Click **Wake Word** → **Create Custom Wake Word**
3. Type `hey charli`, select platform **Raspberry Pi**, download the `.ppn` file
4. Copy it to the Pi (run this on your Mac):
   ```bash
   scp ~/Downloads/hey-charli_en_raspberry-pi.ppn charli@charli-home.local:~/charli-home/models/
   ```
5. Add to `~/.bashrc` on the Pi:
   ```bash
   export CHARLI_KEYWORD_PATH="/home/charli/charli-home/models/hey-charli_en_raspberry-pi.ppn"
   ```

**Option B — Use built-in "Jarvis" fallback** (no setup needed):

Skip this step and say "Jarvis" instead of "Hey Charli". You can add the custom keyword later.

### Step 9 — Test the building blocks one by one

Run each test **in order**. Fix any issues before moving to the next:

```bash
cd ~/charli-home
source .venv/bin/activate
```

**Test 1: Microphone**
```bash
python3 src/record.py
```
Expected: records 5 seconds, prints `Saved to .../charli_recording.wav`
Verify: `aplay recordings/charli_recording.wav` (should hear your voice)
If it fails: check `CHARLI_MIC_DEVICE` matches your `arecord -l` output

**Test 2: Speech-to-Text**
```bash
python3 src/transcribe.py
```
Expected: prints what you said as text (transcribes the file from Test 1)
First run: downloads ~150MB model — be patient

**Test 3: OpenClaw Connection**
```bash
python3 src/ask_charli.py
```
Expected: CHARLI responds with a greeting
If "connection refused": check `CHARLI_HOST` and that OpenClaw is running on Mac Mini
If "401 Unauthorized": check `CHARLI_TOKEN`

**Test 4: Text-to-Speech**
```bash
python3 src/speak.py
```
Expected: hear "Hello! I am CHARLI..." from the Bluetooth speaker
If no sound: re-pair Bluetooth, or test with `espeak-ng "test"`

**Test 5: Wake Word**
```bash
python3 src/wake_word.py
```
Expected: say "Hey Charli" (or "Jarvis") and it prints "Wake word detected!"
If it fails: check `PICOVOICE_ACCESS_KEY` is set

**Test 6: System Monitor**
```bash
python3 src/system_monitor.py
```
Expected: prints JSON with CPU temp, RAM, disk, Tailscale status

### Step 10 — Run the full system

```bash
cd ~/charli-home
source .venv/bin/activate
python3 charli_home.py
```

You should see:
```
CHARLI Home v2.0 — Desk Hub
Web UI: http://localhost:8080
Waiting for wake word... (Ctrl+C to quit)
```

Open Chromium on the Pi and go to `http://localhost:8080`. You'll see the JARVIS UI with the animated orb.

Say "Hey Charli" → ask a question → watch the orb change colors → hear the answer.

### Step 11 — Set up the TUI companion (optional)

The TUI is a terminal dashboard that connects to the same WebSocket as the browser. You can run it on the Pi, or remotely from your Mac.

**On the Pi (local):**
```bash
cd ~/charli-home
source .venv/bin/activate
python3 tui/charli_tui.py
```

**From your Mac (remote, pointing at the Pi):**
```bash
# First, install the dependencies on your Mac (one-time):
pip3 install textual websockets

# Run the TUI pointing at the Pi:
python3 ~/CHARLI/raspberry_pi/charli-home/tui/charli_tui.py --host charli-home.local
```

See the [TUI section](#tui-companion) below for full details and Mac alias setup.

### Step 12 — Set up autostart (do this last, once everything works)

Once everything works manually, make it start on boot:

**a) Create the environment file:**
```bash
nano ~/charli-home/.env
```

Add your real values (no `export`, no quotes):
```
CHARLI_HOST=https://your-mac-mini.tail1234.ts.net
CHARLI_TOKEN=your-token
PICOVOICE_ACCESS_KEY=your-key
CHARLI_MIC_DEVICE=hw:0,0
CHARLI_MIC_CHANNELS=1
CHARLI_KEYWORD_PATH=/home/charli/charli-home/models/hey-charli_en_raspberry-pi.ppn
```

**b) Create the systemd service:**
```bash
sudo nano /etc/systemd/system/charli-home.service
```

Paste:
```ini
[Unit]
Description=CHARLI Home Desk Hub
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

Save and enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable charli-home
sudo systemctl start charli-home
```

Check it's running:
```bash
sudo systemctl status charli-home
# Look for "Active: active (running)"
```

View live logs:
```bash
journalctl -u charli-home -f
```

**c) Chromium kiosk (auto-opens the UI on boot):**
```bash
mkdir -p ~/.config/autostart

cat > ~/.config/autostart/charli-kiosk.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=CHARLI Kiosk
Exec=bash -c 'sleep 8 && chromium-browser --kiosk --noerrdialogs --disable-infobars --no-first-run http://localhost:8080'
EOF
```

> The `sleep 8` gives the web server time to start before Chromium tries to load the page.

**d) Hide cursor and disable screen blanking:**
```bash
sudo apt install -y unclutter

cat > ~/.config/autostart/unclutter.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Hide Cursor
Exec=unclutter -idle 0.5 -root
EOF
```

Disable screen blanking (keeps the screen on forever):
```bash
sudo bash -c 'echo "@xset s off" >> /etc/xdg/lxsession/LXDE-pi/autostart'
sudo bash -c 'echo "@xset -dpms" >> /etc/xdg/lxsession/LXDE-pi/autostart'
sudo bash -c 'echo "@xset s noblank" >> /etc/xdg/lxsession/LXDE-pi/autostart'
```

**e) Reboot and verify:**
```bash
sudo reboot
```

After reboot: Pi boots → systemd starts `charli-home` → Chromium opens kiosk → JARVIS UI appears → say "Hey Charli" to test.

---

## TUI Companion

The TUI (Terminal User Interface) is a monitoring dashboard you run in your terminal. It connects to the same `/ws` WebSocket as the browser, so it shows the exact same data — live state changes, conversation transcript, and system metrics.

### What It Looks Like

```
┌── C.H.A.R.L.I. Home ── Desk Hub Monitor ────────────────────────────┐
│ CPU: 42.5°C  |  RAM: 12%  |  NET: connected  |  WS: connected      │
├──────────────────────────────────────────────────────────────────────┤
│                        [ LISTENING ]                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  YOU: What's the weather like today?                                 │
│  CHARLI: It's 72 degrees and sunny in Austin.                        │
│                                                                      │
│  YOU: What about tomorrow?                                           │
│  CHARLI: Tomorrow should be around 68 degrees with a chance of rain. │
│                                                                      │
│  Connection lost: [Errno 111] Connection refused. Retrying in 3s...  │
│  YOU: Are you there?                                                 │
│  CHARLI: I'm here, Sir. Just had a brief network hiccup.            │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│ 🔗 charli-home.local:8080                                            │
├──────────────────────────────────────────────────────────────────────┤
│  q Quit  c Clear                                                     │
└──────────────────────────────────────────────────────────────────────┘
```

**Color scheme (Cyberdeck aesthetic):**
- Status bar: Copper/Brass (#B87333)
- State display: Amber (#FFB000) — changes color per state
- User messages: Cyan (#00d4ff)
- CHARLI messages: Amber (#FFB000)
- Background: Deep Space Blue (#0B1026)

**Keyboard shortcuts:**
| Key | Action |
|-----|--------|
| `q` | Quit the TUI |
| `c` | Clear the transcript |

### Running the TUI

**Option 1 — On the Pi directly:**
```bash
cd ~/charli-home && source .venv/bin/activate
python3 tui/charli_tui.py
```

**Option 2 — From your Mac, pointing at the Pi over the network:**
```bash
python3 tui/charli_tui.py --host charli-home.local
```

**Option 3 — SSH into Pi and run there:**
```bash
ssh charli@charli-home.local
cd ~/charli-home && source .venv/bin/activate
python3 tui/charli_tui.py
```

### Setting Up the `charli` Alias on Your Mac

This lets you type `charli` in any Mac terminal to instantly launch the TUI — just like how you type `claude` to launch Claude Code.

**Step 1 — Install dependencies on your Mac (one-time):**
```bash
pip3 install textual websockets
```

**Step 2 — Add the alias to your shell config:**

For **zsh** (default on Mac):
```bash
# Open your zsh config
nano ~/.zshrc
```

Add this at the bottom:
```bash
# CHARLI Home TUI — type `charli` to launch the monitoring dashboard
alias charli="python3 ~/CHARLI/raspberry_pi/charli-home/tui/charli_tui.py --host charli-home.local"
```

Save and reload:
```bash
source ~/.zshrc
```

For **bash**:
```bash
# Open your bash config
nano ~/.bash_profile

# Add the same alias line, then:
source ~/.bash_profile
```

**Step 3 — Test it:**
```bash
charli
```

You should see the Cyberdeck TUI connect to the Pi and show live state.

> **Requirements:** The Pi must be running (`charli_home.py` or the systemd service) and your Mac must be on the same network (Tailscale or local WiFi).

### How the TUI Connects

```
┌──────────────┐         WebSocket          ┌──────────────────┐
│  Your Mac     │ ───── ws://charli-home ──► │  Pi: FastAPI      │
│  charli_tui   │         :8080/ws           │  (same /ws as     │
│  (Textual)    │ ◄──── state, messages ──── │   the browser UI) │
└──────────────┘                             └──────────────────┘
```

The TUI receives the same WebSocket messages as the browser:
- `snapshot` — full state + history on connect
- `state` — state changes (IDLE → LISTENING → etc.)
- `message` — new transcript entries
- `system` — CPU temp, RAM, Tailscale status every 10s

---

## Web Kiosk Display (7" Touchscreen)

The 7" touchscreen runs Chromium in kiosk mode (fullscreen, no URL bar, no cursor) pointing at `http://localhost:8080`.

### Current Layout: Orb + Transcript

```
800×480 pixels
┌──────────────────────────────────────────────────────────────────┐
│ C.H.A.R.L.I.                                    ● 17:42:03      │ 40px status bar
├────────────────────────┬─────────────────────────────────────────┤
│                        │ TRANSCRIPT                              │
│                        │                                         │
│     ╭────────────╮     │ ┌─YOU──────────────────────────────┐    │
│    ╱  ┌────────┐  ╲    │ │ What's the weather like today?   │    │
│   │   │ ░░░░░░ │   │   │ └─────────────────────────────────┘    │
│   │   │ ░ORB ░ │   │   │                                         │
│   │   │ ░░░░░░ │   │   │ ┌─CHARLI───────────────────────────┐   │
│    ╲  └────────┘  ╱    │ │ It's 72 degrees and sunny in     │   │
│     ╰────────────╯     │ │ Austin today.                     │   │
│                        │ └───────────────────────────────────┘   │
│      [ SPEAKING ]      │                                         │ 440px content
│                        │                                         │
│   360px orb section    │          440px transcript section       │
├────────────────────────┴─────────────────────────────────────────┤
└──────────────────────────────────────────────────────────────────┘
```

**What the orb does in each state:**

| State | Orb Color | Behavior | Label |
|-------|-----------|----------|-------|
| IDLE | Blue (#0088cc) | Slow pulse, gentle wobble | `IDLE` |
| LISTENING | Cyan (#00d4ff) | Faster wobble, more particles | `LISTENING` |
| THINKING | Orange (#ff8c00) | Rapid deformation, energetic | `THINKING` |
| SPEAKING | Gold (#ffc845) | Smooth pulse, warm glow | `SPEAKING` |

**Visual features:**
- **Animated blob orb** — 80-point deformable circle with noise-based wobble
- **Glow layers** — 3 concentric outer rings with increasing transparency
- **HUD rings** — subtle dashed circles for sci-fi aesthetic
- **24 orbiting particles** — tiny dots circling the orb with wobble
- **CRT scanlines** — repeating horizontal lines overlay for retro effect
- **Smooth transitions** — 3% lerp per frame between state color profiles

### How the Web UI Works

```
  charli_home.py                     Browser (Chromium kiosk)
  ┌─────────────┐                    ┌─────────────────────┐
  │ Voice        │  WebSocket /ws    │ charli.js           │
  │ Pipeline     │──────────────────►│  ├─ onmessage()     │
  │              │  {"type":"state", │  │  applyState()     │
  │ set_state()  │   "state":"listen │  │  addTranscript()  │
  │ add_message()│   ing"}           │  └─ Orb.setState()  │
  └──────┬───────┘                   │                      │
         │                           │ orb.js               │
  ┌──────▼───────┐                   │  ├─ drawBlob()       │
  │ State        │  On connect:      │  ├─ drawParticles()  │
  │ Manager      │  sends snapshot   │  └─ animate() 60fps  │
  │ _broadcast() │──────────────────►│                      │
  └──────────────┘                   │ charli.css            │
                                     │  └─ dark JARVIS theme │
                                     └─────────────────────┘
```

1. `charli_home.py` calls `state.set_state(State.LISTENING)`
2. StateManager broadcasts `{"type": "state", "state": "listening"}` to all WebSocket clients
3. `charli.js` receives it, updates the label text + color, tells the orb
4. `orb.js` smoothly transitions the blob from blue to cyan (3% per frame)
5. When the pipeline adds a message, `charli.js` appends it to the transcript div

---

## Display Brainstorm: Future Directions

The current orb + transcript layout works great. Here are ideas for evolving the display — we don't have to pick one, these can be different "modes" or pages on the touchscreen.

### Option A: Cyberdeck Full Dashboard

Combine the orb with stats, logs, and a system bar — everything on one screen:

```
┌──────────────────────────────────────────────────────────────────┐
│ C.H.A.R.L.I.  v2.0      CPU 42°C  RAM 12%  TS ●    17:42:03   │
├──────────────────────────────────────────────────────────────────┤
│                  │                                                │
│   ┌──────────┐   │  YOU: What's the weather?                     │
│   │  ░░░░░░  │   │  CHARLI: It's 72 degrees and sunny.          │
│   │  ░ORB ░  │   │                                               │
│   │  ░░░░░░  │   │  YOU: What about tomorrow?                    │
│   └──────────┘   │  CHARLI: 68 degrees, chance of rain.          │
│   [ LISTENING ]  │                                               │
│                  │                                                │
├──────────────────┴──────────────────────────────────────────────┤
│ [17:42:03] Wake word detected                                    │
│ [17:42:08] Transcribed: "What about tomorrow?"                   │
│ [17:42:09] OpenClaw response (142 tokens, 1.2s)                  │
└──────────────────────────────────────────────────────────────────┘
```

Adds: system metrics in status bar, debug/event log at the bottom.

### Option B: ASCII Art Eyes (Cyberdeck Mode)

Replace the canvas orb with ASCII-animated eyes for a retro terminal feel:

```
┌──────────────────────────────────────────────────────────────────┐
│ ● C.H.A.R.L.I.   [LISTENING]   42°C  12% RAM   TS:OK   17:42  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                                                                  │
│              ╔══════════╗      ╔══════════╗                      │
│              ║  ██████  ║      ║  ██████  ║                      │
│              ║  ██  ██  ║      ║  ██  ██  ║                      │
│              ║  ██████  ║      ║  ██████  ║                      │
│              ╚══════════╝      ╚══════════╝                      │
│                                                                  │
│                         ───────                                  │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ > YOU: What's the weather?                                       │
│ > CHARLI: It's 72 degrees and sunny in Austin.                   │
│ > YOU: What about tomorrow?                                      │
│ > CHARLI: 68 degrees, chance of rain.                            │
└──────────────────────────────────────────────────────────────────┘
```

The eyes could animate:
- **IDLE** — slow blink every few seconds, pupils drift lazily
- **LISTENING** — eyes widen, pupils dilate (bigger inner squares)
- **THINKING** — pupils look side to side (shift the inner blocks)
- **SPEAKING** — eyes half-close to "relaxed", gentle pulse

This could be rendered in a `<pre>` tag with a monospace font, updated via WebSocket — same architecture, just different rendering.

### Option C: Waveform Visualizer

Replace the orb with a live audio waveform during LISTENING, and a pulsing line during other states:

```
┌──────────────────────────────────────────────────────────────────┐
│ C.H.A.R.L.I.                                    ● 17:42:03      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                                                                  │
│                                                                  │
│         ╱╲    ╱╲╱╲       ╱╲                                      │
│  ───╱╲╱╱  ╲╱╱    ╲╱╲╱╲╱╱  ╲╱───────────────────                │
│                                                                  │
│                        [ LISTENING ]                             │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ TRANSCRIPT                                                       │
│ YOU: What's the weather?                                         │
│ CHARLI: It's 72 degrees and sunny.                               │
└──────────────────────────────────────────────────────────────────┘
```

### Option D: Hybrid — Orb + Stats + Swipeable Pages

Keep the orb as the "home" view but add swipeable pages (touchscreen!):

```
Page 1: Voice Assistant (current)     ← swipe →    Page 2: Dashboard
┌─────────────────────────────┐       ┌─────────────────────────────┐
│   ORB + TRANSCRIPT          │       │  CPU ████████░░ 42°C        │
│   (what we have now)        │       │  RAM ██░░░░░░░░ 12%         │
│                             │       │  DSK ██░░░░░░░░  5%         │
│                             │       │  NET ● Tailscale OK         │
│                             │       │  UPT 3h 42m                 │
│                             │       │  ────────────────────       │
│                             │       │  Last 5 conversations:      │
│                             │       │  "weather" · "time" · ...   │
└─────────────────────────────┘       └─────────────────────────────┘

          ← swipe →    Page 3: Quick Actions
          ┌─────────────────────────────┐
          │  ┌─────────┐ ┌──────────┐  │
          │  │ 🎯      │ │ 🎮       │  │
          │  │ Pomodoro │ │ Gaming   │  │
          │  └─────────┘ └──────────┘  │
          │  ┌─────────┐ ┌──────────┐  │
          │  │ 💡      │ │ 📷       │  │
          │  │ Lights  │ │ Camera   │  │
          │  └─────────┘ └──────────┘  │
          └─────────────────────────────┘
```

### Option E: "LCARS" Star Trek Panel

Inspired by Star Trek computer panels — colored blocks and rounded corners:

```
┌──────────────────────────────────────────────────────────────────┐
│██████│ C.H.A.R.L.I. HOME                         │██████████████│
│██████│                                            │              │
│      ├────────────────────────────────────────────┤  CPU  42°C   │
│██████│                                            │  RAM  12%    │
│██████│              ┌──────────┐                  │  DSK  5%     │
│      │              │          │                  │              │
│██████│              │   ORB    │                  │  ● ONLINE    │
│██████│              │          │                  │              │
│      │              └──────────┘                  ├──────────────│
│██████│           [ LISTENING ]                    │ TRANSCRIPT   │
│██████│                                            │              │
│      ├────────────────────────────────────────────┤ You: Hello   │
│██████│ [17:42] Wake word detected                 │ C: Hi Sir!   │
│██████│ [17:42] Recording 5s audio...              │              │
└──────┴────────────────────────────────────────────┴──────────────┘
```

### Recommendation

**Start with Option A (Cyberdeck Full Dashboard)** as the next evolution. It keeps the orb you already have and adds the stats and log panel that the system_monitor is already broadcasting. Minimal new code — just CSS layout changes and handling the `"system"` WebSocket message type in `charli.js`.

Later, the ASCII eyes (Option B) would be a fun project with Isabella — building ASCII art animations is a great intro to coordinate systems and frame-by-frame rendering.

The swipeable pages (Option D) make sense once you have more features (pomodoro, gaming, lights) that need their own screens.

---

## Pulling Updates

When new code is pushed to the repo:

```bash
# On the Pi:
cd ~/CHARLI
git pull

# If requirements.txt changed:
cd ~/charli-home
source .venv/bin/activate
pip install -r requirements.txt

# Restart the service:
sudo systemctl restart charli-home
```

---

## REST API Reference

The web server exposes these endpoints for the Pi↔Mac nervous system:

| Method | Endpoint | Description | Example |
|--------|----------|-------------|---------|
| `GET` | `/health` | Health check (is the Pi alive?) | `curl http://charli-home:8080/health` |
| `GET` | `/api/status` | Current state + metrics | `curl http://charli-home:8080/api/status` |
| `POST` | `/api/speak` | Make Pi speak text aloud | `curl -X POST http://charli-home:8080/api/speak -H 'Content-Type: application/json' -d '{"text":"Dinner is ready"}'` |
| `POST` | `/api/ask` | Ask CHARLI a question | `curl -X POST http://charli-home:8080/api/ask -H 'Content-Type: application/json' -d '{"question":"What time is it?"}'` |
| `WebSocket` | `/ws` | Real-time state + message stream | Connects from browser, TUI, or any WebSocket client |

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `arecord` shows no USB mic | Unplug/replug the mic. Run `arecord -l` again. Update `CHARLI_MIC_DEVICE` in `~/.bashrc`. |
| Wake word not detecting | Verify: `echo $PICOVOICE_ACCESS_KEY` prints your key. Try the "jarvis" fallback. |
| No sound from speaker | Re-pair Bluetooth: `bluetoothctl` → `connect AA:BB:CC:DD:EE:FF`. Test: `espeak-ng "test"` |
| Web UI won't load | Check `curl http://localhost:8080` on the Pi. Look at `journalctl -u charli-home -f` for errors. |
| `CHARLI_HOST: unbound variable` | Run `source ~/.bashrc`. Verify: `echo $CHARLI_HOST` |
| Error 401 Unauthorized | Token is wrong or expired. Re-copy from Mac Mini: `cat ~/.openclaw/openclaw.json` |
| Whisper slow on first run | It's downloading the ~150MB model. Only happens once. Be patient. |
| `ModuleNotFoundError` | You're not in the venv. Run: `source ~/charli-home/.venv/bin/activate` |
| Service won't start | Check logs: `journalctl -u charli-home -f`. Common: missing env vars in `.env` file. |
| Kiosk Chromium shows error | Web server not ready yet. Increase sleep: change `sleep 8` to `sleep 12` in the `.desktop` file. |
| TUI can't connect | Is `charli_home.py` running on the Pi? Is your Mac on the same network (Tailscale)? Try: `curl http://charli-home.local:8080/health` |
| TUI looks garbled | Your terminal might not support the color scheme. Try a different terminal app (iTerm2, Ghostty, Alacritty). |
| `charli` alias not working | Did you `source ~/.zshrc`? Is the path correct? Test with full command first: `python3 ~/CHARLI/raspberry_pi/charli-home/tui/charli_tui.py --host charli-home.local` |

---

## Roadmap

### Voice Assistant (current)
- [x] Wake word detection ("Hey Charli")
- [x] Voice pipeline (record → transcribe → ask → speak)
- [x] JARVIS animated orb UI with live transcript
- [x] faster-whisper (4x speedup over openai-whisper)
- [x] Conversation context (3-turn memory for follow-ups)
- [x] System monitoring (CPU, RAM, Tailscale)
- [x] REST API for Pi↔Mac nervous system
- [x] TUI companion (Textual, Cyberdeck theme)
- [ ] Piper TTS upgrade (natural voice)
- [ ] Voice Activity Detection (stop recording on silence)
- [ ] Conversation persistence (SQLite)

### Display & UI
- [ ] Cyberdeck full dashboard (stats + log + orb)
- [ ] ASCII animated eyes mode
- [ ] Swipeable pages (touch navigation)
- [ ] Quick-action touch buttons
- [ ] Screensaver / photo frame (idle mode)

### Future Features
- [ ] Pomodoro timer ("Hey Charli, start a pomodoro")
- [ ] Retro gaming (RetroPie / EmulationStation)
- [ ] Camera + vision ("Hey Charli, what do you see?")
- [ ] Home automation (smart lights, blinds, MQTT)
- [ ] Weather + calendar dashboard widgets
- [ ] Cloudflare tunnel (phone access without Tailscale)

### How new features plug in

Every feature follows the same pattern:

1. **Add a building block** in `src/` (e.g., `src/pomodoro.py`)
2. **Add a route** in `web/server.py` (e.g., `/pomodoro`)
3. **Add a page** in `web/static/` (e.g., `pomodoro.html`)
4. **Link it** from the main JARVIS home screen

Voice commands go through the same pipeline — CHARLI recognizes intent ("start a pomodoro") and triggers the right action. The hub grows by adding pages and building blocks.

---

*Built with love by Christian and Isabella Bermeo, 2026*
