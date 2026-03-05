# CHARLI Home — Desk Hub
*A JARVIS-style voice assistant + desk hub with a 7" touchscreen — powered by the real CHARLI*

**Status:** In Progress
**Started:** 2026-02-21
**Team:** Christian Bermeo + Isabella Bermeo
**Hardware:** Raspberry Pi 5 8GB · M.2 HAT+ · 256GB NVMe SSD · Active Cooler · 7" Touchscreen · USB Microphone · Bluetooth Speaker

---

## What This Is

A desk hub that lives on your desk with a 7" touchscreen. The home screen is a JARVIS-style voice assistant — say "Hey Charli" and an animated orb lights up, CHARLI listens, thinks, and answers out loud with real-time visual feedback.

But it's more than a voice assistant. The touchscreen is a platform: retro gaming, pomodoro timer, camera experiments, home automation — all one tap (or voice command) away.

The Pi is just the ears, mouth, and display. The brain lives on the Mac Mini via OpenClaw + Tailscale.

---

## Architecture

Three concurrent subsystems sharing a state manager:

```
                   +-----------------+
                   |  State Manager  |  (single source of truth)
                   +-----------------+
                      |    |    |
         +------------+    |    +-------------+
         |                 |                  |
  +------v------+   +-----v------+   +-------v-------+
  | Wake Word   |   | Voice      |   | FastAPI Web   |
  | Listener    |   | Pipeline   |   | Server        |
  | (Porcupine) |   | (building  |   | (WebSocket +  |
  |             |   |  blocks)   |   |  static files)|
  +-------------+   +------------+   +-------+-------+
                                             |
                                    +--------v--------+
                                    | Chromium Kiosk   |
                                    | (localhost:8080) |
                                    | JARVIS UI        |
                                    +-----------------+
```

**Voice pipeline flow:**
```
"Hey Charli" → Porcupine detects → USB mic records 5s → Whisper (speech→text)
→ OpenClaw on Mac Mini (CHARLI responds) → espeak-ng speaks → 7" screen shows orb + transcript
```

**State machine:** `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

---

## Hardware

```
+-----------------------------+
|  7" Official Touchscreen    |  ← HDMI + USB touch, shows JARVIS UI
+-----------------------------+
|  USB Microphone             |  ← plugged into Pi USB port
+-----------------------------+
|  M.2 HAT+ with NVMe SSD    |  ← standoffs + FFC ribbon cable to PCIe
+-----------------------------+
|  Active Cooler (on CPU)     |  ← clips directly onto the SoC chip
+-----------------------------+
|  Raspberry Pi 5             |  ← the board itself
+-----------------------------+
|  Bluetooth Speaker          |  ← paired via Bluetooth
+-----------------------------+
```

---

## Project Structure

```
charli-home/
  charli_home.py              # async orchestrator — runs everything
  requirements.txt            # Python dependencies
  src/
    __init__.py
    state_manager.py          # tracks state + broadcasts to UI via WebSocket
    wake_word.py              # listens for "Hey Charli" (Porcupine)
    record.py                 # records voice from USB mic
    transcribe.py             # Whisper: voice → text
    ask_charli.py             # sends question to CHARLI on Mac Mini
    speak.py                  # speaks answer out loud (espeak-ng)
  web/
    __init__.py
    server.py                 # FastAPI web server + WebSocket endpoint
    static/
      index.html              # JARVIS UI (orb + transcript)
      css/
        charli.css            # dark JARVIS theme + animations
      js/
        charli.js             # WebSocket client + UI updates
        orb.js                # animated glowing orb (canvas)
  models/                     # Porcupine .ppn wake word files
  recordings/                 # temp audio files (gitignored)
