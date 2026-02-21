# Project 1: CHARLI Home 🏠🤖
*A JARVIS-style voice assistant — powered by the real CHARLI*

**Status:** In Progress
**Started:** 2026-02-21
**Team:** Christian Bermeo + Isabella Bermeo 🎨
**Hardware:** Raspberry Pi 5 8GB · Pirate Audio Dual Mic HAT · Bluetooth Speaker · 256GB NVMe SSD

---

## 🎯 What We're Building

A home voice assistant. You press a button → say something → Charli listens, thinks, and answers out loud through the speaker. The display shows a glowing animated orb that reacts to your voice, plus the text of what Charli said.

This isn't a generic AI — it's the actual CHARLI who knows Sir, Madam, and the whole family. The Pi is just the ears, mouth, and display. The brain lives on the Mac Mini.

```
[Press Button A]
       ↓
[Pirate Audio mics record your voice]
       ↓
[Whisper turns speech into text — runs ON the Pi]
       ↓
[Text sent to Mac Mini → OpenClaw → Real CHARLI responds]
       ↓
[Response spoken aloud + shown on display]
```

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
| 256GB NVMe SSD Kit | Our boot drive — faster than microSD |
| Pirate Audio Dual Mic HAT | Microphones + color display |
| Bluetooth Speaker | Charli's voice |
| 32GB microSD | Used ONLY for the very first boot (see Phase 0) |
| Keyboard + Mouse + Monitor | Only needed for first boot setup |

---

## 🗓️ What We Build Each Sunday

| Phase | Goal | When |
|-------|------|------|
| 0 | Turn on the Pi for the first time + set up Tailscale | Sunday 1 |
| 1 | Get the microphone HAT and Bluetooth speaker working | Sunday 1 |
| 2 | **Isabella writes the code** — button makes Charli talk back 🎉 | Sunday 1 (the big goal) |
| 3 | Add the Wobble Orb display + subtitles | Sunday 2 |
| 4 | Upgrade to a more natural voice (Piper TTS) | Sunday 2 |
| 5 | Wake word — just say "Charli" to wake her up | Sunday 3 |
| 6 | Smart home buttons trigger automations | Sunday 4+ |

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

## Step 0.2 — First Boot from microSD

1. Insert the microSD into the Pi 5 (slot is on the underside)
2. Connect the monitor, keyboard, and mouse to the Pi
3. Plug in power — the Pi will boot!
4. **👩‍💻 Isabella: watch it boot for the first time** 🎉
5. Go through the setup wizard (you can skip installing updates for now)

## Step 0.3 — Update the Pi's Bootloader

> This tells the Pi how to boot from the NVMe SSD. Run this before we move over.

```bash
# Open a Terminal on the Pi (or SSH in from Mac)
sudo apt update
sudo rpi-eeprom-update -a
sudo reboot
```

## Step 0.4 — Move the OS to the NVMe SSD

> The Pi 5 has a special slot (PCIe) that the NVMe SSD plugs into. It's much faster than microSD.

1. Make sure the Pi is powered off: `sudo shutdown now`
2. Seat the NVMe SSD into the PCIe adapter from the kit, then plug it into the Pi 5's M.2 slot
3. Power the Pi back on (it will still boot from microSD for now)
4. Open a Terminal and run the Pi's built-in SD Card Copier:

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

5. Shut down: `sudo shutdown now`
6. Remove the microSD card
7. Power on — Pi now boots from the 256GB NVMe SSD ✅

## Step 0.5 — SSH In From the Mac

> After this step, we won't need the monitor/keyboard/mouse anymore. We work from the Mac.

```bash
# On your Mac, open Terminal and type:
ssh charli@charli-home.local
# Enter the password you set in Step 0.1
```

If that doesn't work, find the Pi's IP address on your router and try:
```bash
ssh charli@192.168.X.X
```

**👩‍💻 Isabella: you type the SSH command. You're logging into the Pi remotely!**

## Step 0.6 — Install Essential Tools

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

> The HAT plugs onto the 40 metal pins (the GPIO header) on the Pi 5.

1. **Shut down the Pi first!** Never add hardware while powered on.
   ```bash
   sudo shutdown now
   ```
2. Unplug the power cable
3. Align the Pirate Audio Dual Mic HAT over the GPIO pins — the HAT has a matching socket underneath
4. Press down firmly and evenly until it's fully seated
5. Power the Pi back on

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

```bash
# Show available audio recording devices — should list the Pirate Audio HAT
arecord -l

# Record 5 seconds of audio
arecord -D hw:0,0 -f S16_LE -r 16000 -c 1 -d 5 /tmp/mic_test.wav

# Play it back to confirm the mic captured something
aplay /tmp/mic_test.wav
```

