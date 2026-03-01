#!/usr/bin/env python3
"""
CHARLI Home - Building Block 2: Convert audio into text using Whisper.
Updated for better sensitivity and Pi 5 CPU compatibility.
"""

import whisper
import os

# -- Load the model ----------------------------------------------------
print("Loading Whisper AI model...")
model = whisper.load_model("base")
print("✅ Whisper is ready!")


def transcribe(audio_path: str) -> tuple:
    """
    Takes the path to an audio file and returns (text, language).
    """

    if not audio_path or not os.path.exists(audio_path):
        print(f"❌ Error: Audio file not found at {audio_path}")
        return "", "en"

    print(f"📝 Listening to {audio_path}...")

    try:
        # Transcribe with fp16=False to avoid CPU warnings/errors
        # and verbose=False to keep it clean
        result = model.transcribe(
            audio_path, 
            fp16=False,
            task="transcribe"
        )
        
        text = result["text"].strip()
        language = result.get("language", "en")

        lang_name = "English" if language == "en" else "Spanish" if language == "es" else language
        
        if text:
            print(f"💬 [{lang_name}] You said: '{text}'")
        else:
            print(f"⚠️ Whisper heard silence or couldn't decode speech.")
            
        return text, language

    except Exception as e:
        print(f"❌ Transcription Error: {e}")
        return "", "en"

if __name__ == "__main__":
    # Test with the standard recording path
    path = "/home/charli/charli-home/recordings/charli_recording.wav"
    transcribe(path)