```

---

## Step-by-Step Setup

> These are the exact commands to run, in order. Everything happens on the Pi unless noted otherwise.

### Step 1 — SSH into the Pi

From your Mac terminal:
```bash
ssh charli@charli-home.local
```

If `charli-home.local` doesn't resolve, use the Pi's IP address instead:
```bash
ssh charli@192.168.x.x
```

### Step 2 — Install system packages

These are OS-level tools the project needs. Only do this once:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-pip python3-venv curl wget espeak-ng libportaudio2
```

### Step 3 — Clone the repo

```bash
# Clone the full CHARLI repo
git clone https://github.com/christiancabp/CHARLI.git ~/CHARLI

# Create a shortcut so ~/charli-home points to the project folder
# (the code lives at raspberry_pi/charli-home/ inside the repo)
ln -s ~/CHARLI/raspberry_pi/charli-home ~/charli-home
```

Verify it worked:
```bash
ls ~/charli-home/charli_home.py
# Should print: /home/charli/charli-home/charli_home.py
```

> **Why a symlink?** The code lives inside the full CHARLI repo at `raspberry_pi/charli-home/`, but scripts and paths expect `~/charli-home`. The symlink bridges the two — `git pull` in `~/CHARLI` updates everything and `~/charli-home` still works.

### Step 4 — Create the Python virtual environment

```bash
cd ~/charli-home
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt. This means you're inside the virtual environment.

### Step 5 — Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn`, `websockets`, `pvporcupine`, `pvrecorder`, `openai-whisper`, `openai`, `soundfile`, `numpy`.

> **Whisper downloads a ~145MB model the first time you run it.** This is normal and only happens once.

### Step 6 — Find your USB microphone device

```bash
arecord -l
```

Look for your USB mic in the output. Example:
```
card 1: Microphone [USB Microphone], device 0: USB Audio [USB Audio]
```

In this example the device string would be `plughw:1,0` (card 1, device 0). The `plughw:` prefix tells ALSA to auto-convert audio formats.

### Step 7 — Set environment variables

Open `~/.bashrc`:
```bash
nano ~/.bashrc
```

Add these lines at the very bottom (replace the placeholder values with your actual values):
```bash
# ── CHARLI Home ──────────────────────────────────────
# Gateway connection (get CHARLI_TOKEN from Mac Mini: cat ~/.openclaw/openclaw.json)
export CHARLI_HOST="https://your-mac-mini.tail1234.ts.net"
export CHARLI_TOKEN="paste-your-token-here"

# Picovoice wake word (get key at https://console.picovoice.ai)
export PICOVOICE_ACCESS_KEY="paste-your-key-here"

# USB mic (use the device string from Step 6)
export CHARLI_MIC_DEVICE="plughw:1,0"
export CHARLI_MIC_CHANNELS="1"
```

Save and exit: **Ctrl+X → Y → Enter**

Apply the changes:
```bash
source ~/.bashrc
```

**How to get each value:**

| Variable | Where to get it |
|----------|----------------|
| `CHARLI_HOST` | On Mac Mini, run: `tailscale status` to see the hostname, or run `/Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg 18789` to set up Tailscale Serve and get the HTTPS URL |
| `CHARLI_TOKEN` | On Mac Mini, run: `cat ~/.openclaw/openclaw.json \| python3 -c "import sys,json; print(json.load(sys.stdin)['gateway']['auth']['token'])"` |
| `PICOVOICE_ACCESS_KEY` | Sign up at https://console.picovoice.ai → copy your Access Key from the dashboard |
| `CHARLI_MIC_DEVICE` | From `arecord -l` output (Step 6) |

### Step 8 — Set up the wake word

Option A — **Custom "Hey Charli" keyword** (recommended):
1. Go to https://console.picovoice.ai
2. Click **Wake Word** → **Create Custom Wake Word**
3. Type `hey charli`, select platform **Raspberry Pi**, download the `.ppn` file
4. Copy it to the Pi:
   ```bash
   # Run this on your Mac:
   scp ~/Downloads/hey-charli_en_raspberry-pi.ppn charli@charli-home.local:~/charli-home/models/
   ```
