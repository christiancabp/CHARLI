#!/usr/bin/env python3
"""
CHARLI Home — Version 0.2
The full voice pipeline:
  Button A → Record → Whisper (speech to text) → CHARLI (AI response) → Speak

Fixed for Raspberry Pi 5 using gpiozero.
"""

import time
from gpiozero import Button

# ── Import our building blocks ────────────────────────────────────────
from src.record import record_audio          # Step 1: record voice
from src.transcribe import transcribe        # Step 2: voice → text
from src.ask_charli import ask_charli        # Step 3: text → CHARLI's answer
from src.speak import speak                  # Step 4: answer → spoken aloud

# ── Settings ──────────────────────────────────────────────────────────
# GPIO pin 5 for Button A on Pirate Audio HAT
button = Button(5)

# ── Main loop ─────────────────────────────────────────────────────────
print("✅ CHARLI Home is ready! Press Button A to speak.")
print("Waiting for button press... (Ctrl+C to quit)")

try:
    while True:
        # Check if button is pressed
        if button.is_pressed:
            # Run the full pipeline
            audio_file = record_audio()        # 🎤 Record your voice

            if audio_file:
                question, language = transcribe(audio_file)  # voice -> text + language

                # Only ask CHARLI if we actually heard something
                if question:
                    answer = ask_charli(question, language)  # ask CHARLI
                    speak(answer, language)                   # 🔊 Speak

            # Wait half a second before checking the button again
            time.sleep(0.5)

        # Check the button every 50ms
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n👋 CHARLI Home shutting down. Goodbye!")
