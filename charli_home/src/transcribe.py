#!/usr/bin/env python3
"""
CHARLI Home - Building Block 2: Convert audio into text (Speech-to-Text).

This is CHARLI's ability to UNDERSTAND what you said. The USB mic records
your voice (Building Block 1), and this module converts that audio into
text that we can send to the LLM.

Uses faster-whisper (CTranslate2 backend) instead of openai-whisper:
  - 4x faster on Pi 5 (~3-4 seconds vs ~10-15 seconds for 5s of audio)
  - ~200MB less RAM (no PyTorch dependency)
  - INT8 quantization = model uses 8-bit numbers instead of 32-bit
    (4x smaller in memory, nearly identical accuracy)
  - Same Whisper model weights — OpenAI trained the model, CTranslate2
    just runs it more efficiently

This runs 100% LOCALLY on the Pi — no internet, no API calls, no tokens.
It's like having a tiny AI brain right on the device.
"""

import os
from faster_whisper import WhisperModel

# ── Load the Model ────────────────────────────────────────────────────
# This runs ONCE when the module is first imported (at startup).
# The model stays in memory so we don't reload it for every transcription.
#
# In JavaScript terms, this is like a module-level singleton:
#   const model = loadModel('base')  // runs once at import time
#   export function transcribe(audio) { return model.process(audio) }
#
# Parameters:
#   "base"        — Model size. Options: tiny, base, small, medium, large.
#                   "base" is the sweet spot for Pi 5: fast enough and accurate enough.
#   device="cpu"  — Run on CPU (Pi 5 has no NVIDIA GPU for CUDA)
#   compute_type="int8" — Use 8-bit integers instead of 32-bit floats.
#                         This is called "quantization" — it's like compressing
#                         the model's brain to use less memory. The quality loss
#                         is negligible for speech recognition.
print("Loading faster-whisper model (base, INT8)...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("✅ faster-whisper is ready!")


def transcribe(audio_path: str) -> tuple:
    """
    Takes the path to a WAV audio file and returns (text, language).

    Example:
      text, lang = transcribe("recordings/charli_recording.wav")
      # text = "What's the weather like today?"
      # lang = "en"

    The language is auto-detected — if you speak Spanish, it returns "es".
    This is passed to ask_charli() and speak() so the whole pipeline
    responds in the same language you used.

    Returns ("", "en") on any error — the empty text signals to the
    voice pipeline that nothing was understood, so it skips this turn.
    """

    # Guard: make sure the audio file actually exists
    if not audio_path or not os.path.exists(audio_path):
        print(f"❌ Error: Audio file not found at {audio_path}")
        return "", "en"

    print(f"📝 Listening to {audio_path}...")

    try:
        # ── Run the Whisper Model ─────────────────────────────────
        # model.transcribe() returns TWO things:
        #   1. segments — an iterator of text chunks (like paragraphs)
        #   2. info — metadata including detected language
        #
        # beam_size=5 means "consider 5 possible interpretations at each
        # step and pick the best one." Higher = more accurate but slower.
        # 5 is the default sweet spot.
        segments, info = model.transcribe(audio_path, beam_size=5)

        # ── Collect All Text Segments ─────────────────────────────
        # Whisper breaks audio into segments (chunks of text).
        # For a 5-second recording, there's usually just 1 segment.
        # We join them all into one string.
        #
        # This is a "generator expression" — Python's version of:
        #   segments.map(s => s.text.trim()).join(' ')
        text = " ".join(segment.text.strip() for segment in segments).strip()

        # Get the detected language (e.g., "en" for English, "es" for Spanish)
        language = info.language or "en"

        # Map language codes to human-readable names for the log
        lang_name = "English" if language == "en" else "Spanish" if language == "es" else language

        if text:
            print(f"💬 [{lang_name}] You said: '{text}'")
        else:
            print("⚠️ Whisper heard silence or couldn't decode speech.")

        return text, language

    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return "", "en"


# ── Standalone Test ───────────────────────────────────────────────────
# First record audio:  python3 src/record.py
# Then test this:      python3 src/transcribe.py
if __name__ == "__main__":
    path = "/home/charli/charli-home/recordings/charli_recording.wav"
    transcribe(path)
