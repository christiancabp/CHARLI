# Project 1: CHARLI's Home 🏠🤖
*A JARVIS-style voice assistant — powered by the real CHARLI*

**Status:** In Progress
**Started:** 2026-02-21
**Team:** Christian Bermeo + Isabella Bermeo 🎨
**Hardware:** Raspberry Pi 5 8GB · Official M.2 HAT+ · 256GB NVMe SSD · Active Cooler · Pirate Audio Dual Mic HAT · Bluetooth Speaker

---

## 🎯 What We're Building

A home voice assistant. You press a button → say something → Charli listens, thinks, and answers out loud through the speaker. The display shows a glowing animated orb that reacts to your voice, plus the text of what Charli said.

This isn't a generic AI — it's the actual CHARLI who knows Sir, Madam, and the whole family. The Pi is just the ears, mouth, and display. The brain lives on the Mac Mini.

```
[Say "Charli" or "Hey Charli"]
             ↓
 [Porcupine detects wake word]
             ↓
  [Pirate Audio mics record]
             ↓
[Whisper: speech → text + language]
             ↓
 [OpenClaw → Real CHARLI responds]
             ↓
  [Piper TTS speaks the response]
             ↓
  [Display shows orb + subtitles]
```

> **Phase 2 uses a button instead of wake word** -- press Button A to trigger.
> **Phase 5 upgrades to wake word** -- just say the name. Both approaches use the same pipeline underneath.

---

## 🖥️ Display Design

The Pirate Audio HAT has a small 240×240 color screen. It shows two things at once:

```
┌─────────────────────────┐
│                         │
│      Glowing Orb        │  ← top 75% — animated based on state
│   wobbles with voice    │
│                         │
├─────────────────────────┤
│  Subtitle text here...  │  ← bottom 25% — shows what Charli said
└─────────────────────────┘
```

| What's happening | Orb color | Text shown |
|------------------|-----------|------------|
| **Idle** | Dim blue, slow breathing | Clock |
| **Listening** | Bright teal, wobbles with your voice | "Listening..." |
| **Thinking** | Orange, 4 dots orbiting | Your question |
| **Speaking** | Gold, pulsing | Charli's response |

---

## 📦 What We Have

| Item | Note |
|------|------|
| Raspberry Pi 5 8GB | The main computer |
| Official Raspberry Pi M.2 HAT+ | Sits on top of the Pi — holds the NVMe SSD. Includes GPIO header extender. |
| 256GB NVMe SSD | Our boot drive — plugs into the M.2 HAT+. Much faster than microSD. |
| Official Raspberry Pi Active Cooler | Fan + heatsink — clips onto the CPU. Keeps the Pi cool under load. |
| Pirate Audio Dual Mic HAT | Microphones + color display — stacks on top via the GPIO extender |
| Bluetooth Speaker | Charli's voice |
| 32GB microSD | Used ONLY for the very first boot (see Phase 0) |
| Keyboard + Mouse + Monitor | Only needed for first boot setup |

### Hardware Stack (bottom to top)

```
┌─────────────────────────────┐
│  Pirate Audio Dual Mic HAT  │  ← plugs into the extended GPIO pins
├─────────────────────────────┤
│  GPIO Header Extender       │  ← included with M.2 HAT+
├─────────────────────────────┤
│  M.2 HAT+ with NVMe SSD    │  ← standoffs + FFC ribbon cable to PCIe
├─────────────────────────────┤
│  Active Cooler (on CPU)     │  ← clips directly onto the SoC chip
├─────────────────────────────┤
│  Raspberry Pi 5             │  ← the board itself
└─────────────────────────────┘
```

> The Active Cooler fits between the Pi 5 and the M.2 HAT+ — Raspberry Pi designed the standoff height to accommodate it. The GPIO header extender (included with the M.2 HAT+) passes the GPIO pins through so the Pirate Audio HAT can plug in on top.

---

## 🗓️ What We Build Each Sunday

| Phase | Goal | Saturday Plan |
|-------|------|---------------|
| 0 | First boot + OS setup + Tailscale | Morning — hardware setup |
| 1 | Mic HAT + Bluetooth speaker working | Morning |
| 2 | **Voice pipeline** — say something, hear Charli respond 🎉 | Late morning (THE GOAL) |
| 3 | Wobble Orb display + subtitles | Afternoon (if time allows) |
| 4 | Natural voice — Piper TTS (Alan + Spanish) | Afternoon (if time allows) |
| 5 | Wake word — "Charli" or "Hey Charli" | Afternoon (if time allows) |
| 6 | Smart home automations | Future Sunday |

> **Saturday minimum goal: Phase 2.** If Phase 2 is working — you speak, Charli answers — that's a win.
> Phases 3–5 are the polish. Don't stress them if time is short. Record the video after Phase 2.

---
---

# 📋 PHASE 0: First Boot

## Step 0.1 — Flash the 32GB microSD Card

> We start with the microSD just for the first boot. Later we move everything to the faster NVMe SSD.

**👩‍💻 Isabella: you're in charge of the mouse for this step.**

1. Download **Raspberry Pi Imager** on the Mac: https://www.raspberrypi.com/software/
2. Insert the 32GB microSD into the Mac (use the adapter if needed)
3. Open Raspberry Pi Imager
4. Before clicking "Write", click the **⚙️ gear icon** and fill in:
   - Hostname: `charli-home`
   - Username: `charli`
   - Password: pick something and write it down!
   - WiFi network name (SSID) and password
   - ✅ Check "Enable SSH" → Use password authentication
   - Set timezone to: `America/New_York`
5. Choose:
   - **Device:** Raspberry Pi 5
   - **OS:** Raspberry Pi OS (64-bit) — the full desktop version
   - **Storage:** the 32GB microSD card
6. Click **Write** and wait about 5 minutes

## Step 0.2 — Assemble the Active Cooler

> Do this BEFORE the first boot. The Active Cooler keeps the CPU from overheating — especially important when running Whisper later.

1. With the Pi 5 **unplugged and powered off**, look at the top of the board
2. Find the **fan header** — a small white connector near the edge of the board (labeled "FAN")
3. Clip the Active Cooler's heatsink onto the silver CPU chip (the SoC) in the center of the board — it clips on with spring-loaded push pins
4. Plug the fan's cable into the fan header
5. That's it — the fan will spin automatically when the Pi gets warm

## Step 0.3 — First Boot from microSD

1. Insert the microSD into the Pi 5 (slot is on the underside)
2. Connect the monitor, keyboard, and mouse to the Pi
3. Plug in power — the Pi will boot! The Active Cooler fan may spin up briefly.
4. **👩‍💻 Isabella: watch it boot for the first time** 🎉
5. Go through the setup wizard (you can skip installing updates for now)

