#!/usr/bin/env python3
"""
CHARLI Home - Building Block 4: Speak text aloud using espeak-ng.

This is CHARLI's "mouth" — the final step in the voice pipeline.
After the LLM generates a text response, this module converts that
text into audible speech through the Bluetooth speaker.

Uses espeak-ng, a text-to-speech (TTS) engine:
  - Runs as a Linux command (like arecord for recording)
  - Robotic-sounding but instant — no model loading, no GPU needed
  - Supports 100+ languages including English and Spanish
  - Phase 4 will upgrade to Piper TTS for a natural human-like voice

Same subprocess pattern as record.py:
  Node.js:  execSync('espeak-ng -v en "Hello world"')
  Python:   subprocess.run(['espeak-ng', '-v', 'en', 'Hello world'])
"""

import subprocess  # For running espeak-ng as a Linux command

# ── Voice Map ─────────────────────────────────────────────────────────
# Maps Whisper's language codes to espeak-ng voice names.
# Whisper detects "en" or "es", and we tell espeak-ng which voice to use.
# This is like a simple lookup table:
#   const VOICE_MAP = { en: "en", es: "es" };
VOICE_MAP = {
    "en": "en",   # English
    "es": "es",   # Spanish
}


def speak(text: str, language: str = "en"):
    """
    Speaks the given text aloud through the Bluetooth speaker.

    Args:
        text:     The text to speak (CHARLI's response from ask_charli)
        language: Language code from Whisper ("en" or "es")

    How it works:
      1. Looks up the espeak-ng voice name for the language
      2. Runs: espeak-ng -v en "It's 72 degrees and sunny."
      3. The audio plays through the default audio output (Bluetooth speaker)
      4. The command blocks until speech is finished playing

    The blocking behavior is actually what we want here — we don't want
    to start listening for the next wake word while CHARLI is still talking.
    """

    # Don't try to speak empty text
    if not text:
        print("⚠️ Nothing to say.")
        return

    # Look up the espeak-ng voice. If the language isn't in our map,
    # default to English. .get() is like: VOICE_MAP[language] ?? "en"
    voice = VOICE_MAP.get(language, "en")
    print(f"🔊 Speaking ({voice})...")

    try:
        # Run espeak-ng as a subprocess (Linux command).
        # Arguments:
        #   -v voice  = which voice/language to use
        #   text      = the text to speak (passed as the last argument)
        #
        # check=True means "raise an error if espeak-ng returns non-zero exit code"
        # This call BLOCKS until the speech finishes playing.
        subprocess.run(
            ["espeak-ng", "-v", voice, text],
            check=True
        )
    except FileNotFoundError:
        # espeak-ng isn't installed on this system
        print("❌ espeak-ng not found. Install it with: sudo apt install espeak-ng")
    except subprocess.CalledProcessError as e:
        # espeak-ng ran but encountered an error (bad voice name, audio issue, etc.)
        print(f"❌ espeak-ng error: {e}")


# ── Standalone Test ───────────────────────────────────────────────────
# Test the speaker:
#   python3 src/speak.py
# You should hear "Hello! I am CHARLI..." through the Bluetooth speaker.
if __name__ == "__main__":
    speak("Hello! I am CHARLI, your personal assistant.")
