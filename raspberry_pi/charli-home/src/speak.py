#!/usr/bin/env python3
"""
CHARLI Home - Building Block 4: Speak text aloud using espeak-ng.
This is the final step in the voice pipeline — CHARLI's mouth.
"""

import subprocess

# Map language codes (from Whisper) to espeak-ng voice names
VOICE_MAP = {
    "en": "en",
    "es": "es",
}


def speak(text: str, language: str = "en"):
    """
    Speaks the given text aloud using espeak-ng.
    Language defaults to English; pass 'es' for Spanish, etc.
    """

    if not text:
        print("⚠️ Nothing to say.")
        return

    voice = VOICE_MAP.get(language, "en")
    print(f"🔊 Speaking ({voice})...")

    try:
        subprocess.run(
            ["espeak-ng", "-v", voice, text],
            check=True
        )
    except FileNotFoundError:
        print("❌ espeak-ng not found. Install it with: sudo apt install espeak-ng")
    except subprocess.CalledProcessError as e:
        print(f"❌ espeak-ng error: {e}")


if __name__ == "__main__":
    speak("Hello! I am CHARLI, your personal assistant.")