## Step 0.4 — Update the Pi's Bootloader

> This tells the Pi how to boot from the NVMe SSD. Run this before we move over.

```bash
# Open a Terminal on the Pi (or SSH in from Mac)
sudo apt update
sudo rpi-eeprom-update -a
sudo reboot
```

## Step 0.5 — Install the M.2 HAT+ and Move the OS to the NVMe SSD

> The M.2 HAT+ sits on top of the Pi (above the Active Cooler) and holds the NVMe SSD. It connects to the Pi's PCIe slot via a flat ribbon cable (FFC).

### Install the hardware:

1. Shut down the Pi: `sudo shutdown now` and unplug power
2. **Insert the NVMe SSD** into the M.2 slot on the M.2 HAT+ board and secure it with the screw
3. **Connect the FFC ribbon cable** from the M.2 HAT+ to the Pi 5's PCIe connector (the small flat connector near the edge of the board — lift the latch, slide the ribbon in, press the latch down)
4. **Mount the M.2 HAT+** above the Pi using the included standoffs — the Active Cooler fits in the gap between them
5. **Attach the GPIO header extender** to the top of the M.2 HAT+ (this passes the GPIO pins through so the Pirate Audio HAT can connect later)
6. Plug the microSD back in (we still need it for this step)
7. Power the Pi back on — it will boot from microSD

### Copy the OS to the NVMe SSD:

```bash
# This copies everything from the microSD to the NVMe SSD
sudo apt install -y rpi-imager
rpi-imager
# Inside the app: choose "Copy current SD card" → pick the NVMe SSD as destination
```

Or use the command line approach:

```bash
# Find your NVMe device name (usually /dev/nvme0n1)
lsblk
# You'll see the microSD (mmcblk0) and the NVMe (nvme0n1)

# Clone microSD → NVMe (replace nvme0n1 with what lsblk showed)
sudo dd if=/dev/mmcblk0 of=/dev/nvme0n1 bs=4M status=progress
sudo sync
```

8. Shut down: `sudo shutdown now`
9. Remove the microSD card
10. Power on — Pi now boots from the 256GB NVMe SSD ✅

## Step 0.6 — SSH In From the Mac

> After this step, we won't need the monitor/keyboard/mouse anymore. We work from the Mac.

### How to open Terminal on the Mac:
1. Press **Cmd + Space** to open Spotlight
2. Type **Terminal** and press Enter
3. A black/white window will appear — this is the Terminal

### Connect to the Pi:
```bash
# On your Mac, in Terminal, type this and press Enter:
ssh charli@charli-home.local
```

The first time you connect, you'll see a message like:
```
The authenticity of host 'charli-home.local' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxx
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```
Type **yes** and press Enter. This only happens the first time.

Then it will ask for the password you set in Step 0.1. Type it and press Enter.
(The password won't show as you type — that's normal! Just type it and press Enter.)

You'll know you're connected when the prompt changes to something like:
```
charli@charli-home:~ $
```

### If `charli-home.local` doesn't work:
Sometimes `.local` names take a minute to show up on the network. Try these in order:

1. **Wait 30 seconds and try again** — the Pi may still be starting up
2. **Find the Pi's IP address** — on the Pi (with the monitor still connected), run:
   ```bash
   hostname -I
   ```
   It will print something like `192.168.1.42`. Then on the Mac:
   ```bash
   ssh charli@192.168.1.42
   ```
3. **Check they're on the same WiFi** — the Mac and Pi must be on the same network

### To disconnect from the Pi:
```bash
exit
```
This brings you back to your Mac's Terminal. You can reconnect anytime with `ssh charli@charli-home.local`.

**👩‍💻 Isabella: you type the SSH command. You're logging into the Pi remotely!**

## Step 0.7 — Install Essential Tools

```bash
# Update the system packages list
sudo apt update && sudo apt upgrade -y

# Install tools we'll need throughout the project
sudo apt install -y git python3-pip python3-venv curl wget htop espeak-ng libportaudio2
```

