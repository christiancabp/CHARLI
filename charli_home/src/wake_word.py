#!/usr/bin/env python3
"""
CHARLI Home - Building Block 5: Wake Word Detection

This is CHARLI's "attention filter" — it listens 24/7 but only activates
when it hears the magic words "Hey Charli" (or "Jarvis" as a fallback).

This is how Alexa, Google Home, and Siri work too:
  1. A tiny, efficient ML model runs constantly, listening for ONE phrase
  2. When detected, it "wakes up" the expensive speech recognition (Whisper)
  3. This way the Pi isn't burning CPU on Whisper 100% of the time

Uses Picovoice Porcupine:
  - Tiny model (~15MB RAM) that barely uses CPU
  - Works offline (no internet needed)
  - Supports custom wake words via Picovoice Console
  - Falls back to built-in "Jarvis" keyword if custom model not found

Requires:
  PICOVOICE_ACCESS_KEY — your free key from https://console.picovoice.ai/
"""

import os
import pvporcupine       # Picovoice wake word engine
from pvrecorder import PvRecorder  # Picovoice audio recorder (captures mic frames)

# ── Configuration ─────────────────────────────────────────────────────

# Your Picovoice access key (free tier gives 3 months).
# Get one at https://console.picovoice.ai/
ACCESS_KEY = os.environ.get("PICOVOICE_ACCESS_KEY", "")

# Path to the custom "Hey Charli" wake word model file (.ppn).
# This file is generated on Picovoice Console — you train it with
# examples of how "Hey Charli" sounds, and it creates a .ppn file
# optimized for the Raspberry Pi's ARM processor.
#
# The path resolution: __file__ → src/wake_word.py
#   dirname(dirname(__file__)) → charli-home/ (project root)
#   + "models/hey-charli_en_raspberry-pi.ppn"
KEYWORD_PATH = os.environ.get(
    "CHARLI_KEYWORD_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "models", "hey-charli_en_raspberry-pi.ppn")
)

# Audio device index for the microphone.
# -1 = "use the system default input device" (usually the USB mic).
# If you have multiple mics and the wrong one is selected, find the
# right index by running: PvRecorder.get_available_devices()
AUDIO_DEVICE_INDEX = int(os.environ.get("CHARLI_AUDIO_DEVICE_INDEX", "-1"))


class WakeWordDetector:
    """
    Wraps Porcupine for wake word detection.

    This class uses "lazy initialization" — the Porcupine engine isn't
    created in __init__, but on the first call to wait_for_wakeword().
    This avoids loading the model if it's never used (saves startup time).

    Usage:
        detector = WakeWordDetector()
        detector.wait_for_wakeword()   # blocks until "Hey Charli" heard
        detector.stop()                # clean shutdown (release mic + model)

    In JavaScript terms, this is like:
        const detector = new WakeWordDetector();
        await detector.waitForWakeword();  // resolves when wake word heard
        detector.stop();
    """

    def __init__(self):
        # These start as None and get created in _init_engine().
        # This is the "lazy initialization" pattern.
        self._porcupine = None   # The wake word detection engine
        self._recorder = None    # The audio capture device

    def _init_engine(self):
        """
        Initialize Porcupine and the audio recorder.
        Called automatically on first wait_for_wakeword() call.
        """

        # Guard: can't do anything without an access key
        if not ACCESS_KEY:
            raise RuntimeError(
                "PICOVOICE_ACCESS_KEY not set. "
                "Get a free key at https://console.picovoice.ai/"
            )

        # Try to use the custom "Hey Charli" wake word model.
        # If the .ppn file doesn't exist yet, fall back to Porcupine's
        # built-in "Jarvis" keyword as a placeholder.
        if os.path.exists(KEYWORD_PATH):
            # Custom keyword — trained specifically for "Hey Charli"
            self._porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keyword_paths=[KEYWORD_PATH],  # Path to the .ppn file
            )
        else:
            print(f"Custom keyword not found at {KEYWORD_PATH}")
            print("Falling back to built-in 'jarvis' keyword")
            # Built-in keyword — Porcupine comes with several pre-trained
            # keywords like "jarvis", "alexa", "hey google", etc.
            self._porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keywords=["jarvis"],  # Use built-in keyword by name
            )

        # Create the audio recorder.
        # frame_length = how many audio samples to capture per "frame".
        # Porcupine tells us exactly how many it needs (usually 512 samples).
        # Each frame is processed by Porcupine to check for the wake word.
        self._recorder = PvRecorder(
            frame_length=self._porcupine.frame_length,
            device_index=AUDIO_DEVICE_INDEX,
        )

    def wait_for_wakeword(self):
        """
        Block until the wake word is detected. Returns True on detection.

        This is a BLOCKING function — it sits in a while loop reading
        audio frames from the mic and checking each one with Porcupine.
        That's why charli_home.py runs it in run_in_executor() to avoid
        freezing the event loop.

        The loop:
          1. Read a frame of audio from the mic (512 samples, ~32ms)
          2. Feed it to Porcupine: "Is this the wake word?"
          3. If yes → return True
          4. If no → go back to step 1

        Porcupine processes each frame in <1ms, so this barely uses CPU.
        It's running a tiny neural network optimized for this one task.
        """

        # Lazy init: create the engine on first call
        if self._porcupine is None:
            self._init_engine()

        # Start capturing audio from the microphone
        self._recorder.start()
        print("Listening for wake word...")

        try:
            while True:
                # Read one frame of audio (raw PCM samples as a list of ints)
                pcm = self._recorder.read()

                # Ask Porcupine: "Does this frame contain the wake word?"
                # Returns -1 if no match, or the keyword index (0+) if detected.
                # We only have one keyword, so detection = index 0.
                keyword_index = self._porcupine.process(pcm)

                if keyword_index >= 0:
                    # Wake word detected! Stop the recorder and return.
                    print("Wake word detected!")
                    self._recorder.stop()
                    return True

        except KeyboardInterrupt:
            # User pressed Ctrl+C — stop gracefully
            self._recorder.stop()
            return False

    def stop(self):
        """
        Release all resources — microphone and Porcupine engine.

        Always call this when done! If you don't, the mic stays locked
        and other programs can't use it. The `finally` block in
        charli_home.py's voice_pipeline() ensures this gets called
        even if the program crashes.

        .delete() is Porcupine's way of freeing C memory. Python's
        garbage collector handles Python objects, but Porcupine uses
        native C code under the hood that needs manual cleanup.
        """
        if self._recorder is not None:
            try:
                self._recorder.stop()
            except Exception:
                pass  # Might already be stopped
            self._recorder.delete()   # Free native resources
            self._recorder = None

        if self._porcupine is not None:
            self._porcupine.delete()  # Free native resources
            self._porcupine = None


# ── Standalone Test ───────────────────────────────────────────────────
# Test wake word detection:
#   python3 src/wake_word.py
# Say "Hey Charli" (or "Jarvis" if using fallback) and watch it detect!
if __name__ == "__main__":
    detector = WakeWordDetector()
    try:
        print("Say 'Hey Charli' (or 'Jarvis' if using fallback)...")
        detector.wait_for_wakeword()
        print("Wake word heard! Pipeline would start here.")
    finally:
        # The `finally` block guarantees cleanup even if an error occurs.
        # This is like try/finally in JavaScript.
        detector.stop()