**👩‍💻 Isabella: talk into the mic while it records. Then listen to hear yourself played back!**

If you don't hear anything, try `hw:1,0` instead of `hw:0,0`.

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

# GPIO — lets Python control the Pi's buttons
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

```bash
nano ~/charli-home/src/record.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Step 1: Listen for a button press and record audio.
Written by: Isabella Bermeo 🎨
"""

# We need to import (load) tools that other people already wrote.
# RPi.GPIO lets us detect button presses on the Pi.
import RPi.GPIO as GPIO

# sounddevice records audio from the microphone.
import sounddevice as sd

# soundfile saves the recorded audio to a file.
import soundfile as sf

# time lets us pause the program for a moment (to avoid double-presses).
import time


# ── Settings ──────────────────────────────────────────────────────────
# Which GPIO pin is Button A connected to on the Pirate Audio HAT?
BUTTON_A = 5

# How many audio samples per second? 16000 is great quality for voice.
SAMPLE_RATE = 16000

# How many seconds to record when the button is pressed.
DURATION = 5

# Where to save the audio file.
OUTPUT_FILE = "/tmp/charli_recording.wav"


# ── Set up the button ──────────────────────────────────────────────────
# Tell the Pi to use "BCM" pin numbering (the numbers printed on diagrams).
GPIO.setmode(GPIO.BCM)

# Set up Button A as an input pin.
# PUD_UP means it reads HIGH normally and goes LOW when pressed.
GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)


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


# ── Main loop ─────────────────────────────────────────────────────────
print("CHARLI Home — Recording Test")
print("Press Button A to record 5 seconds...")
print("Press Ctrl+C to quit")

try:
    while True:
        # GPIO.LOW means the button is being pressed
        if GPIO.input(BUTTON_A) == GPIO.LOW:
            record_audio()

            # Wait half a second so one press doesn't trigger twice
            time.sleep(0.5)

        # Small pause so we're not checking the button millions of times per second
        time.sleep(0.05)

except KeyboardInterrupt:
    # When you press Ctrl+C, clean up the GPIO pins before quitting
    print("\nGoodbye!")
    GPIO.cleanup()
```

**Run it:**
```bash
cd ~/charli-home
source .venv/bin/activate
sudo python3 src/record.py
```

> **Why `sudo`?** GPIO access requires administrator permission on the Pi.

Press Button A, say something, and confirm you see "✅ Saved". ✅

---

## File 2: `src/transcribe.py` — Convert Audio to Text

```bash
nano ~/charli-home/src/transcribe.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Step 2: Convert the recorded audio into text using Whisper.
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
def transcribe(audio_path: str) -> str:
    """
    Takes the path to an audio file and returns the text of what was said.
    Example: transcribe("/tmp/charli_recording.wav") → "What is the weather?"
    """

    print(f"📝 Listening to {audio_path}...")

    # Ask Whisper to transcribe the audio file
    # language="en" tells it we're speaking English (faster + more accurate)
    result = model.transcribe(audio_path, language="en")

    # Pull out just the text from the result
    text = result["text"].strip()

    print(f"💬 You said: '{text}'")
    return text


# ── Test it ───────────────────────────────────────────────────────────
# This only runs if you run this file directly (not when imported by another file)
if __name__ == "__main__":
    transcribe("/tmp/charli_recording.wav")
```

**Test it** (after recording something with record.py):
```bash
sudo python3 src/transcribe.py
```

You should see your words printed as text. ✅

---

## File 3: `src/ask_charli.py` — Ask the Real CHARLI

```bash
nano ~/charli-home/src/ask_charli.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Step 3: Send a question to CHARLI and get her response.

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
- All family protocols and boundaries apply as always."""


# ── The ask function ──────────────────────────────────────────────────
def ask_charli(question: str) -> str:
    """
    Sends a question to CHARLI and returns her response as text.
    Example: ask_charli("What's the weather?") → "It's 45 degrees and cloudy in New York."
    """

    print(f"🤔 Asking CHARLI: '{question}'")

    # Send the question to the OpenClaw gateway
    response = client.chat.completions.create(
        model="openclaw:main",          # routes to the real CHARLI session
        messages=[
            {"role": "system", "content": PI_SYSTEM_PROMPT},  # her instructions
            {"role": "user",   "content": question}           # our question
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
sudo python3 src/ask_charli.py
```

You should see CHARLI's response printed. ✅

---

