#!/usr/bin/env python3
"""
CHARLI Home — Version 3.0 (Thin Client)

The desk hub is now a pure client. No backend, no API server.
It does three things: listen, send, play.

Concurrent subsystems via asyncio.gather():
  1. Voice Pipeline  → wake word → record → POST to server → play audio
  2. UI Server       → minimal static file server for JARVIS touchscreen
  3. System Monitor  → CPU temp, RAM (broadcast via server WebSocket)
  4. Mac Link        → persistent WebSocket to Mac Mini

What lives HERE (hardware I/O):
  - Wake word detection (Porcupine, USB mic)
  - Audio recording (arecord, USB mic)
  - Audio playback (aplay/afplay, Bluetooth speaker)
  - JARVIS UI static files (served to Chromium kiosk)

What lives on the SERVER (charli_server on Mac Mini):
  - Speech-to-text (faster-whisper via sidecar)
  - LLM queries (OpenClaw)
  - Text-to-speech (espeak-ng/Piper via sidecar)
  - Conversation history (Prisma/SQLite)
  - Device auth, WebSocket gateway, REST API

No GPIO or sudo needed.
"""

import asyncio
import os
import signal
import subprocess
import sys
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from functools import partial

# ── Our Building Blocks ──────────────────────────────────────────────
from src.state_manager import StateManager, State
from src.wake_word import WakeWordDetector
from src.record import record_audio
from src.system_monitor import monitor_loop
from src.mac_link import MacLink
from src.charli_server_client import (
    voice_pipeline as server_voice_pipeline,
    check_health as server_check_health,
)

# ── Settings ─────────────────────────────────────────────────────────
UI_PORT = 8080
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web", "static")


# =====================================================================
# AUDIO PLAYBACK
# =====================================================================

def play_audio(audio_path: str):
    """
    Play a WAV file through the default audio output (Bluetooth speaker).
    Cleans up the temp file after playback.
    """
    if not audio_path or not os.path.exists(audio_path):
        return

    try:
        if sys.platform == "darwin":
            subprocess.run(["afplay", audio_path], check=True)
        else:
            subprocess.run(["aplay", audio_path], check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Audio playback error: {e}")
    finally:
        try:
            os.unlink(audio_path)
        except OSError:
            pass


def speak_local(text: str, language: str = "en"):
    """
    Local TTS fallback — speak directly via espeak-ng on the Pi.
    Used when Mac pushes a "speak this" command and we don't want
    a server round-trip for something that should be instant.
    """
    voice_map = {"en": "en", "es": "es"}
    voice = voice_map.get(language, "en")
    try:
        subprocess.run(["espeak-ng", "-v", voice, text], check=True, capture_output=True)
    except FileNotFoundError:
        print("⚠️ espeak-ng not installed — cannot speak locally")
    except Exception as e:
        print(f"❌ Local TTS error: {e}")


# =====================================================================
# VOICE PIPELINE — The main conversation loop
# =====================================================================

async def voice_pipeline(state: StateManager):
    """
    Listen → Record → Send to server → Play response. Repeat forever.

    State machine: IDLE → LISTENING → THINKING → SPEAKING → IDLE

    The server returns a WAV file containing CHARLI's spoken answer.
    We just play it through the speaker.
    """
    loop = asyncio.get_event_loop()
    detector = WakeWordDetector()

    if not server_check_health():
        print("⚠️ CHARLI Server is not reachable. Will retry on each wake word.")

    try:
        while True:
            # ── Wait for wake word ────────────────────────────
            await state.set_state(State.IDLE)
            detected = await loop.run_in_executor(None, detector.wait_for_wakeword)
            if not detected:
                continue

            # ── Record audio ──────────────────────────────────
            await state.set_state(State.LISTENING)
            audio_file = await loop.run_in_executor(None, record_audio)
            if not audio_file:
                continue

            # ── Send to server (transcribe → ask → TTS) ──────
            await state.set_state(State.THINKING)

            # Future: capture Pi camera image for vision queries
            # image_path = capture_image()
            image_path = None

            response_audio, transcription, answer, language = await loop.run_in_executor(
                None, server_voice_pipeline, audio_file, image_path
            )

            # Update local state for the JARVIS UI
            if transcription:
                state.add_message_sync("user", transcription)
            if answer:
                state.add_message_sync("charli", answer)

            # Clean up input recording
            try:
                os.unlink(audio_file)
            except OSError:
                pass

            # ── Play the response ─────────────────────────────
            if response_audio:
                await state.set_state(State.SPEAKING)
                await loop.run_in_executor(None, play_audio, response_audio)
            elif answer:
                # Fallback: speak locally if server returned text but no audio
                await state.set_state(State.SPEAKING)
                await loop.run_in_executor(None, speak_local, answer, language)

    except asyncio.CancelledError:
        pass
    finally:
        detector.stop()


# =====================================================================
# UI SERVER — Minimal static file server for the touchscreen
# =====================================================================
# No FastAPI, no REST API, no WebSocket. Just file serving.
# The JARVIS UI's JavaScript connects directly to charli_server's
# WebSocket for real-time state updates.

class QuietHandler(SimpleHTTPRequestHandler):
    """Static file handler that doesn't spam the terminal with logs."""
    def log_message(self, format, *args):
        pass  # Silence request logging

async def run_ui_server():
    """
    Serve the JARVIS UI static files on port 8080.

    Chromium kiosk on the Pi opens http://localhost:8080 and loads
    the HTML/CSS/JS. The JavaScript in charli.js connects to
    charli_server's WebSocket for live state updates.
    """
    handler = partial(QuietHandler, directory=STATIC_DIR)
    server = HTTPServer(("0.0.0.0", UI_PORT), handler)

    # Run in a background thread so it doesn't block the event loop
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    # Keep this coroutine alive (so asyncio.gather doesn't exit)
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        server.shutdown()


# =====================================================================
# MAIN — Start everything
# =====================================================================

async def main():
    state = StateManager()
    state._loop = asyncio.get_event_loop()
    state.system_metrics = {}

    mac_link = MacLink(state)
    mac_link._speak_fn = speak_local

    server_url = os.environ.get("CHARLI_SERVER_URL", "http://charli-server:3000")

    print(f"CHARLI Home v3.0 — Desk Hub (Thin Client)")
    print(f"JARVIS UI: http://localhost:{UI_PORT}")
    print(f"Server:    {server_url}")
    print(f"Waiting for wake word... (Ctrl+C to quit)\n")

    await asyncio.gather(
        voice_pipeline(state),      # Wake word → record → server → play
        run_ui_server(),            # Static files for JARVIS touchscreen
        monitor_loop(state),        # CPU temp, RAM, Tailscale
        mac_link.run(),             # Persistent WS to Mac Mini
    )


if __name__ == "__main__":
    def handle_sigint(sig, frame):
        print("\nCHARLI Home shutting down. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    asyncio.run(main())
