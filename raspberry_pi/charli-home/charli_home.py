#!/usr/bin/env python3
"""
CHARLI Home — Version 2.0 (Desk Hub)

This is the MAIN entry point — the "conductor" of the orchestra.
Think of it like your index.ts or server.ts in a Node project.

It starts 4 things running AT THE SAME TIME (concurrently):
  1. Wake word listener  → Porcupine listens for "Hey Charli"
  2. Voice pipeline      → record → transcribe → ask → speak
  3. Web server          → FastAPI serves the JARVIS UI on port 8080
  4. System monitor      → Reads CPU temp, RAM every 10 seconds
  5. Mac Link            → Persistent WebSocket to Mac Mini

Python Concept — asyncio:
  Python's asyncio is like JavaScript's event loop + async/await.
  In Node.js, everything is async by default. In Python, most things
  are BLOCKING (they freeze the program while they run). So we use
  asyncio to run multiple things concurrently, and run_in_executor()
  to run blocking code without freezing everything else.

  Think of run_in_executor() like wrapping a blocking function in
  new Promise() — it moves the work to a background thread so the
  main event loop stays responsive.

No GPIO or sudo needed — uses USB mic, Bluetooth speaker,
and a 7" touchscreen running Chromium in kiosk mode.
"""

# ── Standard Library Imports ──────────────────────────────────────────
# These come built into Python (like Node.js built-in modules)
import asyncio    # Python's event loop (like Node's event loop)
import signal     # Listen for OS signals (like process.on('SIGINT'))
import sys        # System-level operations (like process.exit())

# ── Third-Party Imports ───────────────────────────────────────────────
# These are installed via pip (like npm packages)
import uvicorn    # ASGI server for FastAPI (like Express.js for Node)

# ── Our Building Blocks ──────────────────────────────────────────────
# Each of these is a module in src/ that does ONE thing.
# In Node terms, these are like importing functions from your own modules:
#   import { recordAudio } from './src/record.js'
from src.state_manager import StateManager, State
from src.wake_word import WakeWordDetector
from src.record import record_audio
from src.transcribe import transcribe
from src.ask_charli import ask_charli
from src.speak import speak
from src.system_monitor import monitor_loop
from src.mac_link import MacLink

# ── Web Server ────────────────────────────────────────────────────────
# We import the FastAPI app AND the module itself.
# The module import lets us inject the state_manager later (line ~102).
# This is a form of "dependency injection" — we create the state_manager
# here in main() and pass it into the web server module.
from web.server import app as web_app
import web.server as web_server

# ── Settings ─────────────────────────────────────────────────────────
# "0.0.0.0" means "listen on ALL network interfaces" — so the web UI
# is accessible from other devices on the network, not just localhost.
# Port 8080 avoids needing sudo (ports below 1024 require root).
WEB_HOST = "0.0.0.0"
WEB_PORT = 8080


# =====================================================================
# VOICE PIPELINE — The main conversation loop
# =====================================================================

async def voice_pipeline(state: StateManager):
    """
    The heart of CHARLI — an infinite loop that:
      1. Waits for "Hey Charli" (wake word)
      2. Records your voice (5 seconds)
      3. Converts speech to text (Whisper AI, runs locally)
      4. Sends the text to OpenClaw on Mac Mini (the ONLY step using tokens)
      5. Speaks the answer aloud (espeak-ng)
      6. Goes back to step 1

    State Machine:
      IDLE → LISTENING → THINKING → SPEAKING → IDLE → ...

    Each state change is broadcast via WebSocket to the JARVIS UI,
    which changes the orb color accordingly.

    The 'await' keyword here works just like in JavaScript — it pauses
    THIS function until the awaited thing finishes, but lets OTHER
    async tasks (like the web server) keep running.
    """

    # Get a reference to the event loop so we can run blocking functions
    # in a background thread. This is the key Python async pattern:
    #   await loop.run_in_executor(None, blocking_function, arg1, arg2)
    # is equivalent to JavaScript's:
    #   await new Promise(resolve => {
    #     worker.postMessage({ fn: blockingFunction, args: [arg1, arg2] });
    #     worker.onmessage = (result) => resolve(result);
    #   });
    loop = asyncio.get_event_loop()

    # Create the wake word detector (Porcupine).
    # It's created once and reused across loop iterations.
    detector = WakeWordDetector()

    try:
        # ── Infinite conversation loop ────────────────────────────
        # This runs forever until the program is stopped (Ctrl+C).
        # Each iteration is one complete conversation turn.
        while True:

            # ── STEP 1: Wait for wake word ────────────────────────
            # Set state to IDLE → orb turns blue, UI shows "IDLE"
            await state.set_state(State.IDLE)

            # wait_for_wakeword() is BLOCKING (it sits in a while loop
            # reading audio frames). run_in_executor moves it to a
            # background thread so the web server keeps running.
            detected = await loop.run_in_executor(
                None,                        # None = use default thread pool
                detector.wait_for_wakeword   # the blocking function to run
            )

            # If detection was cancelled (e.g., KeyboardInterrupt), skip
            if not detected:
                continue

            # ── STEP 2: Record audio ──────────────────────────────
            # Set state to LISTENING → orb turns cyan
            await state.set_state(State.LISTENING)

            # record_audio() runs `arecord` for 5 seconds (blocking)
            audio_file = await loop.run_in_executor(None, record_audio)

            # If recording failed, go back to waiting for wake word
            if not audio_file:
                continue

            # ── STEP 3: Transcribe + Ask CHARLI ───────────────────
            # Set state to THINKING → orb turns orange
            await state.set_state(State.THINKING)

            # Whisper converts the audio file to text (runs locally on Pi).
            # Returns a tuple: ("what you said", "en" or "es")
            question, language = await loop.run_in_executor(
                None, transcribe, audio_file
            )

            # If Whisper couldn't understand anything, skip this turn
            if not question:
                continue

            # Save what the user said to conversation history.
            # add_message_sync is the thread-safe version — it schedules
            # the WebSocket broadcast on the event loop from this thread.
            state.add_message_sync("user", question)

            # Send the question to OpenClaw on Mac Mini.
            # We pass the conversation history so CHARLI can understand
            # follow-ups like "How big is it?" after "What's the capital of France?"
            answer = await loop.run_in_executor(
                None,                    # thread pool
                ask_charli,              # function
                question,                # arg 1: what you asked
                language,                # arg 2: "en" or "es"
                state.conversation       # arg 3: past messages for context
            )

            # Save CHARLI's response to conversation history
            state.add_message_sync("charli", answer)

            # ── STEP 4: Speak the answer ──────────────────────────
            # Set state to SPEAKING → orb turns gold
            await state.set_state(State.SPEAKING)

            # espeak-ng reads the text aloud through the Bluetooth speaker
            await loop.run_in_executor(None, speak, answer, language)

            # Loop back to STEP 1 (IDLE) automatically

    except asyncio.CancelledError:
        # This happens during graceful shutdown — it's normal, not an error.
        # In Node.js terms, this is like handling process.on('SIGTERM').
        pass
    finally:
        # Always clean up Porcupine resources, even if we crash.
        # The `finally` block runs no matter what — like a try/finally in JS.
        detector.stop()