5. Tell CHARLI Home where to find it (add to `~/.bashrc`):
   ```bash
   export CHARLI_KEYWORD_PATH="/home/charli/charli-home/models/hey-charli_en_raspberry-pi.ppn"
   ```

Option B — **Use built-in "Jarvis" fallback** (no setup needed):

If you skip this step, the system automatically falls back to the built-in "Jarvis" wake word. Say "Jarvis" instead of "Hey Charli". You can always add the custom keyword later.

### Step 9 — Test the building blocks one by one

Run each test **in order**. Fix any issues before moving to the next:

```bash
cd ~/charli-home
source .venv/bin/activate

# Test 1: Does the mic record?
python3 src/record.py
# Expected: records 5 seconds, prints "Saved to .../charli_recording.wav"
# If it fails: check CHARLI_MIC_DEVICE matches your arecord -l output

# Test 2: Does Whisper transcribe?
# (speak into the mic during test 1 first so there's audio to transcribe)
python3 src/transcribe.py
# Expected: prints what you said as text
# First run downloads the model (~145MB) — be patient

# Test 3: Can we reach CHARLI on the Mac Mini?
python3 src/ask_charli.py
# Expected: CHARLI responds with a greeting
# If "connection refused": check CHARLI_HOST and that OpenClaw is running on Mac Mini
# If "401 Unauthorized": check CHARLI_TOKEN

# Test 4: Does text-to-speech work?
python3 src/speak.py
# Expected: you hear "Hello! I am CHARLI..." from the Bluetooth speaker
# If no sound: re-pair Bluetooth, or test with: espeak-ng "test"

# Test 5: Does wake word detection work?
python3 src/wake_word.py
# Expected: say "Hey Charli" (or "Jarvis") and it prints "Wake word detected!"
# If it fails: check PICOVOICE_ACCESS_KEY is set
```

### Step 10 — Run the full system

```bash
cd ~/charli-home
source .venv/bin/activate
python3 charli_home.py
```

You should see:
```
CHARLI Home v1.0 — Desk Hub
Web UI: http://localhost:8080
Waiting for wake word... (Ctrl+C to quit)
```

Open Chromium on the Pi's touchscreen and go to `http://localhost:8080`. You should see the JARVIS UI with the animated orb.

Say "Hey Charli" → ask a question → watch the orb change colors → hear the answer.

### Step 11 — Set up autostart (optional, do this last)

Once everything works manually, set it up to start on boot:

**a) Create the environment file:**
```bash
nano ~/charli-home/.env
```

Add (with your real values — no `export`, no quotes):
```
CHARLI_HOST=https://your-mac-mini.tail1234.ts.net
CHARLI_TOKEN=your-token
PICOVOICE_ACCESS_KEY=your-key
CHARLI_MIC_DEVICE=plughw:1,0
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

Disable screen blanking:
```bash
# Add to the end of /etc/xdg/lxsession/LXDE-pi/autostart:
sudo bash -c 'echo "@xset s off" >> /etc/xdg/lxsession/LXDE-pi/autostart'
sudo bash -c 'echo "@xset -dpms" >> /etc/xdg/lxsession/LXDE-pi/autostart'
sudo bash -c 'echo "@xset s noblank" >> /etc/xdg/lxsession/LXDE-pi/autostart'
```

**e) Reboot and verify:**
```bash
sudo reboot
```

After reboot, the Pi should boot straight into the JARVIS UI with no cursor. Say "Hey Charli" to test.

---

## Pulling updates

When new code is pushed to the repo:

```bash
cd ~/CHARLI
git pull

# If requirements.txt changed:
cd ~/charli-home
source .venv/bin/activate
pip install -r requirements.txt

