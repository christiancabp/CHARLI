#!/usr/bin/env python3
"""
CHARLI Home — Version 1.0 (Desk Hub)

Async orchestrator that runs three subsystems concurrently:
  1. Wake word listener  (Porcupine — "Hey Charli")
  2. Voice pipeline      (record → transcribe → ask → speak)
  3. Web server          (FastAPI + WebSocket for JARVIS UI)

No more GPIO or sudo needed — uses USB mic, Bluetooth speaker,
and a 7" touchscreen running Chromium in kiosk mode.
"""

import asyncio
import signal
import sys

import uvicorn

# ── Building blocks ──────────────────────────────────────────────────
from src.state_manager import StateManager, State
from src.wake_word import WakeWordDetector
from src.record import record_audio
from src.transcribe import transcribe
from src.ask_charli import ask_charli
from src.speak import speak

# ── Web server (FastAPI app) ─────────────────────────────────────────
from web.server import app as web_app
import web.server as web_server

# ── Settings ─────────────────────────────────────────────────────────
WEB_HOST = "0.0.0.0"
WEB_PORT = 8080


async def voice_pipeline(state: StateManager):
    """
    Runs the wake-word → record → transcribe → ask → speak loop
    in a background thread (blocking calls wrapped with run_in_executor).
    """
    loop = asyncio.get_event_loop()
    detector = WakeWordDetector()

    try:
        while True:
            # ── Wait for wake word ───────────────────────────────────
            await state.set_state(State.IDLE)
            detected = await loop.run_in_executor(
                None, detector.wait_for_wakeword
            )
            if not detected:
                continue

            # ── Record ───────────────────────────────────────────────
            await state.set_state(State.LISTENING)
            audio_file = await loop.run_in_executor(None, record_audio)
            if not audio_file:
                continue

            # ── Transcribe + Ask CHARLI ──────────────────────────────
            await state.set_state(State.THINKING)
            question, language = await loop.run_in_executor(
                None, transcribe, audio_file
            )

            if not question:
                continue

            # Add user message to conversation
            state.add_message_sync("user", question)

            answer = await loop.run_in_executor(
                None, ask_charli, question, language
            )

            # Add CHARLI's response to conversation
            state.add_message_sync("charli", answer)

            # ── Speak ────────────────────────────────────────────────
            await state.set_state(State.SPEAKING)
            await loop.run_in_executor(None, speak, answer, language)

    except asyncio.CancelledError:
        pass
    finally:
        detector.stop()


async def run_web_server(state: StateManager):
    """Start the FastAPI/uvicorn web server as an async task."""
    # Inject the shared state manager into the web server module
    web_server.state_manager = state

    config = uvicorn.Config(
        web_app,
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    """Launch all subsystems concurrently."""
    state = StateManager()
    state._loop = asyncio.get_event_loop()

    print(f"CHARLI Home v1.0 — Desk Hub")
    print(f"Web UI: http://localhost:{WEB_PORT}")
    print(f"Waiting for wake word... (Ctrl+C to quit)")

    # Run web server and voice pipeline concurrently
    await asyncio.gather(
        run_web_server(state),
        voice_pipeline(state),
    )


if __name__ == "__main__":
    # Graceful shutdown on Ctrl+C
    def handle_sigint(sig, frame):
        print("\nCHARLI Home shutting down. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    asyncio.run(main())