## File 4: `src/speak.py` — Speak CHARLI's Response Out Loud

```bash
nano ~/charli-home/src/speak.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home - Step 4: Convert CHARLI's text response into speech and play it.
We use espeak-ng for now — it sounds a little robotic but it works.
In Phase 4 we'll upgrade to Piper which sounds much more natural.
"""

# subprocess lets Python run other programs (like espeak-ng)
import subprocess


def speak(text: str):
    """
    Takes a text string and speaks it out loud through the speaker.
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
sudo python3 src/speak.py
```

You should hear the voice through the Bluetooth speaker. ✅

---

## The Main App: `charli_home.py` — Putting It All Together

> This is the file that ties everything together. When it runs, CHARLI Home is live.

```bash
nano ~/charli-home/charli_home.py
```

```python
#!/usr/bin/env python3
"""
CHARLI Home — Version 0.1
The full voice pipeline:
  Button A → Record → Whisper (speech to text) → CHARLI (AI response) → Speak

Team: Christian & Isabella Bermeo
Date: 2026-02-21
"""

# Standard Python tools
import os
import time
import subprocess

# Hardware control
import RPi.GPIO as GPIO

# Audio recording
import sounddevice as sd
import soundfile as sf

# Speech-to-text AI
import whisper

# CHARLI's API client
from openai import OpenAI


# ── Settings ──────────────────────────────────────────────────────────
BUTTON_A    = 5                           # GPIO pin for Button A on Pirate Audio HAT
SAMPLE_RATE = 16000                       # 16kHz — good quality for voice recording
DURATION    = 5                           # record for 5 seconds after button press
TEMP_AUDIO  = "/tmp/charli_recording.wav" # temporary file for the recording


# ── Connect to CHARLI on the Mac Mini ─────────────────────────────────
# These were set in .bashrc — if they're missing, the program will crash here
# with a clear error telling you to set them.
charli_host  = os.environ["CHARLI_HOST"]
charli_token = os.environ["CHARLI_TOKEN"]

client = OpenAI(
    base_url=f"{charli_host}/v1",
    api_key=charli_token
)

PI_PROMPT = """You respond through the CHARLI Home Raspberry Pi voice assistant.
Answer in 1 to 3 sentences only. No lists, no markdown, no asterisks.
Speak naturally — your answer will be read aloud through a speaker.
You know Sir (Christian), Madam (Dominica), Isabella, and the whole family.
Always apply family protocol and keep responses appropriate for all ages."""


# ── Set up the button ──────────────────────────────────────────────────
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# ── Load Whisper model ────────────────────────────────────────────────
print("Loading Whisper AI model... (this takes about 30 seconds the first time)")
stt_model = whisper.load_model("base")
print("✅ CHARLI Home is ready! Press Button A to speak.")


# ── Pipeline functions ────────────────────────────────────────────────

def record():
    """Records 5 seconds of audio from the microphone."""
    print("🎤 Recording...")
    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='int16'
    )
    sd.wait()  # wait until recording finishes
    sf.write(TEMP_AUDIO, audio, SAMPLE_RATE)
    print("✅ Done recording")


def transcribe():
    """Converts the recorded audio file into text using Whisper."""
    result = stt_model.transcribe(TEMP_AUDIO, language="en")
    text = result["text"].strip()
    print(f"💬 You said: '{text}'")
    return text


def ask(question: str) -> str:
    """Sends the transcribed question to CHARLI and returns her answer."""
    print("🤔 Asking CHARLI...")
    response = client.chat.completions.create(
        model="openclaw:main",
        messages=[
            {"role": "system", "content": PI_PROMPT},
            {"role": "user",   "content": question}
        ],
        max_tokens=150,
        user="pi-home"
    )
    answer = response.choices[0].message.content
    print(f"🤖 CHARLI: '{answer}'")
    return answer


def speak(text: str):
    """Speaks CHARLI's response out loud through the speaker."""
    text = text.replace("*", "").replace("#", "").replace("`", "")
    subprocess.run(["espeak-ng", "-v", "en-us+f3", "-s", "155", "-p", "45", text])


# ── Main loop ─────────────────────────────────────────────────────────
# This loop runs forever until you press Ctrl+C
print("Waiting for button press... (Ctrl+C to quit)")

try:
    while True:
        # Check if Button A is being pressed (LOW = pressed)
        if GPIO.input(BUTTON_A) == GPIO.LOW:

            # Run the full pipeline
            record()

            question = transcribe()

            # Only ask CHARLI if we actually heard something
            if question:
                answer = ask(question)
                speak(answer)

            # Wait half a second before checking the button again
            # (prevents one press from triggering multiple times)
            time.sleep(0.5)

        # Check the button every 50ms — fast enough to feel instant
        time.sleep(0.05)

