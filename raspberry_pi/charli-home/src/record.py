#!/usr/bin/env python3
"""
CHARLI Home - Building Block 1: Record audio from the microphone.

Supports both the original Pirate Audio HAT (stereo, hw:2,0) and
USB microphones (typically mono, plughw:1,0). Configure via env vars:

  CHARLI_MIC_DEVICE   — ALSA device string  (default: plughw:1,0)
  CHARLI_MIC_CHANNELS — Number of channels   (default: 1)
"""

import os
import subprocess
import soundfile as sf
import numpy as np

# ── Settings ──────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
DURATION = 5

# Mic configuration — override via environment variables
MIC_DEVICE = os.environ.get("CHARLI_MIC_DEVICE", "hw:0,0")
MIC_CHANNELS = int(os.environ.get("CHARLI_MIC_CHANNELS", "1"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
OUTPUT_FILE = os.path.join(RECORDINGS_DIR, "charli_recording.wav")

os.makedirs(RECORDINGS_DIR, exist_ok=True)

def record_audio():
    """Records audio using arecord with the configured mic device."""

    print(f"Recording ({MIC_CHANNELS}ch on {MIC_DEVICE}) — speak now!")

    try:
        cmd = [
            "arecord",
            "-D", MIC_DEVICE,
            "-f", "S16_LE",
            "-r", str(SAMPLE_RATE),
            "-c", str(MIC_CHANNELS),
            "-d", str(DURATION),
            OUTPUT_FILE
        ]

        subprocess.run(cmd, check=True)

        # Read the recorded file
        data, samplerate = sf.read(OUTPUT_FILE)

        # Convert to mono if stereo (for Whisper compatibility)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Normalize and boost volume
        if np.max(np.abs(data)) > 0:
            data = data / np.max(np.abs(data))
            data = data * 2.0
            data = np.clip(data, -1.0, 1.0)

        sf.write(OUTPUT_FILE, data, samplerate)

        os.chmod(OUTPUT_FILE, 0o666)
        print(f"Saved to {OUTPUT_FILE}")
        return OUTPUT_FILE

    except Exception as e:
        print(f"Recording Error: {e}")
        return None

if __name__ == "__main__":
    record_audio()