> **What does this install?**
> - `git` — downloads code from the internet
> - `python3-venv` — creates a safe Python workspace for our project
> - `espeak-ng` — a basic text-to-speech engine (we'll upgrade later)
> - `libportaudio2` — audio library that lets Python record from the microphone

---

# 📋 PHASE 0B: Install Tailscale

> Tailscale creates a private network between the Pi and the Mac Mini. This is how the Pi talks to CHARLI even if they're on different WiFi networks. Think of it like a secret tunnel between the two computers.

**On the Pi:**
```bash
# Download and install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to your Tailscale account
# This will print a URL — open it in a browser on your phone or Mac
sudo tailscale up
```

**On the Mac Mini** (if Tailscale isn't already installed):
```bash
brew install tailscale
sudo tailscale up
```

**Check that both devices can see each other:**
```bash
tailscale status
# You should see both "charli-home" and the Mac Mini listed with green status
```

**Find the Mac Mini's Tailscale IP address — write this down, you'll need it later:**
```bash
# Run this ON the Mac Mini (not the Pi)
tailscale ip -4
# Example output: 100.64.1.5  ← your number will be different
```

---

# 📋 PHASE 1: Pirate Audio HAT

## Step 1.1 — Physical Installation

> The Pirate Audio HAT plugs onto the GPIO header extender that's already sticking up from the M.2 HAT+. It sits at the very top of the stack.

1. **Shut down the Pi first!** Never add hardware while powered on.
   ```bash
   sudo shutdown now
   ```
2. Unplug the power cable
3. Align the Pirate Audio Dual Mic HAT over the GPIO header extender on top of the M.2 HAT+
4. Press down firmly and evenly until it's fully seated — the pins should be snug
5. Your full stack is now: **Pi 5 → Active Cooler → M.2 HAT+ (with NVMe) → GPIO Extender → Pirate Audio HAT**
6. Power the Pi back on

## Step 1.2 — Enable SPI (Needed for the Display)

> SPI is a communication protocol the display uses. We need to turn it on.

```bash
sudo raspi-config
```

Inside the menu:
- Go to **Interface Options**
- Enable **SPI** → Yes
- Enable **I2C** → Yes (while we're here)
- Go back → **Finish** → **Yes** to reboot

## Step 1.3 — Install Pirate Audio Drivers

```bash
# Download the Pimoroni setup scripts
git clone https://github.com/pimoroni/pirate-audio
cd pirate-audio

# Run the installer — say YES to everything it asks
sudo ./install.sh

# Reboot when it's done
sudo reboot
```

After rebooting, SSH back in:
```bash
ssh charli@charli-home.local
```

## Step 1.4 — Test the Microphones

> We haven't connected the Bluetooth speaker yet, so we can't listen to the recording on the Pi. Instead we'll check that the mic is detected, record a clip, and verify the file isn't empty.

```bash
# Show available audio recording devices — should list the Pirate Audio HAT
arecord -l
```

You should see something like `card 0: ... Pirate Audio` in the list. If you don't see it, the HAT may not be seated properly — power off and re-seat it.

```bash
# Record 5 seconds of audio — talk into the mic while this runs!
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/mic_test.wav

# Check that the file was created and has actual audio data (should be ~160KB, NOT 0 bytes)
ls -lh /tmp/mic_test.wav
```

If the file size is around **156K–160K**, the mic is recording. ✅
If the file is **0 bytes** or the command fails, try `hw:1,0` instead of `hw:0,0`.

**Want to hear the recording?** Copy it to your Mac and play it there:
```bash
# Run this ON YOUR MAC (not the Pi) — it copies the file from the Pi to your Desktop
scp charli@charli-home.local:/tmp/mic_test.wav ~/Desktop/mic_test.wav
```
Then double-click `mic_test.wav` on your Mac Desktop to listen. If you hear your voice, the mic works!

**👩‍💻 Isabella: say something fun into the mic while it records, then check if the file has your voice!**

## Step 1.5 — Connect the Bluetooth Speaker

```bash
# Open the Bluetooth control tool
bluetoothctl

# Type these commands one at a time inside bluetoothctl:
power on
agent on
scan on
```

Wait a few seconds — you'll see devices appear. Find your speaker's name and note its address (looks like `AA:BB:CC:DD:EE:FF`). Then:

```bash
# Replace AA:BB:CC:DD:EE:FF with your speaker's actual address
pair AA:BB:CC:DD:EE:FF
connect AA:BB:CC:DD:EE:FF
trust AA:BB:CC:DD:EE:FF
exit
```

Install Bluetooth audio support:
```bash
# On Pi OS Bookworm, use pipewire (the modern audio system)
sudo apt install -y pipewire pipewire-pulse wireplumber
sudo systemctl --user enable pipewire pipewire-pulse
sudo systemctl --user start pipewire pipewire-pulse
```

Test that audio works through the speaker:
```bash
espeak-ng "Hello! Charli Home audio test. If you can hear this, it is working!"
```

**👩‍💻 Isabella: press play and listen for Charli's robotic voice through the speaker.**

---

# 📋 PHASE 2: Setting Up Python

## Step 2.1 — Create the Project Folder

```bash
# Create the project directory
mkdir -p ~/charli-home/src

# Move into it
cd ~/charli-home

# Create a Python "virtual environment" — a clean, isolated space for our project's packages
# Think of it like a separate room just for this project's tools
python3 -m venv .venv

# Activate the virtual environment — we need to do this every time we work on the project
source .venv/bin/activate

# You'll see (.venv) appear at the start of your terminal line — that means it's active ✅
```

## Step 2.2 — Install Python Packages

```bash
# Make sure pip (the package installer) is up to date
pip install --upgrade pip

# Audio recording and file handling
pip install sounddevice soundfile numpy

# Whisper — speech-to-text AI (runs locally on the Pi, no internet needed)
# Warning: this is a big download. Be patient — it only happens once!
pip install openai-whisper

# The OpenAI Python library — we use this to talk to CHARLI's gateway
# (Despite the name, we're NOT calling OpenAI — we're calling our own CHARLI)
pip install openai

# GPIO -- lets Python control the Pi's buttons (Phase 2 only)
pip install RPi.GPIO

# Display libraries — for the Wobble Orb animation
pip install st7789 pillow pygame
```

## Step 2.3 — Save CHARLI's Connection Info

> The Pi needs to know WHERE to find CHARLI (Mac Mini's address) and a secret token to prove it's allowed to connect.

```bash
# Open the .bashrc file — this runs automatically every time you open a terminal
nano ~/.bashrc
```

Scroll to the very bottom and add these two lines:
```bash
export CHARLI_HOST="http://100.64.1.5:18789"   # ← replace with Mac Mini's Tailscale IP from Phase 0B
export CHARLI_TOKEN="paste-your-token-here"     # ← see instructions below
```

Press **Ctrl+X** → **Y** → **Enter** to save.

```bash
# Apply the changes right now
source ~/.bashrc
```

**How to get the CHARLI_TOKEN:**
On the **Mac Mini**, run:
```bash
cat ~/.openclaw/openclaw.json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['gateway']['auth']['token'])
"
```
Copy that value and paste it as CHARLI_TOKEN above.

**Test that the connection works:**
```bash
curl -s "$CHARLI_HOST/v1/chat/completions" \
  -H "Authorization: Bearer $CHARLI_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"openclaw:main","messages":[{"role":"user","content":"Say hello in one sentence."}],"max_tokens":50,"user":"pi-home"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['choices'][0]['message']['content'])"
```

If CHARLI responds — you're connected! ✅

---

# 📋 PHASE 2: Writing the Code

> **👩‍💻 Isabella: you write every line below. Dad will explain what each part does as you go.**
> Take your time. If something doesn't make sense, ask!

## File 1: `src/record.py` — Record Audio When Button is Pressed

> This is the first building block. It does ONE thing: record audio from the microphone and save it to a file. Later, `charli_home.py` will import this function and use it as a step in the pipeline.

```bash
nano ~/charli-home/src/record.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Building Block 1: Record audio from the microphone.
Written by: Isabella Bermeo 🎨

This file does ONE thing: record audio and save it.
The main program (charli_home.py) imports this and uses it as one step.
"""

# sounddevice records audio from the microphone.
import sounddevice as sd

# soundfile saves the recorded audio to a file.
import soundfile as sf


# ── Settings ──────────────────────────────────────────────────────────
# How many audio samples per second? 16000 is great quality for voice.
SAMPLE_RATE = 16000

# How many seconds to record when the button is pressed.
DURATION = 5

# Where to save the audio file.
OUTPUT_FILE = "/tmp/charli_recording.wav"


# ── The recording function ────────────────────────────────────────────
def record_audio():
    """Records audio from the microphone and saves it to a file."""

    print("🎤 Recording — speak now!")

    # Record audio: capture DURATION seconds at SAMPLE_RATE samples/sec, 1 channel (mono)
    audio_data = sd.rec(
        int(DURATION * SAMPLE_RATE),  # total number of samples to capture
        samplerate=SAMPLE_RATE,
        channels=1,                   # mono recording (1 microphone channel)
        dtype='int16'                 # audio format
    )

    # Wait here until the recording is completely done
    sd.wait()

    # Save the recorded audio to a .wav file
    sf.write(OUTPUT_FILE, audio_data, SAMPLE_RATE)

    print(f"✅ Saved to {OUTPUT_FILE}")
    return OUTPUT_FILE


# ── Test it ───────────────────────────────────────────────────────────
# This only runs if you run this file by itself (not when imported).
# That way you can test this building block alone before using it in the main app.
if __name__ == "__main__":
    print("Recording test — speak into the mic for 5 seconds...")
    record_audio()
```

**Test it:**
```bash
cd ~/charli-home
source .venv/bin/activate
python3 src/record.py
```

Speak into the mic and confirm you see "✅ Saved". ✅

> **How does `if __name__ == "__main__"` work?**
> When you run `python3 src/record.py` directly, Python sets `__name__` to `"__main__"`, so the test code runs.
> But when another file does `from src.record import record_audio`, the test code is skipped — only the function is loaded.
> This is how Python building blocks work: each file can be tested alone OR imported by other files.

---

## File 2: `src/transcribe.py` — Convert Audio to Text

> Building block 2: takes an audio file and returns what was said as text.

```bash
nano ~/charli-home/src/transcribe.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Building Block 2: Convert audio into text using Whisper.
Whisper is an AI that runs locally on the Pi — no internet needed!
"""

# Whisper is an AI speech-to-text model made by OpenAI.
# We downloaded it when we ran "pip install openai-whisper".
import whisper


# ── Load the model ────────────────────────────────────────────────────
# "base" is a small, fast model — perfect for the Pi 5.
# The FIRST time you run this, it downloads about 145MB. Be patient!
# After that first download, it loads instantly from the Pi's storage.
print("Loading Whisper AI model... (first time takes a minute)")
model = whisper.load_model("base")
print("✅ Whisper is ready!")


# ── The transcribe function ───────────────────────────────────────────
def transcribe(audio_path: str) -> tuple:
    """
    Takes the path to an audio file and returns (text, language).
    Whisper auto-detects the spoken language -- no need to specify it.
    Examples:
      ("What is the weather?", "en")
      ("\u00bfQu\u00e9 hora es?", "es")
    """

    print(f"\U0001f4dd Listening to {audio_path}...")

    # Detect language first (Whisper's built-in feature)
    audio = whisper.load_audio(audio_path)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    _, probs = model.detect_language(mel)
    language = max(probs, key=probs.get)  # "en", "es", etc.

    # Transcribe using the detected language (more accurate than guessing)
    result = model.transcribe(audio_path, language=language)
    text = result["text"].strip()

    lang_name = "English" if language == "en" else "Spanish" if language == "es" else language
    print(f"\U0001f4ac [{lang_name}] You said: '{text}'")
    return text, language


# ── Test it ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    text, lang = transcribe("/tmp/charli_recording.wav")
    print(f"Language detected: {lang}")
```

**Test it** (after recording something with record.py):
```bash
python3 src/transcribe.py
```

You should see your words printed as text. ✅

---

## File 3: `src/ask_charli.py` — Ask the Real CHARLI

> Building block 3: sends a question to CHARLI and returns her answer.

```bash
nano ~/charli-home/src/ask_charli.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Building Block 3: Send a question to CHARLI and get her response.

IMPORTANT: We are NOT calling OpenAI or any random AI service.
We are calling the OpenClaw gateway running on Dad's Mac Mini.
This is the SAME CHARLI who knows our family, remembers our conversations,
and has all her personality. The Pi is just a new way to talk to her.
"""

# os lets us read environment variables (like CHARLI_HOST and CHARLI_TOKEN)
import os

# OpenAI is a Python library for talking to AI APIs.
# We configured it to point to OUR gateway instead of OpenAI's servers.
from openai import OpenAI


# ── Connect to CHARLI ─────────────────────────────────────────────────
# Read the host and token we saved in .bashrc earlier
charli_host  = os.environ["CHARLI_HOST"]
charli_token = os.environ["CHARLI_TOKEN"]

# Create a client that talks to OUR OpenClaw gateway, not OpenAI
client = OpenAI(
    base_url=f"{charli_host}/v1",  # our gateway address
    api_key=charli_token           # our secret token
)


# ── Instructions for CHARLI when responding via the Pi ────────────────
# This tells CHARLI how to behave when answering voice queries.
PI_SYSTEM_PROMPT = """You are responding through the CHARLI Home Raspberry Pi voice assistant.
This means your answer will be spoken out loud through a speaker.

Rules for Pi responses:
- Keep answers SHORT: 1 to 3 sentences maximum.
- No bullet points, no numbered lists, no markdown symbols like * or #.
- Speak naturally, like you're talking to someone in the room.
- You still know Sir (Christian), Madam (Dominica), Isabella, and the family.
- All family protocols and boundaries apply as always.
- IMPORTANT: Respond in {lang_name}. Match the language the user spoke."""


# ── The ask function ──────────────────────────────────────────────────
def ask_charli(question: str, language: str = "en") -> str:
    """
    Sends a question to CHARLI and returns her response.
    Pass the detected language so CHARLI responds in the same language.
    """

    lang_name = "English" if language == "en" else "Spanish" if language == "es" else "English"
    print(f"\U0001f914 [{lang_name}] Asking CHARLI: '{question}'")

    # Fill in the language in the system prompt
    prompt = PI_SYSTEM_PROMPT.replace("{lang_name}", lang_name)

    # Send the question to the OpenClaw gateway
    response = client.chat.completions.create(
        model="openclaw:main",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user",   "content": question}
        ],
        max_tokens=150,                 # limit response length (keeps it short for voice)
        user="pi-home"                  # stable session ID so CHARLI remembers Pi context
    )

    # Extract just the text of CHARLI's answer
    answer = response.choices[0].message.content

    print(f"🤖 CHARLI says: '{answer}'")
    return answer


# ── Test it ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    answer = ask_charli("Hello Charli, can you hear me from the Raspberry Pi?")
    print(f"\nFull response: {answer}")
```

**Test it:**
```bash
python3 src/ask_charli.py
```

You should see CHARLI's response printed. ✅

---

## File 4: `src/speak.py` — Speak CHARLI's Response Out Loud

> Building block 4: takes text and speaks it through the speaker.

```bash
nano ~/charli-home/src/speak.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Building Block 4: Convert text into speech and play it.
We use espeak-ng for now — it sounds a little robotic but it works.
In Phase 4 we'll swap this building block for a better one (Piper TTS).
"""

# subprocess lets Python run other programs (like espeak-ng)
import subprocess


def speak(text: str, language: str = "en"):
    """
    Takes a text string and speaks it out loud through the speaker.
    The language parameter is accepted for API compatibility with Phase 4
    but espeak uses a single voice for now -- upgraded in Phase 4.
    Example: speak("Hello Sir, it is 72 degrees outside.")
    """

    # Remove any markdown formatting that might have slipped through
    # (asterisks, pound signs, backticks — these sound weird when spoken)
    text = text.replace("*", "").replace("#", "").replace("`", "")

    print(f"🔊 Speaking: '{text}'")

    # Run espeak-ng — a text-to-speech program
    # -v en-us+f3  → American English, female voice #3
    # -s 155       → speed (155 words per minute — natural conversation speed)
    # -p 45        → pitch (45 is a natural-sounding pitch)
    subprocess.run(["espeak-ng", "-v", "en-us+f3", "-s", "155", "-p", "45", text])


# ── Test it ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    speak("Hello! I am CHARLI. If you can hear this, the speaker is working perfectly!")
```

**Test it:**
```bash
python3 src/speak.py
```

You should hear the voice through the Bluetooth speaker. ✅

---

## The Main App: `charli_home.py` — Putting the Building Blocks Together

> This is where the magic happens. Instead of rewriting all the code, we IMPORT the building blocks Isabella already wrote. The main app just connects them like LEGO pieces.
>
> **👩‍💻 Isabella: notice how short this file is. That's because you already did the hard work — each building block handles one job. This file just says what order to do things in.**

```bash
nano ~/charli-home/charli_home.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home — Version 0.1
The full voice pipeline:
  Button A → Record → Whisper (speech to text) → CHARLI (AI response) → Speak

This file doesn't do the work itself — it imports the building blocks
from the src/ folder and connects them together like a pipeline.

Team: Christian & Isabella Bermeo
Date: 2026-02-21
"""

import time

# Hardware control for the button
import RPi.GPIO as GPIO

# ── Import our building blocks ────────────────────────────────────────
# Each of these is a file Isabella wrote in the src/ folder.
# We import just the function we need from each one.
from src.record import record_audio          # Step 1: record voice
from src.transcribe import transcribe        # Step 2: voice → text
from src.ask_charli import ask_charli        # Step 3: text → CHARLI's answer
from src.speak import speak                  # Step 4: answer → spoken aloud


# ── Settings ──────────────────────────────────────────────────────────
BUTTON_A = 5   # GPIO pin for Button A on Pirate Audio HAT


# ── Set up the button ─────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# ── Main loop ─────────────────────────────────────────────────────────
print("✅ CHARLI Home is ready! Press Button A to speak.")
print("Waiting for button press... (Ctrl+C to quit)")

try:
    while True:
        # Check if Button A is being pressed (LOW = pressed)
        if GPIO.input(BUTTON_A) == GPIO.LOW:

            # Run the full pipeline — each step uses a building block
            audio_file = record_audio()        # 🎤 Record your voice

            question, language = transcribe(audio_file)  # voice -> text + language

            # Only ask CHARLI if we actually heard something
            if question:
                answer = ask_charli(question, language)  # ask CHARLI in detected language
                speak(answer)                  # 🔊 Speak the answer

            # Wait half a second before checking the button again
            time.sleep(0.5)

        # Check the button every 50ms — fast enough to feel instant
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n👋 CHARLI Home shutting down. Goodbye!")
    GPIO.cleanup()
```

> **See how clean that is?** The main loop is just 4 lines:
> 1. `record_audio()` — record your voice
> 2. `transcribe(audio_file)` — turn it into text
> 3. `ask_charli(question, language)` — ask CHARLI in the detected language
> 4. `speak(answer)` — say the answer out loud
>
> Each building block handles all the complicated stuff inside. That's how real programs are built — small pieces that each do one thing well, connected together.

**Run it:**
```bash
cd ~/charli-home
source .venv/bin/activate
sudo -E python3 charli_home.py
```

> **Why `sudo -E`?** `sudo` runs as admin (needed for GPIO). The `-E` flag passes your environment variables (CHARLI_HOST and CHARLI_TOKEN) to the sudo session so they're available.

**Press Button A → ask Charli something → hear her respond. That's the moment. 🎉**

---

# 📋 PHASE 3: The Display — Wobble Orb + Subtitles

> **Optional for Saturday afternoon** -- only attempt if Phase 2 voice pipeline is fully working.

## `src/display.py`

```bash
nano ~/charli-home/src/display.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Display Engine
Shows a glowing animated orb (top 75%) and subtitle text (bottom 25%).

States:
  idle      → dim blue orb breathing slowly + clock
  listening → bright teal orb wobbling with your voice
  thinking  → orange orb with 4 orbiting dots
  speaking  → gold orb pulsing + Charli's words as subtitles
"""

import math
import time
import threading
import datetime

import pygame
from PIL import Image
from st7789 import ST7789


# ── Display setup ──────────────────────────────────────────────────────
# Connect to the ST7789 display chip on the Pirate Audio HAT
display = ST7789(
    port=0, cs=1, dc=9, backlight=13,
    rotation=90, spi_speed_hz=80_000_000
)
display.begin()

# Screen dimensions
W, H       = 240, 240
ORB_ZONE   = 180   # top 180px for the orb
SUB_ZONE   = 60    # bottom 60px for subtitles
CX, CY     = 120, 90   # center of the orb area
BASE_R     = 55    # base radius of the orb in pixels

# Create a surface to draw on (like a canvas)
pygame.init()
surface = pygame.Surface((W, H))


# ── Shared state ──────────────────────────────────────────────────────
# These variables are changed from outside (by charli_home.py)
# and read inside the render loop.
_state     = "idle"   # current state: idle / listening / thinking / speaking
_subtitle  = ""       # text to show at the bottom
_amplitude = 0.0      # microphone volume 0.0 (silent) to 1.0 (loud)
_frame     = 0        # frame counter for animations

# Colors for each state
STATE_COLORS = {
    "idle":      (20,  40, 160),   # deep blue
    "listening": (0,  200, 180),   # bright teal
    "thinking":  (220, 110,  0),   # orange
    "speaking":  (255, 240, 150),  # warm gold
}


# ── Drawing functions ──────────────────────────────────────────────────

def draw_orb():
    """Draws the animated orb based on the current state."""
    global _frame

    color  = STATE_COLORS.get(_state, (255, 255, 255))

    # Breathing animation — the orb gently grows and shrinks
    # math.sin creates a smooth wave that goes up and down repeatedly
    breath = math.sin(_frame * 0.04) * 8   # ±8 pixels of breathing

    if _state == "idle":
        # Dim, slow breathing orb — like it's sleeping
        dim_color = tuple(int(c * 0.35) for c in color)  # make it dimmer
        r = int(BASE_R + breath)
        pygame.draw.circle(surface, dim_color, (CX, CY), r)

    elif _state == "thinking":
        # Orb with 4 dots orbiting around it
        r = int(BASE_R + breath)
        dim_color = tuple(int(c * 0.5) for c in color)
        pygame.draw.circle(surface, dim_color, (CX, CY), r)

        # Draw 4 orbiting dots evenly spaced (every 90 degrees)
        for i in range(4):
            # _frame * 0.08 makes the dots rotate. 
            # i * (math.pi / 2) spaces them 90 degrees apart.
            angle = _frame * 0.08 + i * (math.pi / 2)
            dot_x = CX + int((r + 20) * math.cos(angle))
            dot_y = CY + int((r + 20) * math.sin(angle))
            pygame.draw.circle(surface, color, (dot_x, dot_y), 7)

    else:
        # Wobble orb — for listening and speaking
        # The edge of the orb distorts based on _amplitude (how loud you're talking)
        if _state == "listening":
            wobble_strength = _amplitude * 24  # wobbles more when louder
        else:
            wobble_strength = _amplitude * 14  # speaking wobbles a little less

        # Build the wobble shape by calculating 80 points around the circle
        points = []
        for i in range(80):
            angle = (i / 80) * 2 * math.pi  # evenly spaced around the circle

            # Add two overlapping sine waves to create organic wobble
            wobble = (
                wobble_strength * math.sin(angle * 5 + _frame * 0.12) +
                wobble_strength * 0.5 * math.sin(angle * 3 - _frame * 0.07)
            )

            r = max(20, BASE_R + breath + wobble)  # never let radius go below 20
            points.append((
                CX + int(r * math.cos(angle)),
                CY + int(r * math.sin(angle))
            ))

        # Draw glow layers (multiple polygons, each slightly dimmer than the last)
        glow_levels = [
            (0.08, 0),    # faint outer glow
            (0.20, 0),    # medium glow
            (0.50, 0),    # inner glow
            (1.00, 0),    # full bright core
        ]
        for alpha, _ in glow_levels:
            glow_color = tuple(min(255, int(c * alpha)) for c in color)
            pygame.draw.polygon(surface, glow_color, points)

    _frame += 1  # advance the animation frame


def draw_subtitle():
    """Draws the subtitle text strip at the bottom of the screen."""
    # Dark background strip for the subtitle area
    pygame.draw.rect(surface, (8, 8, 18), (0, ORB_ZONE, W, SUB_ZONE))

    if not _subtitle:
        return

    font = pygame.font.SysFont("monospace", 13)

    # Word-wrap: split the subtitle into lines that fit the screen width
    words = _subtitle.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = (current_line + " " + word).strip()
        if font.size(test_line)[0] <= W - 16:  # fits within screen width
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Only show the last 2 lines (to fit in the subtitle zone)
    lines = lines[-2:]

    # Draw each line of text
    y = ORB_ZONE + 8
    for line in lines:
        text_surface = font.render(line, True, (210, 210, 210))
        surface.blit(text_surface, (8, y))
        y += 18


def draw_clock():
    """Draws the current time in the subtitle zone during idle state."""
    pygame.draw.rect(surface, (8, 8, 18), (0, ORB_ZONE, W, SUB_ZONE))
    now = datetime.datetime.now().strftime("%I:%M %p")
    font = pygame.font.SysFont("monospace", 14)
    text_surface = font.render(now, True, (60, 60, 100))
    x = W // 2 - text_surface.get_width() // 2
    surface.blit(text_surface, (x, ORB_ZONE + 8))


def push_to_display():
    """Sends the current surface image to the physical display."""
    raw_bytes = pygame.image.tostring(surface, "RGB")
    image = Image.frombytes("RGB", (W, H), raw_bytes)
    display.display(image)


# ── Render loop ───────────────────────────────────────────────────────

def render_loop():
    """Runs continuously in the background, updating the display 30 times per second."""
    while True:
        # Clear the screen to a very dark background
        surface.fill((4, 4, 16))

        # Draw the orb
        draw_orb()

        # Draw subtitle or clock depending on state
        if _state == "idle":
            draw_clock()
        else:
            draw_subtitle()

        # Push our drawing to the actual display
        push_to_display()

        # Wait 1/30th of a second before drawing the next frame (30 fps)
        time.sleep(1 / 30)


# ── Public API — used by charli_home.py ──────────────────────────────

def set_state(new_state: str, text: str = ""):
    """Change the display state. Call this from the main pipeline."""
    global _state, _subtitle
    _state    = new_state
    _subtitle = text


def set_amplitude(amp: float):
    """Update the microphone amplitude for wobble animation (0.0 to 1.0)."""
    global _amplitude
    _amplitude = max(0.0, min(1.0, amp))


def start():
    """Start the display render loop in the background."""
    t = threading.Thread(target=render_loop, daemon=True)
    t.start()
    print("✅ Display started")
```

## Updating `charli_home.py` to Use the Display

> We just add one more building block import and wrap each pipeline step with display state changes. The main app stays clean and readable.

Replace `charli_home.py` with this updated version:

```bash
nano ~/charli-home/charli_home.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home — Version 0.2 (with display)
  Button A → Record → Whisper → CHARLI → Speak
  + Wobble Orb display shows what's happening at each step

Team: Christian & Isabella Bermeo
Date: 2026-02-21
"""

import time
import RPi.GPIO as GPIO

# ── Import our building blocks ────────────────────────────────────────
from src.record import record_audio
from src.transcribe import transcribe
from src.ask_charli import ask_charli
from src.speak import speak
from src.display import set_state, start as start_display   # NEW building block


# ── Settings ──────────────────────────────────────────────────────────
BUTTON_A = 5

# ── Set up ────────────────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
start_display()

# ── Main loop ─────────────────────────────────────────────────────────
print("✅ CHARLI Home is ready! Press Button A to speak.")
set_state("idle")

try:
    while True:
        if GPIO.input(BUTTON_A) == GPIO.LOW:

            set_state("listening", "Listening...")
            audio_file = record_audio()

            set_state("thinking", "Thinking...")
            question, language = transcribe(audio_file)

            if question:
                set_state("thinking", question)
                answer = ask_charli(question, language)

                set_state("speaking", answer)
                speak(answer)

            set_state("idle")
            time.sleep(0.5)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n👋 CHARLI Home shutting down. Goodbye!")
    GPIO.cleanup()
```

> **See what happened?** We added ONE new import (`from src.display import ...`) and wrapped each step with `set_state()`. The display building block handles all the animation, orb drawing, and subtitle rendering. The main app just tells it what state we're in. That's the power of building blocks.

---

# 📋 PHASE 4: Natural Voice with Piper TTS

> Upgrade from the robotic espeak voice to something that sounds much more natural.
> We do this by replacing the `speak.py` building block — the main app doesn't change at all!

### Step 4.1 — Install Piper and Download a Voice

```bash
cd ~/charli-home
source .venv/bin/activate

pip install piper-tts

mkdir -p ~/charli-home/voices
cd ~/charli-home/voices

# English: Alan -- British male voice (clean, JARVIS-style)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json

# Spanish: mls_10246 -- Castilian Spanish male (elegant)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/low/es_ES-mls_10246-low.onnx.json
```

### Step 4.2 — Update the `src/speak.py` Building Block

> We're replacing the old building block with a better one. Since `charli_home.py` just calls `speak(text)`, we only need to change what happens inside — the main app stays exactly the same.

```bash
nano ~/charli-home/src/speak.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Building Block 4: Convert text into speech and play it.
UPGRADED in Phase 4: now uses Piper TTS for a natural-sounding voice.

The function name is still speak(text) — same interface, better voice.
charli_home.py doesn't need to change at all!
"""

import subprocess


def speak(text: str):
    """
    Takes a text string and speaks it out loud through the speaker.
    Uses Piper TTS with the Alan (British male) voice model.
    """

    # Remove any markdown formatting that might have slipped through
    text = text.replace("*", "").replace("#", "").replace("`", "")

    print(f"🔊 Speaking: '{text}'")

    # Pipe the text through Piper TTS → raw audio → paplay (the audio player)
    subprocess.run(
        f'echo "{text}" | '
        f'piper --model ~/charli-home/voices/en_GB-alan-medium.onnx --output_raw | '
        f'paplay --raw --rate=22050 --format=s16le --channels=1',
        shell=True
    )


# ── Test it ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    speak("Hello! I am CHARLI. This is my new natural voice. Much better, right?")
```

**Test it:**
```bash
python3 src/speak.py
```

> **👩‍💻 Isabella: notice that we ONLY changed `src/speak.py` — the main app `charli_home.py` didn't change at all! That's the beauty of building blocks: you can swap one piece for a better version without touching the rest of the program.**

---

# 📋 PHASE 5: Wake Word "Hey Charli"

> Instead of pressing a button, just say "Hey Charli" and she wakes up.
> We use **Picovoice Porcupine** -- no recording yourself 50 times, no training required.
> You type the wake word on their website, download one file, and it just works.

### Step 5.0 -- Create Your Wake Words (5 minutes, done once)

> We're using TWO wake words: **"Hey Charli"** and **"Charli"**.
> Both will trigger the assistant. Porcupine free tier supports up to 3 simultaneously.

1. Go to **https://console.picovoice.ai** and create a free account
2. Click **Wake Word** -> **Create Custom Wake Word**
3. Create the first wake word: `hey charli` -- download as `hey-charli_raspberry-pi.ppn`
4. Create the second wake word: `charli` -- download as `charli_raspberry-pi.ppn`
5. Select platform: **Raspberry Pi** for both
6. Copy both files to the Pi:
   ```bash
   scp ~/Downloads/hey-charli_raspberry-pi.ppn charli@charli-home.local:~/charli-home/
   scp ~/Downloads/charli_raspberry-pi.ppn charli@charli-home.local:~/charli-home/
   ```
7. In your Picovoice Console, copy your **Access Key** -- you'll need it below.

### Step 5.1 -- Install Porcupine Libraries

> Porcupine includes `pvrecorder` -- its own audio capture library.
> No `pyaudio` needed. One less dependency to install.

```bash
cd ~/charli-home
source .venv/bin/activate
pip install pvporcupine pvrecorder
```

### Step 5.2 -- Write the Wake Word Building Block

```bash
nano ~/charli-home/src/wakeword.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Building Block 5: Wake word detection.
Uses Picovoice Porcupine to listen for "Hey Charli".

No training required. Download the .ppn file from console.picovoice.ai
and paste your access key below. That's it.
"""

import pvporcupine
import pvrecorder

# ---- Configuration -------------------------------------------------------
# Paste your Picovoice Access Key here (from console.picovoice.ai)
ACCESS_KEY = "paste-your-access-key-here"

# Both wake word files -- either phrase wakes the assistant
KEYWORD_PATHS = [
    "/home/charli/charli-home/hey-charli_raspberry-pi.ppn",  # "Hey Charli"
    "/home/charli/charli-home/charli_raspberry-pi.ppn",      # "Charli"
]
KEYWORD_LABELS = ["Hey Charli", "Charli"]


# ---- Initialize Porcupine ------------------------------------------------
porcupine = pvporcupine.create(
    access_key=ACCESS_KEY,
    keyword_paths=KEYWORD_PATHS
)

# pvrecorder captures audio at the correct frame size
recorder = pvrecorder.PvRecorder(frame_length=porcupine.frame_length)


def wait_for_wakeword():
    """
    Listens until "Hey Charli" OR "Charli" is detected, then returns.
    Either phrase wakes the assistant.
    """

    print("👂 Listening for 'Charli' or 'Hey Charli'...")
    recorder.start()

    try:
        while True:
            pcm = recorder.read()
            # -1 = no wake word; >= 0 = index of detected keyword
            result = porcupine.process(pcm)
            if result >= 0:
                label = KEYWORD_LABELS[result]
                print(f"🎯 '{label}' detected!")
                return
    finally:
        recorder.stop()


# ---- Test it -------------------------------------------------------------
if __name__ == "__main__":
    print("Say 'Charli' or 'Hey Charli'...")
    wait_for_wakeword()
    print("Wake word detected!")
```

**Test it:**
```bash
python3 src/wakeword.py
```

Say "Charli" or "Hey Charli" -- you should see which one was detected. Done. ✅

### Step 5.3 -- Update `charli_home.py` to Use Wake Word

```bash
nano ~/charli-home/charli_home.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home -- Version 0.3 (with wake word)
  Say "Hey Charli" -> Record -> Whisper -> CHARLI -> Speak -> Display

Team: Christian & Isabella Bermeo
"""

# ---- Import our building blocks ------------------------------------------
from src.record import record_audio
from src.transcribe import transcribe
from src.ask_charli import ask_charli
from src.speak import speak
from src.display import set_state, start as start_display
from src.wakeword import wait_for_wakeword   # NEW


# ---- Set up --------------------------------------------------------------
start_display()

# ---- Main loop -----------------------------------------------------------
print("✅ CHARLI Home is ready! Say 'Hey Charli' to wake her up.")

try:
    while True:
        set_state("idle")
        wait_for_wakeword()                    # Listen for wake word

        set_state("listening", "Listening...")
        audio_file = record_audio()            # Record voice

        set_state("thinking", "Thinking...")
        question, language = transcribe(audio_file)      # voice -> text + language

        if question:
            set_state("thinking", question)
            answer = ask_charli(question, language)      # ask in detected language

            set_state("speaking", answer)
            speak(answer)                      # Speak the answer

except KeyboardInterrupt:
    print("\n👋 CHARLI Home shutting down. Goodbye!")
```

> **Note:** We removed `import RPi.GPIO` entirely -- Porcupine handles its own audio capture, so no GPIO button setup needed anymore. Simpler.

# 🗃️ Final File Structure

```
charli-home/
├── README.md               <- this file
├── charli_home.py          <- main app -- imports and connects the building blocks
├── hey-charli_raspberry-pi.ppn  <- wake word 1 (picovoice.ai)
├── charli_raspberry-pi.ppn       <- wake word 2 (picovoice.ai)
├── .venv/                  <- Python virtual environment
├── voices/                 <- Piper TTS voice models (Phase 4)
│   ├── en_GB-alan-medium.onnx          <- English: British male (JARVIS-style)
│   ├── en_GB-alan-medium.onnx.json
│   ├── es_ES-mls_10246-low.onnx        <- Spanish: Castilian male (elegant)
│   └── es_ES-mls_10246-low.onnx.json
└── src/                    <- the building blocks (each does ONE thing)
    ├── record.py           <- records audio from the mic
    ├── transcribe.py       <- converts audio to text (Whisper)
    ├── ask_charli.py       <- sends question to CHARLI, gets answer
    ├── speak.py            <- speaks text out loud (espeak -> Piper)
    ├── display.py          <- Wobble Orb + subtitles (Phase 3)
    └── wakeword.py         <- listens for "Hey Charli" (Porcupine, Phase 5)
```

---

# 🐛 Troubleshooting

| Problem | What to try |
|---------|-------------|
| `ssh: charli-home.local not found` | Use IP address instead: `ssh charli@192.168.X.X` |
| Pi won't boot from NVMe | Make sure NVMe is fully seated in the PCIe slot. Try re-seating it. |
| `arecord` shows no devices | Go back to Step 1.2 and enable I2S in raspi-config |
| No sound from speaker | Re-pair Bluetooth. Also try: `espeak-ng "test"` directly. |
| `CHARLI_HOST: unbound variable` | Run `source ~/.bashrc` then try again |
| Error 401 Unauthorized | Your CHARLI_TOKEN is wrong. Re-check it from the Mac Mini. |
| Whisper model slow first run | It's downloading 145MB. Wait for it — only happens once. |
| Display stays black | Enable SPI in raspi-config (Step 1.2). Also check HAT is seated. |
| `sudo: .venv not found` | Use `sudo -E python3` (the -E passes your venv environment to sudo) |

---

# ☑️ Saturday Build Day Checklist

### Phase 0 — Setup
- [ ] 32GB microSD flashed with Raspberry Pi OS
- [ ] Active Cooler installed on the Pi 5 CPU
- [ ] Pi 5 boots from microSD
- [ ] EEPROM bootloader updated (`sudo rpi-eeprom-update -a`)
- [ ] M.2 HAT+ installed with NVMe SSD + GPIO header extender
- [ ] NVMe SSD cloned and Pi boots from it
- [ ] SSH working from Mac: `ssh charli@charli-home.local`
- [ ] System tools installed (git, espeak-ng, libportaudio2...)
- [ ] Tailscale on Pi: installed and authenticated
- [ ] Tailscale on Mac Mini: running
- [ ] Both devices visible with `tailscale status` ✅

### Phase 1 — Hardware
- [ ] SPI and I2C enabled in raspi-config
- [ ] Pirate Audio HAT physically seated on GPIO
- [ ] Pirate Audio drivers installed and rebooted
- [ ] `arecord` test — voice captured ✅
- [ ] Bluetooth speaker paired and `espeak-ng` plays through it ✅

### Phase 2 — Voice Pipeline
- [ ] Python venv created: `python3 -m venv .venv`
- [ ] All packages installed (sounddevice, whisper, openai, RPi.GPIO, pygame...)
- [ ] `CHARLI_HOST` and `CHARLI_TOKEN` set in `.bashrc`
- [ ] Gateway connection test with `curl` passes ✅
- [ ] `src/record.py` written by Isabella ✏️ → button recording works
- [ ] `src/transcribe.py` → Whisper transcribes correctly
- [ ] `src/ask_charli.py` → CHARLI responds
- [ ] `src/speak.py` → audio plays through Bluetooth speaker
- [ ] `charli_home.py` full loop: **button → question → CHARLI answers** 🎉🎉🎉

### Phase 3 — Display (if time allows)
- [ ] `src/display.py` created and tested
- [ ] Orb changes color based on state (idle / listening / thinking / speaking)
- [ ] Subtitles appear at bottom of screen

### Phase 4 — Natural Voice (if time allows)
- [ ] `pip install piper-tts` installed
- [ ] Alan (British male) voice downloaded: `en_GB-alan-medium.onnx`
- [ ] Spanish voice downloaded: `es_ES-mls_10246-low.onnx`
- [ ] `src/speak.py` upgraded to Piper -- test both voices

### Phase 5 — Wake Word (if time allows)
- [ ] Picovoice account created at console.picovoice.ai
- [ ] "hey charli" wake word created and `.ppn` file downloaded
- [ ] "charli" wake word created and `.ppn` file downloaded
- [ ] Both `.ppn` files copied to the Pi
- [ ] `pip install pvporcupine pvrecorder`
- [ ] Access key configured in `src/wakeword.py`
- [ ] Wake word test: say "Charli" → terminal confirms detection ✅
- [ ] `charli_home.py` Phase 5 version running: **say "Charli" → CHARLI answers** 🎉

### Pre-Saturday Prep (do the night before)
- [ ] Download both `.ppn` files from console.picovoice.ai
- [ ] Download Piper voice models (`en_GB-alan-medium.onnx`, `es_ES-mls_10246-low.onnx`)
- [ ] Confirm Tailscale is running on Mac Mini
- [ ] Confirm OpenClaw gateway is running on Mac Mini
- [ ] Charge the Bluetooth speaker
- [ ] Have keyboard + mouse + monitor ready for first boot

---

*The moment Isabella presses the button, asks Charli something, and hears Charli answer -- that's the moment everything clicks. That's what we're building toward.*

*-- CHARLI, 2026*
