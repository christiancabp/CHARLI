# Raspberry Pi CLI Commands

Copy-paste ready commands to interact with your Pi like a pro. Organized by task so you can find what you need fast.

---

## SSH & Remote Access

```bash
# Connect to your Pi
ssh charli@charli-home.local

# Connect with verbose output (debug connection issues)
ssh -v charli@charli-home.local

# Connect to a Pi by IP instead of hostname
ssh charli@192.168.1.XXX

# Generate SSH keys (run on your Mac, not the Pi)
ssh-keygen -t ed25519 -C "charli-mac"

# Copy your SSH key to the Pi (no more password prompts)
ssh-copy-id charli@charli-home.local

# SSH config shortcut — add this to ~/.ssh/config on your Mac:
# Host pi
#     HostName charli-home.local
#     User charli
# Then just: ssh pi
```

## File Transfers

```bash
# Copy a file TO the Pi
scp myfile.txt charli@charli-home.local:~/

# Copy a file FROM the Pi
scp charli@charli-home.local:~/myfile.txt .

# Copy an entire folder TO the Pi
scp -r myfolder/ charli@charli-home.local:~/

# Sync a folder (faster than scp for repeated transfers, only sends changes)
rsync -avz --progress ./my-project/ charli@charli-home.local:~/my-project/

# Sync FROM the Pi to your Mac
rsync -avz --progress charli@charli-home.local:~/my-project/ ./my-project/

# Sync but exclude certain files
rsync -avz --exclude '.venv' --exclude '__pycache__' ./src/ charli@charli-home.local:~/src/
```

## System Information

```bash
# Check Pi model and hardware
cat /proc/cpuinfo

# One-liner: which Pi model am I on?
cat /proc/device-tree/model && echo

# Check OS version
cat /etc/os-release

# CPU temperature (keep under 80C, throttles at 85C)
vcgencmd measure_temp

# CPU frequency
vcgencmd measure_clock arm

# Voltage
vcgencmd measure_volts core

# Memory usage (human readable)
free -h

# Disk usage
df -h

# Uptime and load average
uptime

# See all connected USB devices
lsusb

# Detailed USB device info
lsusb -v 2>/dev/null | grep -E "idVendor|idProduct|iProduct"

# See GPIO pinout diagram in terminal
pinout

# List all GPIO pins and their state (Pi 5)
gpioinfo gpiochip4

# Check kernel messages (useful after plugging in hardware)
dmesg | tail -20

# Watch system resources live
htop
```

## CPU & Performance Monitoring

```bash
# Live CPU temperature monitoring (updates every 2 seconds)
watch -n 2 vcgencmd measure_temp

# Full system dashboard (CPU, memory, temp, processes)
htop

# Check if CPU is being throttled
vcgencmd get_throttled
# 0x0 = all good
# 0x50005 = throttled due to temperature

# Benchmark: quick CPU stress test (run for 30 seconds then check temp)
stress --cpu 4 --timeout 30 && vcgencmd measure_temp

# Monitor memory usage over time
watch -n 5 free -h
```

## Package Management

```bash
# Update package lists & upgrade everything
sudo apt update && sudo apt upgrade -y

# Full distribution upgrade (for major OS updates)
sudo apt full-upgrade -y

# Install a package
sudo apt install -y <package-name>

# Install multiple packages at once
sudo apt install -y git vim htop tmux

# Search for a package
apt search <keyword>

# Show package info before installing
apt show <package-name>

# Remove a package
sudo apt remove <package-name>

# Remove a package AND its config files
sudo apt purge <package-name>

# Clean up unused packages and cache
sudo apt autoremove -y && sudo apt clean
```

## Python & Virtual Environments

```bash
# Check Python version
python3 --version

# Create a virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Deactivate
deactivate

# Install dependencies from requirements file
pip install -r requirements.txt

# Install a single package
pip install <package-name>

# Freeze current packages to requirements
pip freeze > requirements.txt

# Run a script with sudo but keep your env vars
sudo -E .venv/bin/python3 myscript.py

# Check which python you're using (should point to .venv)
which python3

# Upgrade pip itself
pip install --upgrade pip
```

