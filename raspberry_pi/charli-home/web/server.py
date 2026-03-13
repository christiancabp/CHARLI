#!/usr/bin/env python3
"""
CHARLI Home - Web Server

FastAPI application that serves the JARVIS touchscreen UI and provides
both WebSocket (real-time state updates) and REST API endpoints.

FastAPI is Python's equivalent of Express.js:
  Express:  app.get('/api/status', (req, res) => res.json({...}))
  FastAPI:  @app.get('/api/status') async def get_status(): return {...}

The web server does THREE things:
  1. Serves the JARVIS UI (HTML/CSS/JS) as static files → the touchscreen
  2. Provides a WebSocket at /ws for real-time state updates → the orb reacts
  3. Exposes REST API endpoints for the Pi↔Mac nervous system:
       POST /api/speak  — Make Pi speak text aloud
       POST /api/ask    — Send a question through CHARLI
       GET  /api/status — Get current state + system metrics
       GET  /health     — Simple health check for monitoring
"""

import json
import os
import time

# FastAPI imports — these are the building blocks for the web server.
# FastAPI is like Express.js but with automatic request validation,
# auto-generated API docs, and built-in WebSocket support.
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles   # Serve static files (like express.static())
from fastapi.responses import HTMLResponse     # Return HTML instead of JSON

# Pydantic models define the SHAPE of request bodies.
# This is like TypeScript interfaces for API requests — if the request
# doesn't match the shape, FastAPI automatically returns a 422 error.
# Example: SpeakRequest requires {text: string, language?: string}
from pydantic import BaseModel

# ── Dependency Injection ──────────────────────────────────────────────
# These module-level variables are set by charli_home.py at startup.
# This is a simple form of dependency injection — the orchestrator
# creates these objects and "injects" them into this module.
#
# In Express.js, you might do: app.locals.stateManager = stateManager;
# In Python, we set module-level variables: web_server.state_manager = state

# The shared StateManager — holds current state + conversation history
state_manager = None

# References to building block functions (so REST API can use them)
speak_fn = None    # src/speak.py's speak() function
ask_fn = None      # src/ask_charli.py's ask_charli() function

# ── Create the FastAPI App ────────────────────────────────────────────
# This is like: const app = express();
app = FastAPI(title="CHARLI Home")

# Serve static files (HTML, CSS, JS) from web/static/ directory.
# Any request to /static/... will serve files from that directory.
# This is like: app.use('/static', express.static('web/static'))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Record when the server started (used for uptime calculation)
_start_time = time.time()


# =====================================================================
# REQUEST MODELS — Define the shape of API request bodies
# =====================================================================
# These are like TypeScript interfaces:
#   interface SpeakRequest { text: string; language?: string; }
#
# Pydantic validates incoming JSON automatically. If someone sends
# {"text": 123} instead of {"text": "hello"}, they get a clear error.

class SpeakRequest(BaseModel):
    text: str              # Required: the text to speak
    language: str = "en"   # Optional: defaults to English


class AskRequest(BaseModel):
    question: str          # Required: the question to ask CHARLI
    language: str = "en"   # Optional: defaults to English


# =====================================================================
# PAGES — Serve the JARVIS UI
# =====================================================================

@app.get("/")
async def root():
    """
    Serve the main JARVIS UI page.

    When you open http://localhost:8080 in a browser (or Chromium kiosk),
    this handler reads index.html and returns it.

    The @app.get("/") decorator is like:
      app.get('/', (req, res) => { res.sendFile('index.html') })
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r") as f:
        html = f.read()
    return HTMLResponse(content=html)


# =====================================================================
# WEBSOCKET — Real-time state updates
# =====================================================================

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket endpoint for real-time communication with the UI.

    This is the live connection between the Python backend and the
    browser's JavaScript (charli.js). It works like this:

    1. Browser connects: new WebSocket('ws://localhost:8080/ws')
    2. Server sends a "snapshot" — full current state + conversation history
    3. Server streams updates as they happen:
       - {"type": "state", "state": "listening"}     → orb turns cyan
       - {"type": "message", "role": "user", ...}    → transcript updates
       - {"type": "system", "metrics": {...}}         → status bar updates
    4. Connection stays open until browser disconnects

    The "snapshot on connect" pattern ensures the UI always shows the
    correct state, even if you refresh the page mid-conversation.
    This is like sending the Redux store's initial state to a new client.
    """

    # Accept the WebSocket handshake (like the TCP 3-way handshake but for WS)
    await ws.accept()

    # Guard: if the server isn't fully initialized yet, reject the connection
    if state_manager is None:
        await ws.close(reason="State manager not initialized")
        return

    # Register this client to receive broadcasts.
    # state_manager._broadcast() will now include this WebSocket.
    state_manager.register(ws)

    try:
        # Send the full current state to the newly connected client.
        # This includes: current state (IDLE/LISTENING/etc.) + all conversation messages.
        # The UI uses this to render the correct state immediately.
        snapshot = await state_manager.snapshot()
        await ws.send_text(json.dumps(snapshot))

        # Keep the connection alive by listening for messages from the frontend.
        # Currently we just log them, but in the future this could handle:
        #   - Manual wake word trigger (touch button on UI)
        #   - IoT controls (smart lights, etc.)
        #   - Text input (type a question instead of speaking)
        while True:
            data = await ws.receive_text()
            print(f"Received from UI: {data}")

    except WebSocketDisconnect:
        # Browser tab was closed or connection lost — this is normal
        pass
    finally:
        # Always unregister the client, even if we crash.
        # Otherwise the broadcast loop would try to send to a dead connection.
        state_manager.unregister(ws)


