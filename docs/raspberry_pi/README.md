# Raspberry Pi Journey

So here is where we are Feb 2026. I have 0 experience with Raspberry Pi's and i just bought a bunch of Raspberry Pi stuff (went a little oberboard because i got excited). As you already know I am a software engineer and i work building fullstack web applications using typescript and node with all our infrastructure running on AWS. I have very little experience with python but i can read basic syntax and understand logic. I also have good experience with basic C++. I enjoy C++ a lot actually. I love programming and I have always been fascinated by space, robotics and AI. I hope to build really cool shit for a living. I need to learn more hardware stuff embedded systems and experience more base level programming.

Also my oldest daughter is 11 and is showing some interest in programming. I hope to have her "help" me with some of these projects to build and learn together. I hope to inspire her and see if I spark some interest in her. She is super excited about how I am building you (CHARLI) and wants to be involved.

**C.H.A.R.L.I.** Not only will you assist me on building cool Raspberry Pi projects but we will be building extensions of you to run on the Raspberry Pi like a "Google Home" like device with a tablet interfaces and automation projects we can triggrer through our n8n instance or via api. all projects we work on should exist in this directory `~raspberry_pi`.

## Motivation

The biggest reason I was impulsed to buy NOW was because I got to build CHARLI. I want to create a "Google home" like device but with CHARLI embedded in it so I can just say "Charli, what is the weather like today?" and you respond with the weather. I want to be able to build an interface like a tablet application with buttons that can trigger stuff and a ready to go TUI that i can interact with you on the go. or on the desk. A display that can show me information about my environment and the world around me. Maybe a mini clawdbot to be in the house and do something.

The goal. Learn & Experiment with important concepts of robotics and embedded systems while building cool gadgets with my daughter.

Nooooww drumroll please...

## INVENTORY:

| **Item** | **Quantity** | **Purpose** |
|---|---|---|
| Raspberry Pi 5 8GB RAM | 1 | Main processing unit |
| Raspberry Pi Camera Module 3 Wide | 1 | Camera projects |
| Raspberry Pi AI HAT+ 13 TOPS | 1 | AI projects |
| Raspberry Pi Active Cooler | 1 | Cooling for AI HAT+ |
| Raspberry Pi SSD Kit 256GB NVMe | 1 | Storage for Raspberry Pi 5 |
| Raspberry Pi 7" Touchscreen Display | 1 | Display and touch interface for projects |
| Raspberry Pi Zero 2 W | 2 | IoT projects |
| Adafruit 135x240 Color Mini PiTFT | 2 | Small color display for projects |
| Adafruit 128x64 OLED Bonnet | 1 | Small OLED display with joystick and 2 buttons |
| Raspberry Pi Pico Breadboard Kit Plus w/ Capactive Touch Display | 2 | Microcontroller projects? |
| Raspberry Pi Pico H | 1 | Microcontroller projects? |
| Raspberry Pi Pico 2WH | 2 | Microcontroller projects? |
| Raspberry Pi Pico MicroPython Programing Sensor Kit | 1 | Assortment of sensors, LEDs, buttons, potentiometers, servos, etc. |

## Accessories

| **Item** | **Quantity** | **Purpose** |
|---|---|---|
| Raspberry Pi 27W USB-C Power Supply | 1 | Power supply for Raspberry Pi 5 |
| Raspberry Pi Mouse | 1 | Mouse for Raspberry Pi 5 |
| Raspberry Pi Keyboard | 1 | Keyboard for Raspberry Pi 5 |
| Raspberry Pi Case | 1 | Case for Raspberry Pi 5 |
| Raspberry Pi MicroSD Card 32GB | 1 | MicroSD card for Raspberry Pi 5 |
| GPIO Breakout expand kit | 1 | GPIO Extension board & ribbon cable |
| The official Raspberry Pi Beginner's Guide | 1 | Guide for Raspberry Pi 5 |
| Breadboard 830 points | 3 | Connecting components |
| Jumper Wires | 1 | Connecting components |
| Electronics precision tool kit | 1 | Tools for building |

---

> **Note (2026-03):** CHARLI Home is now a thin client (v3.0). The Pi handles only hardware I/O — all backend processing (STT, LLM, TTS, conversation) runs on the central CHARLI Server on the Mac Mini. See `charli_home/README.md` and `docs/charli_server/` for current setup instructions.

## Raspberry Pi Cheat Sheet

Quick reference for commands, tips, and tricks we pick up along the way.