## Networking

```bash
# Check your Pi's IP addresses
hostname -I

# Full network interface details
ip addr show

# Check Wi-Fi connection
iwgetid

# Wi-Fi signal strength
iwconfig wlan0 2>/dev/null | grep -i quality

# Scan for available Wi-Fi networks
sudo iwlist wlan0 scan | grep ESSID

# Test internet connectivity
ping -c 4 google.com

# Check what ports are listening
sudo ss -tlnp

# Check what's using a specific port
sudo lsof -i :8080

# DNS lookup
nslookup charli-home.local

# Download a file
wget <url>

# Make an HTTP request
curl -s http://localhost:8080/health
```

## Tailscale

```bash
# Check Tailscale status
tailscale status

# See your Tailscale IP
tailscale ip

# Ping another Tailscale device
tailscale ping <device-name>

# See all devices on your tailnet
tailscale status --json | python3 -m json.tool

# Check Tailscale Serve config
tailscale serve status

# Restart Tailscale
sudo systemctl restart tailscaled

# Test if OpenClaw gateway is reachable
curl -s -o /dev/null -w "%{http_code}" https://<tailscale-hostname>:18789/v1/models
```

## Process Management

```bash
# Run something in the background (survives SSH disconnect)
nohup python3 charli_home.py > charli.log 2>&1 &

# Better: use tmux for persistent sessions
tmux new -s charli              # start named session
# Ctrl+B then D               # detach (process keeps running)
tmux ls                         # list sessions
tmux attach -t charli           # reattach

# tmux split panes (inside tmux)
# Ctrl+B then %               # split vertical
# Ctrl+B then "               # split horizontal
# Ctrl+B then arrow keys      # switch panes

# Check if a process is running
ps aux | grep charli

# Kill a process by name
pkill -f charli_home.py

# Kill everything matching a pattern
pkill -f "python3.*charli"

# See top CPU-consuming processes
ps aux --sort=-%cpu | head -10

# See top memory-consuming processes
ps aux --sort=-%mem | head -10

# Check system logs
journalctl -xe

# Follow system logs in real time
journalctl -f
```

## Systemd Services

```bash
# Create a service so your app starts on boot
# Save this as /etc/systemd/system/charli.service:
#
# [Unit]
# Description=CHARLI Home Assistant
# After=network-online.target
# Wants=network-online.target
#
# [Service]
# Type=simple
# User=charli
# WorkingDirectory=/home/charli/charli-home
# EnvironmentFile=/home/charli/charli-home/.env
# ExecStart=/home/charli/charli-home/.venv/bin/python3 charli_home.py
# Restart=on-failure
# RestartSec=5
#
# [Install]
# WantedBy=multi-user.target

# After creating the service file:
sudo systemctl daemon-reload
sudo systemctl enable charli        # start on boot
sudo systemctl start charli         # start now
sudo systemctl status charli        # check status
sudo systemctl stop charli          # stop
sudo systemctl restart charli       # restart
sudo systemctl disable charli       # don't start on boot

# View service logs
journalctl -u charli -f
journalctl -u charli --since "10 min ago"
```

## Audio (Mic & Speaker)

```bash
# List recording devices (find your USB mic)
arecord -l

# List playback devices
aplay -l

# Record a 5-second test clip
arecord -D plughw:1,0 -f S16_LE -r 16000 -c 1 -d 5 test.wav

# Play it back
aplay test.wav

# Test speaker output
speaker-test -t wav -c 2

# Test text-to-speech
espeak-ng "Hello from CHARLI"

# Adjust volume levels
alsamixer

# Set volume from command line (0-100)
amixer set Master 80%

# Check Bluetooth audio devices
bluetoothctl devices
bluetoothctl info <MAC_ADDRESS>
```