# =====================================================================
# REST API — Pi↔Mac Nervous System endpoints
# =====================================================================

@app.get("/health")
async def health():
    """
    Simple health check — returns {"status": "ok", "uptime_seconds": 1234}.

    The Mac Mini can poll this endpoint to verify the Pi is alive:
      curl http://charli-home:8080/health

    This is a common pattern in microservices — a /health endpoint that
    monitoring tools (Prometheus, uptime robots, etc.) can check.
    """
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
    }


@app.get("/api/status")
async def get_status():
    """
    Returns the Pi's current state, conversation length, and system metrics.

    Example response:
      {
        "state": "idle",
        "conversation_length": 4,
        "uptime_seconds": 3600,
        "system": {
          "cpu_temp": 42.5,
          "ram_percent": 12.5,
          "tailscale": "connected"
        }
      }

    Useful for building dashboards or monitoring from the Mac.
    """
    if state_manager is None:
        return {"error": "Not initialized"}

    result = {
        "state": state_manager.state.value,
        "conversation_length": len(state_manager.conversation),
        "uptime_seconds": round(time.time() - _start_time),
    }

    # Include system metrics if the system_monitor has collected them.
    # hasattr() checks if the attribute exists (it's added dynamically
    # by charli_home.py: state.system_metrics = {})
    if hasattr(state_manager, "system_metrics") and state_manager.system_metrics:
        result["system"] = state_manager.system_metrics

    return result


@app.post("/api/speak")
async def api_speak(req: SpeakRequest):
    """
    Make the Pi speak text aloud through the Bluetooth speaker.

    Called by the Mac Mini to push voice output to the Pi.
    Example: Mac sends {"text": "Dinner is ready"} and the Pi announces it.

    In curl terms:
      curl -X POST http://charli-home:8080/api/speak \
           -H 'Content-Type: application/json' \
           -d '{"text": "Dinner is ready", "language": "en"}'

    The `req: SpeakRequest` parameter is automatically parsed from the
    JSON body. FastAPI + Pydantic handle validation — if `text` is missing,
    the client gets a 422 error with a helpful message.
    """
    if speak_fn is None:
        return {"error": "Speak function not available"}

    import asyncio
    loop = asyncio.get_event_loop()

    # speak() is BLOCKING (it runs espeak-ng and waits for it to finish).
    # run_in_executor moves it to a background thread so the web server
    # can still handle other requests while the Pi is talking.
    await loop.run_in_executor(None, speak_fn, req.text, req.language)

    return {"status": "ok", "text": req.text}


@app.post("/api/ask")
async def api_ask(req: AskRequest):
    """
    Send a question to CHARLI and return the answer as JSON.

    Useful for programmatic queries from the Mac Mini or other clients.
    Unlike the voice pipeline (which goes through the speaker), this
    returns the answer as text in the HTTP response.

    Example:
      curl -X POST http://charli-home:8080/api/ask \
           -H 'Content-Type: application/json' \
           -d '{"question": "What time is it?"}' \

    Response:
      {"status": "ok", "question": "What time is it?", "answer": "It's 5:42 PM."}

    The question and answer are also saved to conversation history,
    so they appear in the JARVIS UI transcript.
    """
    if ask_fn is None:
        return {"error": "Ask function not available"}

    import asyncio
    loop = asyncio.get_event_loop()

    # Pass conversation history for context-aware responses
    history = state_manager.conversation if state_manager else []

    # ask_charli() is BLOCKING (it makes an HTTP request to OpenClaw).
    # run_in_executor moves it to a background thread.
    answer = await loop.run_in_executor(
        None, ask_fn, req.question, req.language, history
    )

    # Save the exchange to conversation history so it shows in the UI
    # and future questions have context
    if state_manager:
        state_manager.add_message_sync("user", req.question)
        state_manager.add_message_sync("charli", answer)

    return {"status": "ok", "question": req.question, "answer": answer}
