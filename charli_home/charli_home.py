#!/usr/bin/env python3
"""
CHARLI Home — Version 3.0 (Desk Hub → Thin Client)

This is the MAIN entry point — the "conductor" of the orchestra.

It starts 4 things running AT THE SAME TIME (concurrently):
  1. Wake word listener  → Porcupine listens for "Hey Charli"
  2. Voice pipeline      → record → send to CHARLI Server → play response
  3. Web server          → FastAPI serves the JARVIS UI on port 8080
  4. System monitor      → Reads CPU temp, RAM every 10 seconds
  5. Mac Link            → Persistent WebSocket to Mac Mini

What changed in v3.0 (Thin Client):
  Before: record → transcribe (local Whisper) → ask (OpenClaw) → speak (local espeak)
  After:  record → POST to CHARLI Server → play returned audio

  The Pi is now ears (mic), mouth (speaker), and face (touchscreen).
  All processing (STT, LLM, TTS) happens on the Mac Mini via charli_server.

Python Concept — asyncio:
  asyncio is like JavaScript's event loop + async/await. We use
  run_in_executor() to run blocking functions in background threads
  so the main event loop stays responsive.

No GPIO or sudo needed — uses USB mic, Bluetooth speaker,
and a 7" touchscreen running Chromium in kiosk mode.
"""

# ── Standard Library Imports ──────────────────────────────────────────
import asyncio
import os
import signal
import subprocess
import sys

# ── Third-Party Imports ───────────────────────────────────────────────
import uvicorn

# ── Our Building Blocks ──────────────────────────────────────────────
from src.state_manager import StateManager, State
from src.wake_word import WakeWordDetector
from src.record import record_audio
from src.system_monitor import monitor_loop
from src.mac_link import MacLink

# ── CHARLI Server Client ────────────────────────────────────────────
# This replaces local transcribe, ask_charli, and speak modules.
# All heavy processing now happens on the Mac Mini via the server.
from src.charli_server_client import (
    voice_pipeline as server_voice_pipeline,
    ask_charli as server_ask_charli,
    speak_text as server_speak_text,
    check_health as server_check_health,
)

# ── Web Server ────────────────────────────────────────────────────────
from web.server import app as web_app
import web.server as web_server

# ── Settings ─────────────────────────────────────────────────────────
WEB_HOST = "0.0.0.0"
WEB_PORT = 8080


# =====================================================================
# LOCAL AUDIO PLAYBACK
# =====================================================================

def play_audio(audio_path: str):
    """
    Play a WAV file through the default audio output (Bluetooth speaker).

    On Linux (Pi): uses aplay
    On macOS: uses afplay (for development/testing)
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
        # Clean up the temp response file
        try:
            os.unlink(audio_path)
        except OSError:
            pass


def speak_local(text: str, language: str = "en"):
    """
    Local TTS fallback — speak directly via espeak-ng on the Pi.
    Used when the server is unreachable or for push-to-speak from Mac.
    """
    voice_map = {"en": "en", "es": "es"}
    voice = voice_map.get(language, "en")
    try:
        subprocess.run(["espeak-ng", "-v", voice, text], check=True, capture_output=True)
    except Exception as e:
        print(f"❌ Local TTS error: {e}")


# =====================================================================
# VOICE PIPELINE — The main conversation loop
# =====================================================================

async def voice_pipeline(state: StateManager):
    """
    The heart of CHARLI — an infinite loop that:
      1. Waits for "Hey Charli" (wake word)
      2. Records your voice (5 seconds)
      3. Sends audio to CHARLI Server (which does transcribe → ask → TTS)
      4. Plays back the audio response
      5. Goes back to step 1

    State Machine:
      IDLE → LISTENING → THINKING → SPEAKING → IDLE → ...

    The server handles STT, LLM, and TTS. The Pi just records and plays.
    """
    loop = asyncio.get_event_loop()
    detector = WakeWordDetector()

    # Check if server is reachable at startup
    if not server_check_health():
        print("⚠️ CHARLI Server is not reachable. Voice pipeline will retry on each wake word.")

    try:
        while True:
            # ── STEP 1: Wait for wake word ────────────────────────
            await state.set_state(State.IDLE)

            detected = await loop.run_in_executor(
                None, detector.wait_for_wakeword
            )

            if not detected:
                continue

            # ── STEP 2: Record audio ──────────────────────────────
            await state.set_state(State.LISTENING)
            audio_file = await loop.run_in_executor(None, record_audio)

            if not audio_file:
                continue

            # ── STEP 3: Send to CHARLI Server ─────────────────────
            # The server transcribes, asks the LLM, and generates TTS.
            # We get back a WAV file to play.
            await state.set_state(State.THINKING)

            # Optional: capture an image from a Pi camera if attached
            # image_path = capture_image()  # Future: Pi camera support
            image_path = None

            response_audio, transcription, answer, language = await loop.run_in_executor(
                None, server_voice_pipeline, audio_file, image_path
            )

            # Update conversation history in state manager (for the web UI)
            if transcription:
                state.add_message_sync("user", transcription)
            if answer:
                state.add_message_sync("charli", answer)

            # Clean up the input recording
            try:
                os.unlink(audio_file)
            except OSError:
                pass

            # ── STEP 4: Play the response ─────────────────────────
            if response_audio:
                await state.set_state(State.SPEAKING)
                await loop.run_in_executor(None, play_audio, response_audio)
            elif answer:
                # Server returned text but no audio — speak locally as fallback
                await state.set_state(State.SPEAKING)
                await loop.run_in_executor(None, speak_local, answer, language)

            # Loop back to STEP 1 (IDLE) automatically

    except asyncio.CancelledError:
        pass
    finally:
        detector.stop()


# =====================================================================
# WEB SERVER — Serves the JARVIS UI
# =====================================================================

async def run_web_server(state: StateManager):
    """Start the FastAPI/uvicorn web server as an async task."""

    # Inject shared state + functions into the web server module
    web_server.state_manager = state
    web_server.speak_fn = speak_local           # Local TTS for push-to-speak
    web_server.ask_fn = server_ask_charli       # Ask via CHARLI Server
    web_server.speak_text_fn = server_speak_text  # TTS via server (returns audio file)

    config = uvicorn.Config(
        web_app,
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    await server.serve()


# =====================================================================
# MAIN — Start everything
# =====================================================================

async def main():
    """
    Launch all subsystems concurrently using asyncio.gather().
    All tasks run at the same time. If any one crashes, the others keep running.
    """
    state = StateManager()
    state._loop = asyncio.get_event_loop()
    state.system_metrics = {}

    # Pi↔Mac persistent WebSocket connection
    mac_link = MacLink(state)
    mac_link._speak_fn = speak_local  # Local TTS for Mac push commands

    print(f"CHARLI Home v3.0 — Desk Hub (Thin Client)")
    print(f"Web UI: http://localhost:{WEB_PORT}")
    print(f"Server: {os.environ.get('CHARLI_SERVER_URL', 'http://charli-server:3000')}")
    print(f"Waiting for wake word... (Ctrl+C to quit)")

    await asyncio.gather(
        run_web_server(state),
        voice_pipeline(state),
        monitor_loop(state),
        mac_link.run(),
    )


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    def handle_sigint(sig, frame):
        print("\nCHARLI Home shutting down. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    asyncio.run(main())
