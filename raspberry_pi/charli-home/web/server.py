#!/usr/bin/env python3
"""
CHARLI Home - Web Server

FastAPI application that serves the JARVIS touchscreen UI
and provides a WebSocket endpoint for real-time state updates.

REST API endpoints enable the Pi↔Mac "nervous system":
  POST /api/speak  — Make Pi speak text aloud
  POST /api/ask    — Send a question through the voice pipeline
  GET  /api/status — Get current state + system metrics
  GET  /health     — Simple health check for monitoring
"""

import json
import os
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# The StateManager instance is injected by charli_home.py at startup
state_manager = None

# References to building blocks (injected by charli_home.py)
speak_fn = None
ask_fn = None

app = FastAPI(title="CHARLI Home")

# Serve static files (HTML, CSS, JS) from web/static/
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_start_time = time.time()


# ── Request models ────────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    text: str
    language: str = "en"


class AskRequest(BaseModel):
    question: str
    language: str = "en"


# ── Pages ─────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main JARVIS UI page."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r") as f:
        html = f.read()
    return HTMLResponse(content=html)


# ── WebSocket ─────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket endpoint for real-time communication with the UI.
    Sends a full snapshot on connect, then streams state/message updates.
    """
    await ws.accept()

    if state_manager is None:
        await ws.close(reason="State manager not initialized")
        return

    state_manager.register(ws)

    try:
        # Send current state snapshot to the new client
        snapshot = await state_manager.snapshot()
        await ws.send_text(json.dumps(snapshot))

        # Keep connection alive; listen for messages from the frontend
        while True:
            data = await ws.receive_text()
            # Future: handle UI commands (e.g., manual trigger, IoT controls)
            print(f"Received from UI: {data}")

    except WebSocketDisconnect:
        pass
    finally:
        state_manager.unregister(ws)


# ── REST API ──────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Simple health check — used by Mac Mini to verify Pi is alive."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
    }


@app.get("/api/status")
async def get_status():
    """Returns current state, conversation length, and system metrics."""
    if state_manager is None:
        return {"error": "Not initialized"}

    result = {
        "state": state_manager.state.value,
        "conversation_length": len(state_manager.conversation),
        "uptime_seconds": round(time.time() - _start_time),
    }

    # Include system metrics if available
    if hasattr(state_manager, "system_metrics") and state_manager.system_metrics:
        result["system"] = state_manager.system_metrics

    return result


@app.post("/api/speak")
async def api_speak(req: SpeakRequest):
    """
    Make Pi speak text aloud. Called by Mac Mini to push voice output.
    Example: Mac sends "Dinner is ready" and Pi announces it.
    """
    if speak_fn is None:
        return {"error": "Speak function not available"}

    import asyncio
    loop = asyncio.get_event_loop()

    # Run TTS in executor to avoid blocking
    await loop.run_in_executor(None, speak_fn, req.text, req.language)

    return {"status": "ok", "text": req.text}


@app.post("/api/ask")
async def api_ask(req: AskRequest):
    """
    Send a question through CHARLI and return the answer.
    Useful for programmatic queries from Mac Mini or other clients.
    """
    if ask_fn is None:
        return {"error": "Ask function not available"}

    import asyncio
    loop = asyncio.get_event_loop()

    history = state_manager.conversation if state_manager else []
    answer = await loop.run_in_executor(
        None, ask_fn, req.question, req.language, history
    )

    # Record in conversation history
    if state_manager:
        state_manager.add_message_sync("user", req.question)
        state_manager.add_message_sync("charli", answer)

    return {"status": "ok", "question": req.question, "answer": answer}
