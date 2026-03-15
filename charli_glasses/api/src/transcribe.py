#!/usr/bin/env python3
"""
CHARLI Glasses - Audio Transcription (Speech-to-Text).

Same Whisper-based transcription as the desk hub, but packaged for the
glasses API server. The iOS companion app records audio from the glasses'
Bluetooth mic and sends it here for transcription.

Uses faster-whisper with the "base" model — same config as the Pi.
If this server runs on the Mac Mini (which has more power), you could
upgrade to "small" or "medium" for better accuracy.
"""

import os
from faster_whisper import WhisperModel

# ── Load the Model ───────────────────────────────────────────────────
# Model size can be configured via env var. Default "base" matches the Pi.
# On a more powerful machine, use "small" or "medium" for better accuracy.
MODEL_SIZE = os.environ.get("CHARLI_WHISPER_MODEL", "base")

print(f"Loading faster-whisper model ({MODEL_SIZE}, INT8)...")
model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
print("✅ faster-whisper is ready!")


def transcribe(audio_path: str) -> tuple:
    """
    Transcribe an audio file to text.

    Args:
        audio_path: Path to WAV/M4A audio file

    Returns:
        (text, language_code) — e.g. ("What's the weather?", "en")
        Returns ("", "en") on error.
    """
    if not audio_path or not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return "", "en"

    print(f"📝 Transcribing {audio_path}...")

    try:
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        language = info.language or "en"

        lang_name = "English" if language == "en" else "Spanish" if language == "es" else language

        if text:
            print(f"💬 [{lang_name}] Heard: '{text}'")
        else:
            print("⚠️ No speech detected in audio.")

        return text, language

    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return "", "en"


# ── Standalone Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "test_audio.wav"
    transcribe(path)
