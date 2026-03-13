#!/usr/bin/env python3
"""
CHARLI Home - Building Block 1: Record audio from the microphone.

This is CHARLI's "ears" — it captures your voice through the USB mic
and saves it as a WAV file that Whisper can then transcribe.

How it works:
  1. Calls `arecord` (a Linux command) to capture audio from the USB mic
  2. Reads the recorded WAV file back into memory
  3. Converts stereo to mono (if needed) because Whisper expects mono
  4. Normalizes the volume (makes quiet recordings louder)
  5. Saves the processed file back to disk

This is the same pattern as child_process.exec() in Node.js:
  const { execSync } = require('child_process');
  execSync('arecord -D hw:0,0 -d 5 output.wav');

Configure via environment variables:
  CHARLI_MIC_DEVICE   — ALSA device string  (default: hw:0,0)
  CHARLI_MIC_CHANNELS — Number of channels   (default: 1)
"""

import os
import subprocess       # Python's child_process equivalent
import soundfile as sf  # Library to read/write WAV files (like a Node audio package)
import numpy as np      # Numerical arrays — think of it like a math toolkit for arrays

# ── Settings ──────────────────────────────────────────────────────────

# Sample rate: 16,000 samples per second.
# This means the mic captures 16,000 tiny snapshots of sound each second.
# 16kHz is the standard for speech recognition — CD quality is 44.1kHz,
# but Whisper doesn't need that much detail for understanding words.
SAMPLE_RATE = 16000

# How many seconds to record. Fixed at 5 for now.
# Phase 3 (VAD) will upgrade this to stop when you stop talking.
DURATION = 5

# ── Mic Configuration ─────────────────────────────────────────────────

# ALSA device string — tells Linux WHICH microphone to use.
# "hw:0,0" means: sound card 0, device 0 (the USB mic).
# You found this by running: arecord -l (list recording devices)
# os.environ.get() is like process.env.CHARLI_MIC_DEVICE || "hw:0,0"
MIC_DEVICE = os.environ.get("CHARLI_MIC_DEVICE", "hw:0,0")

# Number of audio channels. 1 = mono (one mic), 2 = stereo (left+right).
# USB mics are almost always mono.
MIC_CHANNELS = int(os.environ.get("CHARLI_MIC_CHANNELS", "1"))

# ── File Paths ────────────────────────────────────────────────────────

# __file__ is the path to THIS script (record.py).
# We go up two directories to get the project root (charli-home/).
# os.path is Python's path module — like Node's path.join().
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
OUTPUT_FILE = os.path.join(RECORDINGS_DIR, "charli_recording.wav")

# Create the recordings/ directory if it doesn't exist.
# exist_ok=True means "don't error if it already exists" — like mkdir -p.
os.makedirs(RECORDINGS_DIR, exist_ok=True)


def record_audio():
    """
    Records audio from the USB microphone using the `arecord` Linux command.

    Returns the path to the saved WAV file, or None if recording failed.
    The WAV file is always saved to the same path (overwritten each time)
    since we only need the most recent recording.
    """

    print(f"Recording ({MIC_CHANNELS}ch on {MIC_DEVICE}) — speak now!")

    try:
        # Build the arecord command as a list of arguments.
        # This is safer than a string because it avoids shell injection.
        # In Node.js, this is like: execFileSync('arecord', ['-D', 'hw:0,0', ...])
        cmd = [
            "arecord",             # Linux audio recording command
            "-D", MIC_DEVICE,      # -D = which device (hw:0,0 = USB mic)
            "-f", "S16_LE",        # -f = format: Signed 16-bit, Little Endian
            "-r", str(SAMPLE_RATE),# -r = sample rate: 16000 Hz
            "-c", str(MIC_CHANNELS),# -c = channels: 1 (mono)
            "-d", str(DURATION),   # -d = duration: 5 seconds
            OUTPUT_FILE            # Where to save the WAV file
        ]

        # subprocess.run() executes the command and WAITS for it to finish.
        # check=True means "raise an error if the command fails" (non-zero exit).
        # This is a BLOCKING call — that's why charli_home.py wraps it in
        # run_in_executor() to avoid freezing the event loop.
        subprocess.run(cmd, check=True)

        # ── Post-processing: normalize the audio ─────────────────

        # Read the WAV file back into memory as a numpy array.
        # `data` is an array of numbers between -1.0 and 1.0, where each
        # number represents one audio sample (16,000 per second).
        # Think of it like: const data = fs.readFileSync('recording.wav')
        # but parsed into actual audio values, not raw bytes.
        data, samplerate = sf.read(OUTPUT_FILE)

        # If the mic recorded in stereo (2 channels), average them into mono.
        # Whisper expects a single audio channel.
        # data.shape is like array.length but for multi-dimensional arrays.
        # A stereo file has shape (80000, 2) — 80000 samples, 2 channels.
        # A mono file has shape (80000,) — just 80000 samples.
        if len(data.shape) > 1:
            # np.mean(data, axis=1) averages across channels for each sample.
            # Like: monoSample = (leftSample + rightSample) / 2
            data = np.mean(data, axis=1)

        # Normalize: scale the audio so the loudest part hits maximum volume.
        # This is important because USB mics often record very quietly.
        # Without this, Whisper might not be able to hear what you said.
        if np.max(np.abs(data)) > 0:
            # Step 1: Divide by the loudest sample → everything is now -1.0 to 1.0
            data = data / np.max(np.abs(data))
            # Step 2: Boost by 2x (make it louder)
            data = data * 2.0
            # Step 3: Clip to valid range (anything above 1.0 becomes 1.0)
            # This prevents audio distortion from the boost.
            data = np.clip(data, -1.0, 1.0)

        # Write the processed audio back to the same file
        sf.write(OUTPUT_FILE, data, samplerate)

        # Make the file readable/writable by everyone.
        # 0o666 is an octal number (like chmod 666 in terminal).
        # This prevents permission errors when other processes read it.
        os.chmod(OUTPUT_FILE, 0o666)

        print(f"Saved to {OUTPUT_FILE}")
        return OUTPUT_FILE

    except Exception as e:
        print(f"Recording Error: {e}")
        return None


# ── Standalone Test ───────────────────────────────────────────────────
# Run this file directly to test the mic:
#   python3 src/record.py
# Then play it back:
#   aplay recordings/charli_recording.wav
if __name__ == "__main__":
    record_audio()