# Restart the service
sudo systemctl restart charli-home
```

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| `arecord` shows no USB mic | Unplug/replug the mic. Run `arecord -l` again. Update `CHARLI_MIC_DEVICE`. |
| Wake word not detecting | Verify: `echo $PICOVOICE_ACCESS_KEY` prints your key. Try the "jarvis" fallback. |
| No sound from speaker | Re-pair Bluetooth: `bluetoothctl` → `connect AA:BB:CC:DD:EE:FF`. Test: `espeak-ng "test"` |
| Web UI won't load | Check `curl http://localhost:8080` on the Pi. Look at `journalctl -u charli-home -f` for errors. |
| `CHARLI_HOST: unbound variable` | Run `source ~/.bashrc`. Verify: `echo $CHARLI_HOST` |
| Error 401 Unauthorized | Token is wrong or expired. Re-copy from Mac Mini. |
| Whisper slow on first run | It's downloading the 145MB model. Only happens once. |
| `ModuleNotFoundError` | You're not in the venv. Run: `source ~/charli-home/.venv/bin/activate` |
| Service won't start | Check logs: `journalctl -u charli-home -f`. Common: missing env vars in `.env` file. |
| Kiosk Chromium shows error | The web server may not be ready yet. Increase the sleep in the `.desktop` file (try `sleep 12`). |

---

## Roadmap — The Hub Grows

The 7" touchscreen + FastAPI architecture makes this a **platform**. The JARVIS orb is the home screen — everything else is a tap or voice command away.

### Voice Assistant (current)
- [x] Wake word detection ("Hey Charli")
- [x] Voice pipeline (record → transcribe → ask → speak)
- [x] JARVIS animated orb UI with live transcript
- [ ] Piper TTS upgrade (natural British "Alan" voice)
- [ ] Conversation memory across turns

### Pomodoro Timer
- [ ] "Hey Charli, start a pomodoro" — voice-triggered focus sessions
- [ ] 25-min work / 5-min break cycle with orb visual countdown
- [ ] CHARLI announces breaks: "Time for a break, Sir"
- [ ] Session stats on the touchscreen (streaks, total focus time)
- [ ] Do Not Disturb mode — wake word disabled during focus blocks

### Retro Gaming
- [ ] RetroPie / EmulationStation installed alongside CHARLI Home
- [ ] Launch emulators from the touchscreen UI or by voice: "Hey Charli, let's play some games"
- [ ] NES, SNES, Game Boy, GBA, N64, PS1 via RetroArch
- [ ] Bluetooth controller support (pair like the speaker)
- [ ] "Hey Charli, I'm done gaming" — returns to JARVIS home screen

### Camera + Vision (Camera Module 3 Wide)
- [ ] Live camera feed on a `/camera` page via `picamera2`
- [ ] Object detection — "Hey Charli, what do you see?"
- [ ] Face recognition — CHARLI greets family members by name
- [ ] Time-lapse and security cam modes
- [ ] Vision + voice combined (describe what the camera sees)

### Home Automation / IoT
- [ ] `/automation` dashboard with device controls on the touchscreen
- [ ] Smart blinds — "Hey Charli, open the blinds"
- [ ] Smart lights — "Hey Charli, turn off the lights"
- [ ] Home Assistant integration (REST API) or direct MQTT
- [ ] Morning routine — "Good morning" opens blinds, reads weather, starts coffee

### Dashboard Widgets
- [ ] Weather forecast
- [ ] Family calendar (Google Calendar)
- [ ] Photo frame / screensaver when idle
- [ ] System stats (CPU temp, uptime)

### How new features plug in

Every feature follows the same pattern:

1. **Add a building block** in `src/` (e.g., `src/pomodoro.py`, `src/camera.py`)
2. **Add a route** in `web/server.py` (e.g., `/pomodoro`, `/camera`)
3. **Add a page** in `web/static/` (e.g., `pomodoro.html`, `games.html`)
4. **Link it** from the main JARVIS home screen

Voice commands go through the same pipeline — CHARLI can recognize intent ("start a pomodoro", "open the blinds", "let's play games") and trigger the right action. The hub grows by adding pages and building blocks, not by rewriting anything.

---

*Built with love by Christian and Isabella Bermeo, 2026*
