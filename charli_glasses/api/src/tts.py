#!/usr/bin/env python3
"""
CHARLI Glasses - Text-to-Speech.

Converts CHARLI's text response into an audio file that can be sent back
to the iOS companion app, which plays it through the glasses' speakers.

Unlike the desk hub (which plays audio directly via espeak-ng on the Pi),
this module generates an audio FILE and returns the path — the API server
sends this file back to the iOS app over HTTP.

TTS Options (in order of quality):
  1. espeak-ng  — Robotic but instant. Works everywhere. (current)
  2. Piper TTS  — Natural-sounding, runs locally, ~200ms latency. (upgrade path)
  3. Cloud TTS  — Google/AWS/Azure TTS APIs. Best quality, requires internet.

The module tries Piper first, falls back to espeak-ng.
"""

import os
import subprocess
import tempfile

# ── Voice Maps ───────────────────────────────────────────────────────
ESPEAK_VOICES = {
    "en": "en",
    "es": "es",
}

# Piper model paths (set via env var or leave empty to use espeak-ng)
PIPER_MODEL_PATH = os.environ.get("CHARLI_PIPER_MODEL", "")


def text_to_speech_file(text: str, language: str = "en") -> str:
    """
    Convert text to a WAV audio file and return the file path.

    The returned WAV file is a temporary file — the caller is responsible
    for cleaning it up after sending it to the client.

    Args:
        text:     The text to speak
        language: Language code ("en", "es")

    Returns:
        Path to the generated WAV file, or "" on error.
    """
    if not text:
        print("⚠️ Nothing to speak.")
        return ""

    # Try Piper first (better quality), fall back to espeak-ng
    if PIPER_MODEL_PATH and os.path.exists(PIPER_MODEL_PATH):
        return _tts_piper(text, language)
    else:
        return _tts_espeak(text, language)


def _tts_espeak(text: str, language: str) -> str:
    """Generate speech using espeak-ng (writes to a WAV file)."""
    voice = ESPEAK_VOICES.get(language, "en")

    # Create a temp WAV file for the output
    fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="charli_tts_")
    os.close(fd)

    try:
        # espeak-ng -v en -w output.wav "Hello world"
        # The -w flag writes to a WAV file instead of playing audio
        subprocess.run(
            ["espeak-ng", "-v", voice, "-w", output_path, text],
            check=True,
            capture_output=True,
        )
        print(f"🔊 TTS (espeak-ng) → {output_path}")
        return output_path

    except FileNotFoundError:
        print("❌ espeak-ng not found. Install: brew install espeak-ng (macOS) or sudo apt install espeak-ng (Linux)")
        os.unlink(output_path)
        return ""
    except subprocess.CalledProcessError as e:
        print(f"❌ espeak-ng error: {e}")
        os.unlink(output_path)
        return ""


def _tts_piper(text: str, language: str) -> str:
    """Generate speech using Piper TTS (higher quality, runs locally)."""
    fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="charli_tts_")
    os.close(fd)

    try:
        # Piper reads text from stdin and writes WAV to --output_file
        # echo "Hello" | piper --model en_US-lessac-medium.onnx --output_file out.wav
        subprocess.run(
            ["piper", "--model", PIPER_MODEL_PATH, "--output_file", output_path],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        print(f"🔊 TTS (piper) → {output_path}")
        return output_path

    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"⚠️ Piper failed ({e}), falling back to espeak-ng")
        os.unlink(output_path)
        return _tts_espeak(text, language)


# ── Standalone Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    path = text_to_speech_file("Hello! I am CHARLI, your personal assistant.")
    if path:
        print(f"✅ Audio saved to: {path}")
        # Play it (macOS)
        subprocess.run(["afplay", path])
        os.unlink(path)
