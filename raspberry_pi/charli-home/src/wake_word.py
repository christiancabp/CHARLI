#!/usr/bin/env python3
"""
CHARLI Home - Wake Word Detection

Listens for "Hey Charli" using Picovoice Porcupine.
Uses pvrecorder for audio capture from the USB microphone.

Requires:
  PICOVOICE_ACCESS_KEY — your Picovoice Console access key
"""

import os
import pvporcupine
from pvrecorder import PvRecorder

ACCESS_KEY = os.environ.get("PICOVOICE_ACCESS_KEY", "")

# Path to custom "Hey Charli" wake word model (.ppn file)
# Generate yours at https://console.picovoice.ai/
KEYWORD_PATH = os.environ.get(
    "CHARLI_KEYWORD_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "models", "hey-charli_en_raspberry-pi.ppn")
)

# Audio device index — -1 means default input device
AUDIO_DEVICE_INDEX = int(os.environ.get("CHARLI_AUDIO_DEVICE_INDEX", "-1"))


class WakeWordDetector:
    """
    Wraps Porcupine for wake word detection.

    Usage:
        detector = WakeWordDetector()
        detector.wait_for_wakeword()   # blocks until "Hey Charli"
        detector.stop()                # clean shutdown
    """

    def __init__(self):
        self._porcupine = None
        self._recorder = None

    def _init_engine(self):
        """Initialize Porcupine and the audio recorder."""
        if not ACCESS_KEY:
            raise RuntimeError(
                "PICOVOICE_ACCESS_KEY not set. "
                "Get a free key at https://console.picovoice.ai/"
            )

        # If a custom keyword model exists, use it; otherwise fall back
        # to the built-in "jarvis" keyword as a placeholder
        if os.path.exists(KEYWORD_PATH):
            self._porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keyword_paths=[KEYWORD_PATH],
            )
        else:
            print(f"Custom keyword not found at {KEYWORD_PATH}")
            print("Falling back to built-in 'jarvis' keyword")
            self._porcupine = pvporcupine.create(
                access_key=ACCESS_KEY,
                keywords=["jarvis"],
            )

        self._recorder = PvRecorder(
            frame_length=self._porcupine.frame_length,
            device_index=AUDIO_DEVICE_INDEX,
        )

    def wait_for_wakeword(self):
        """Block until the wake word is detected. Returns True on detection."""
        if self._porcupine is None:
            self._init_engine()

        self._recorder.start()
        print("Listening for wake word...")

        try:
            while True:
                pcm = self._recorder.read()
                keyword_index = self._porcupine.process(pcm)
                if keyword_index >= 0:
                    print("Wake word detected!")
                    self._recorder.stop()
                    return True
        except KeyboardInterrupt:
            self._recorder.stop()
            return False

    def stop(self):
        """Release all resources."""
        if self._recorder is not None:
            try:
                self._recorder.stop()
            except Exception:
                pass
            self._recorder.delete()
            self._recorder = None

        if self._porcupine is not None:
            self._porcupine.delete()
            self._porcupine = None


if __name__ == "__main__":
    detector = WakeWordDetector()
    try:
        print("Say 'Hey Charli' (or 'Jarvis' if using fallback)...")
        detector.wait_for_wakeword()
        print("Wake word heard! Pipeline would start here.")
    finally:
        detector.stop()