# =====================================================================
# WEB SERVER — Serves the JARVIS UI
# =====================================================================

async def run_web_server(state: StateManager):
    """
    Start the FastAPI/uvicorn web server as an async task.

    FastAPI is Python's equivalent of Express.js:
      - Express:  app.get('/api/status', (req, res) => { ... })
      - FastAPI:  @app.get('/api/status') async def get_status(): ...

    uvicorn is the HTTP server that runs FastAPI, like how Node.js
    has a built-in HTTP server that Express sits on top of.
    """

    # "Dependency injection" — we create the state_manager in main()
    # and pass it into the web server module. This way, both the voice
    # pipeline and web server share the SAME state object.
    # In Node/Express, you'd do something like:
    #   app.locals.stateManager = state;
    web_server.state_manager = state

    # Also inject the building block functions so the REST API can use them.
    # The /api/speak endpoint needs speak(), and /api/ask needs ask_charli().
    web_server.speak_fn = speak
    web_server.ask_fn = ask_charli

    # Configure uvicorn (the HTTP server)
    config = uvicorn.Config(
        web_app,               # The FastAPI app object
        host=WEB_HOST,         # "0.0.0.0" = listen on all interfaces
        port=WEB_PORT,         # 8080
        log_level="warning",   # Only show warnings, not every HTTP request
    )
    server = uvicorn.Server(config)

    # server.serve() runs forever — it's the equivalent of
    # app.listen(8080, () => console.log('Server running'))
    await server.serve()


# =====================================================================
# MAIN — Start everything
# =====================================================================

async def main():
    """
    Launch all subsystems concurrently using asyncio.gather().

    asyncio.gather() is like Promise.all() in JavaScript:
      await Promise.all([
        runWebServer(state),
        voicePipeline(state),
        monitorLoop(state),
        macLink.run(),
      ]);

    All four tasks run at the same time. If any one crashes,
    the others keep running.
    """

    # Create the shared state manager — this is the "single source of truth"
    # that all subsystems read from and write to.
    state = StateManager()

    # Give the state manager a reference to the event loop so its
    # thread-safe methods (set_state_sync, add_message_sync) can schedule
    # WebSocket broadcasts from background threads.
    state._loop = asyncio.get_event_loop()

    # This dict will be filled by system_monitor with CPU temp, RAM, etc.
    state.system_metrics = {}

    # Set up the Pi↔Mac persistent WebSocket connection.
    # If CHARLI_MAC_WS_URL env var isn't set, it prints a message and exits
    # gracefully (the other subsystems still run fine without it).
    mac_link = MacLink(state)
    mac_link._speak_fn = speak  # So Mac can push "speak this text" commands

    print(f"CHARLI Home v2.0 — Desk Hub")
    print(f"Web UI: http://localhost:{WEB_PORT}")
    print(f"Waiting for wake word... (Ctrl+C to quit)")

    # Run ALL subsystems concurrently — none of these return until shutdown.
    # They all run in the same process but take turns on the event loop.
    await asyncio.gather(
        run_web_server(state),    # Serves JARVIS UI on port 8080
        voice_pipeline(state),    # Wake word → record → transcribe → ask → speak
        monitor_loop(state),      # CPU temp, RAM, Tailscale status every 10s
        mac_link.run(),           # Persistent WebSocket to Mac Mini
    )


# =====================================================================
# ENTRY POINT — What runs when you type: python3 charli_home.py
# =====================================================================

if __name__ == "__main__":
    # This block only runs when you execute this file directly.
    # It does NOT run when this file is imported as a module.
    # Same concept as: if (require.main === module) { ... } in Node.js

    # Register a signal handler for Ctrl+C (SIGINT).
    # Without this, Python would print an ugly traceback on Ctrl+C.
    # In Node.js, this is: process.on('SIGINT', () => { ... });
    def handle_sigint(sig, frame):
        print("\nCHARLI Home shutting down. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    # asyncio.run() creates an event loop and runs main() until it completes.
    # This is the Python equivalent of the top-level await in Node.js ESM,
    # or wrapping everything in an async IIFE:
    #   (async () => { await main(); })();
    asyncio.run(main())
