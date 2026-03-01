#!/usr/bin/env python3
"""
CHARLI Home - Building Block 1: Record audio from the microphone.
FIXED: Using 2 channels (Stereo) as required by the Pirate Audio HAT.
"""

import os
import subprocess
import soundfile as sf
import numpy as np

# ── Settings ──────────────────────────────────────────────────────────
SAMPLE_RATE = 16000
DURATION = 5

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
OUTPUT_FILE = os.path.join(RECORDINGS_DIR, "charli_recording.wav")

os.makedirs(RECORDINGS_DIR, exist_ok=True)

def record_audio():
    """Records audio using arecord on card 2 with 2 channels."""

    print("🎤 Recording (Stereo) — speak now!")

    try:
        # We use -c 2 because the dual mic HAT requires stereo
        cmd = [
            "arecord",
            "-D", "hw:2,0",
            "-f", "S16_LE",
            "-r", str(SAMPLE_RATE),
            "-c", "2",
            "-d", str(DURATION),
            OUTPUT_FILE
        ]
        
        subprocess.run(cmd, check=True)

        # Read the stereo file
        data, samplerate = sf.read(OUTPUT_FILE)
        
        # Convert to Mono for Whisper (average the two channels)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Normalize and Boost
        if np.max(np.abs(data)) > 0:
            data = data / np.max(np.abs(data))
            data = data * 2.0 # Double the volume after normalizing
            data = np.clip(data, -1.0, 1.0) # Prevent distortion
        
        sf.write(OUTPUT_FILE, data, samplerate)
        
        os.chmod(OUTPUT_FILE, 0o666)
        print(f"✅ Saved to {OUTPUT_FILE}")
        return OUTPUT_FILE

    except Exception as e:
        print(f"❌ Recording Error: {e}")
        return None

if __name__ == "__main__":
    record_audio()