## File System & Permissions

```bash
# Make a script executable
chmod +x myscript.py

# Change ownership (useful after sudo creates files)
sudo chown -R charli:charli ~/charli-home

# Find large files eating your disk
du -sh * | sort -rh | head -10

# Find files larger than 100MB
find / -size +100M -type f 2>/dev/null

# Watch a log file in real time
tail -f /var/log/syslog

# Create a directory and all parents
mkdir -p ~/projects/new-project/src

# Quick file search by name
find ~/ -name "*.py" -type f 2>/dev/null

# Check total disk space used by a directory
du -sh ~/charli-home
```

## Git on the Pi

```bash
# Clone a repo
git clone https://github.com/user/repo.git

# Pull latest changes
git pull

# Check status
git status

# Quick commit workflow
git add -A && git commit -m "update from pi" && git push

# Set up git identity (first time)
git config --global user.name "Charli"
git config --global user.email "your@email.com"

# See recent commits
git log --oneline -10
```

## Raspberry Pi Config

```bash
# Open the interactive config tool
sudo raspi-config

# Enable interfaces from command line (0 = enable, 1 = disable)
sudo raspi-config nonint do_ssh 0
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_serial_hw 0
sudo raspi-config nonint do_camera 0

# Set boot to CLI (no desktop)
sudo raspi-config nonint do_boot_behaviour B1

# Set boot to desktop with autologin
sudo raspi-config nonint do_boot_behaviour B4

# Change hostname
sudo raspi-config nonint do_hostname new-hostname

# Set boot order to NVMe first (Pi 5 with M.2 HAT+)
sudo raspi-config nonint do_boot_order B6

# Edit boot config directly
sudo nano /boot/firmware/config.txt

# Safe reboot
sudo reboot

# Safe shutdown (ALWAYS do this before unplugging!)
sudo shutdown -h now

# Schedule a shutdown in 5 minutes
sudo shutdown -h +5

# Cancel a scheduled shutdown
sudo shutdown -c
```

## Backup & Recovery

```bash
# Backup entire SD card to an image (run on Mac, with SD in reader)
sudo dd if=/dev/diskN of=~/pi-backup.img bs=4m status=progress

# Backup just your home directory (run on Mac)
rsync -avz charli@charli-home.local:~/ ~/pi-backup/home/

# Restore an image to SD card (run on Mac)
sudo dd if=~/pi-backup.img of=/dev/diskN bs=4m status=progress

# Backup on the Pi itself (to USB drive)
sudo dd if=/dev/mmcblk0 of=/media/usb/pi-backup.img bs=4M status=progress
```

## Quick Aliases

Add these to `~/.bashrc` on your Pi for faster workflows:

```bash
# Paste into ~/.bashrc
alias temp='vcgencmd measure_temp'
alias update='sudo apt update && sudo apt upgrade -y'
alias ip='hostname -I'
alias ports='sudo ss -tlnp'
alias gs='git status'
alias gp='git pull'
alias cls='clear'
alias ll='ls -lah'
alias ..='cd ..'
alias ...='cd ../..'
alias pistat='echo "--- Temp ---" && vcgencmd measure_temp && echo "--- Memory ---" && free -h && echo "--- Disk ---" && df -h / && echo "--- Uptime ---" && uptime'

# Reload after editing
source ~/.bashrc
```

## Pi-to-Pi Communication

```bash
# Discover other Pis on your network
ping -c 1 charli-home.local     # Pi 5
# If you set up other Pis with hostnames:
ping -c 1 charli-zero.local     # Pi Zero 2 W

# Quick message between Pis using netcat
# On receiving Pi:
nc -l 9999
# On sending Pi:
echo "hello from pi5" | nc charli-zero.local 9999

# Share files between Pis
scp file.txt charli@charli-zero.local:~/
```

---

> **Tip**: Bookmark this file. When you're SSH'd into the Pi and forget a command, you'll thank yourself later.