### SSH & Remote Access

```bash
# Connect to a Pi on your local network
ssh charli@charli-home.local

# Copy a file TO the Pi
scp myfile.txt charli@charli-home.local:~/

# Copy a file FROM the Pi
scp charli@charli-home.local:~/myfile.txt .

# Copy an entire folder
scp -r myfolder charli@charli-home.local:~/
```

### System Info

```bash
# Check Pi model and hardware
cat /proc/cpuinfo

# Check OS version
cat /etc/os-release

# CPU temperature (keep it under 80°C)
vcgencmd measure_temp

# Memory usage
free -h

# Disk usage
df -h

# See all connected USB devices (mics, cameras, etc.)
lsusb

# See GPIO pin state
pinout
```

### Package Management

```bash
# Update package lists & upgrade everything
sudo apt update && sudo apt upgrade -y

# Install a package
sudo apt install -y <package-name>

# Search for a package
apt search <keyword>

# Remove a package
sudo apt remove <package-name>

# Clean up unused packages
sudo apt autoremove -y
```

### Python & Virtual Environments

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run a script with sudo but keep your env vars (.venv, CHARLI_HOST, etc.)
sudo -E python3 myscript.py

# Check which python you're using (should point to .venv)
which python3
```

### GPIO & Hardware

```bash
# List all GPIO pins and their current state
gpioinfo

# Quick test — read a pin value (gpiochip4 is Pi 5's main chip)
gpioget gpiochip4 5

# Detect audio devices (useful for mic setup)
arecord -l

# Test speaker output
speaker-test -t wav -c 2

# Test espeak-ng TTS
espeak-ng "Hello from CHARLI"
```

### Networking & Tailscale

```bash
# Check your Pi's IP address
hostname -I

# Check Tailscale status
tailscale status

# Ping another Tailscale device
tailscale ping <device-name>

# See Tailscale IP
tailscale ip

# Test if a remote port is reachable
curl -s -o /dev/null -w "%{http_code}" http://<host>:<port>/v1/models
```

### Services & Processes

```bash
# Run something in the background that survives SSH disconnect
nohup sudo -E python3 charli_home.py &

# Or better — use tmux
tmux new -s charli          # start a named session
# Ctrl+B then D to detach
tmux attach -t charli       # reattach later

# Check if a process is running
ps aux | grep charli

# Kill a process by name
pkill -f charli_home.py

# Check system logs
journalctl -xe
```

### File System & Permissions

```bash
# Make a script executable
chmod +x myscript.py

# Change ownership (useful after sudo creates files)
sudo chown -R charli:charli ~/charli-home

# Find large files eating your disk
du -sh * | sort -rh | head -10

# Watch a log file in real time
tail -f /var/log/syslog
```

### Raspberry Pi Config

```bash
# Open the Pi config tool (display, interfaces, boot, etc.)
sudo raspi-config

# Enable/disable interfaces from command line
sudo raspi-config nonint do_ssh 0      # 0 = enable
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Safe reboot
sudo reboot

# Safe shutdown
sudo shutdown -h now
```

### Tips & Tricks

- **Always use `sudo -E`** when running Python scripts that need GPIO *and* environment variables — `sudo` alone wipes your env.
- **Headless setup**: Place an empty file named `ssh` in the boot partition to enable SSH on first boot. For Wi-Fi, add `wpa_supplicant.conf`.
- **Prevent SD card corruption**: Always `sudo shutdown -h now` before unplugging power.
- **NVMe boot**: If you have the M.2 HAT+, boot from NVMe instead of SD for much faster read/write. Use `sudo raspi-config` → Advanced → Boot Order.
- **Backup your SD card**: `sudo dd if=/dev/mmcblk0 of=~/pi-backup.img bs=4M status=progress` — save an image you can flash back later.
- **Temperature throttling**: The Pi 5 throttles at 85°C. If you're running AI workloads, the Active Cooler is a must. Check temp with `vcgencmd measure_temp`.
- **Pi 5 GPIO — do NOT use `RPi.GPIO`**: The Pi 5 has a new RP1 chip. The old `RPi.GPIO` library doesn't support it and will fail silently or crash. Use `gpiozero` (high-level) with `lgpio` (low-level driver). Install both: `pip install gpiozero lgpio`.
- **Pin numbering**: gpiozero uses BCM (Broadcom) pin numbers by default, not physical pin numbers. Pin 5 in code = GPIO5 = physical pin 29.
