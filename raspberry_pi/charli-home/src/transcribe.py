#!/usr/bin/env python3
"""
CHARLI Home - Building Block 2: Convert audio into text using faster-whisper.

Uses faster-whisper (CTranslate2 backend) instead of openai-whisper for:
  - 4x faster transcription on Pi 5 (~3-4s vs ~10-15s for 5s audio)
  - ~200MB less RAM (no PyTorch dependency)
  - INT8 quantization for efficient CPU inference
  - Same Whisper model weights, same accuracy
"""

import os
from faster_whisper import WhisperModel

# -- Load the model --------------------------------------------------------
# INT8 quantization: uses 8-bit integers instead of 32-bit floats.
# This makes the model 4x smaller in memory with negligible accuracy loss.
# "cpu" device since the Pi 5 has no CUDA GPU.
print("Loading faster-whisper model (base, INT8)...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("✅ faster-whisper is ready!")


def transcribe(audio_path: str) -> tuple:
    """
    Takes the path to an audio file and returns (text, language).

    The model runs locally on the Pi — no internet needed, no API calls,
    no token cost. This is like running a mini AI brain right on the device.
    """

    if not audio_path or not os.path.exists(audio_path):
        print(f"❌ Error: Audio file not found at {audio_path}")
        return "", "en"

    print(f"📝 Listening to {audio_path}...")

    try:
        # faster-whisper returns segments (an iterator) and info
        segments, info = model.transcribe(audio_path, beam_size=5)

        # Collect all segment texts into one string
        text = " ".join(segment.text.strip() for segment in segments).strip()

        language = info.language or "en"
        lang_name = "English" if language == "en" else "Spanish" if language == "es" else language

        if text:
            print(f"💬 [{lang_name}] You said: '{text}'")
        else:
            print("⚠️ Whisper heard silence or couldn't decode speech.")

        return text, language

    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return "", "en"


if __name__ == "__main__":
    # Test with the standard recording path
    path = "/home/charli/charli-home/recordings/charli_recording.wav"
    transcribe(path)