except KeyboardInterrupt:
    # Clean up the GPIO when you quit with Ctrl+C
    print("\n👋 CHARLI Home shutting down. Goodbye!")
    GPIO.cleanup()
```

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

> This comes in Sunday Session 2. Phase 2 must be fully working first.

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

## Updating `charli_home.py` to Use the Display (Phase 3 addition)

Add these lines to `charli_home.py` when you're ready for the display:

```python
# Add this import near the top
from src.display import set_state, start as display_start

# Add this near startup (after GPIO setup)
display_start()

# Then wrap each pipeline step:
set_state("listening", "Listening...")
record()

question = transcribe()

set_state("thinking", question)
answer = ask(question)

set_state("speaking", answer)
speak(answer)

set_state("idle")
```

---

# 📋 PHASE 4: Natural Voice with Piper TTS

> Upgrade from the robotic espeak voice to something that sounds much more natural.

```bash
pip install piper-tts

mkdir -p ~/charli-home/voices
cd ~/charli-home/voices

# Download the voice model (Amy — natural US English female voice)
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json
```

Replace the `speak()` function in `charli_home.py` with:

```python
def speak(text: str):
    """Speaks using Piper TTS — much more natural voice than espeak."""
    text = text.replace("*", "").replace("#", "").replace("`", "")
    subprocess.run(
        f'echo "{text}" | '
        f'piper --model ~/charli-home/voices/en_US-amy-medium.onnx --output_raw | '
        f'paplay --raw --rate=22050 --format=s16le --channels=1',
        shell=True
    )
```

---

# 📋 PHASE 5: Wake Word "Charli"

> Instead of pressing a button, just say "Charli" and she wakes up.

```bash
pip install openwakeword pyaudio
```

```python
#!/usr/bin/env python3
"""
Phase 5: Wake word detection
Instead of pressing a button, the Pi always listens for the word "Charli".
When it hears it, it runs the full voice pipeline automatically.
"""
from openwakeword.model import Model
import pyaudio
import numpy as np

# Load a wake word model (we'll train a custom "Charli" model in the future)
oww_model = Model(wakeword_models=["hey_jarvis"])  # placeholder

def listen_for_wakeword():
    """Streams audio from the mic and waits until the wake word is detected."""
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        frames_per_buffer=1280
    )

    print("👂 Listening for 'Charli'...")
    set_state("idle")

    while True:
        # Read a small chunk of audio
        raw_audio = stream.read(1280, exception_on_overflow=False)
        audio_chunk = np.frombuffer(raw_audio, dtype=np.int16)

        # Check if the wake word was detected
        predictions = oww_model.predict(audio_chunk)
        if any(confidence > 0.7 for confidence in predictions.values()):
            print("🎯 Wake word 'Charli' detected!")
            stream.stop_stream()
            pa.terminate()
            return  # Hand off to the recording pipeline
```

**Training a custom "Charli" wake word — Isabella's Phase 5 project:**
1. Record 50 samples of you saying "Charli" in different ways (tired, excited, normal)
2. Isabella records 50 samples of her saying "Charli"
3. Madam records 50 samples
4. Upload to openWakeWord trainer
5. The model now recognizes all three voices saying "Charli"

Isabella literally trains an AI model with her own voice. 🎤

---

# 🗃️ Final File Structure

```
charli-home/
├── README.md               ← this file
├── charli_home.py          ← main app (run this)
├── .venv/                  ← Python virtual environment
├── voices/                 ← Piper TTS voice models (Phase 4)
│   ├── en_US-amy-medium.onnx
│   └── en_US-amy-medium.onnx.json
└── src/
    ├── record.py           ← Isabella's first script 🎨
    ├── transcribe.py       ← Whisper speech-to-text
    ├── ask_charli.py       ← talks to real CHARLI via OpenClaw
    ├── speak.py            ← text-to-speech output
    └── display.py          ← Wobble Orb + subtitles (Phase 3)
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

# ☑️ Sunday Session Checklist

### Phase 0 — Setup
- [ ] 32GB microSD flashed with Raspberry Pi OS
- [ ] Pi 5 boots from microSD
- [ ] EEPROM bootloader updated (`sudo rpi-eeprom-update -a`)
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

---

*The moment Isabella presses the button, asks Charli something, and hears Charli answer — that's the moment everything clicks. That's what we're building toward.*

*— CHARLI, 2026*
