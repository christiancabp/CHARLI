#!/usr/bin/env python3
"""
CHARLI Home - Web Server

FastAPI application that serves the JARVIS touchscreen UI and provides
both WebSocket (real-time state updates) and REST API endpoints.

The web server does THREE things:
  1. Serves the JARVIS UI (HTML/CSS/JS) as static files → the touchscreen
  2. Provides a WebSocket at /ws for real-time state updates → the orb reacts
  3. Exposes REST API endpoints:
       POST /api/speak      — Make Pi speak text aloud (local TTS)
       POST /api/ask        — Send a question through CHARLI Server
       POST /api/ask-vision — Send text + image through CHARLI Server
       GET  /api/status     — Get current state + system metrics
       GET  /health         — Simple health check
"""

import json
import os
import time
import asyncio
import base64

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

# ── Dependency Injection ──────────────────────────────────────────────
# These module-level variables are set by charli_home.py at startup.
state_manager = None
speak_fn = None         # Local TTS (espeak-ng) for push-to-speak
ask_fn = None           # Ask via CHARLI Server → returns text
speak_text_fn = None    # TTS via CHARLI Server → returns audio file path

# ── Create the FastAPI App ────────────────────────────────────────────
app = FastAPI(title="CHARLI Home")

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

_start_time = time.time()


# ── Request Models ────────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    text: str
    language: str = "en"


class AskRequest(BaseModel):
    question: str
    language: str = "en"


class AskVisionRequest(BaseModel):
    question: str
    language: str = "en"
    image_base64: Optional[str] = None
    image_mime: str = "image/jpeg"


# =====================================================================
# PAGES
# =====================================================================

@app.get("/")
async def root():
    """Serve the main JARVIS UI page."""
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

    Protocol:
      Server sends (on connect): {"type": "snapshot", "state": "idle", "conversation": [...]}
      Server sends (on change):  {"type": "state", "state": "listening"}
      Server sends (on message): {"type": "message", "role": "user", "text": "..."}
      Server sends (metrics):    {"type": "system", "metrics": {...}}
    """
    await ws.accept()

    if state_manager is None:
        await ws.close(reason="State manager not initialized")
        return

    state_manager.register(ws)

    try:
        snapshot = await state_manager.snapshot()
        await ws.send_text(json.dumps(snapshot))

        while True:
            data = await ws.receive_text()
            print(f"Received from UI: {data}")

    except WebSocketDisconnect:
        pass
    finally:
        state_manager.unregister(ws)


# =====================================================================
# REST API
# =====================================================================

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - _start_time),
    }


@app.get("/api/status")
async def get_status():
    """Current state, conversation length, system metrics."""
    if state_manager is None:
        return {"error": "Not initialized"}

    result = {
        "state": state_manager.state.value,
        "conversation_length": len(state_manager.conversation),
        "uptime_seconds": round(time.time() - _start_time),
    }

    if hasattr(state_manager, "system_metrics") and state_manager.system_metrics:
        result["system"] = state_manager.system_metrics

    return result


@app.post("/api/speak")
async def api_speak(req: SpeakRequest):
    """
    Make the Pi speak text aloud through the local speaker.
    Uses local espeak-ng directly (no server round-trip needed for push-to-speak).
    """
    if speak_fn is None:
        return {"error": "Speak function not available"}

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, speak_fn, req.text, req.language)
    return {"status": "ok", "text": req.text}


@app.post("/api/ask")
async def api_ask(req: AskRequest):
    """
    Send a text question to CHARLI Server and return the answer.
    The question goes through the central server (Mac Mini) which handles
    the LLM query. Conversation history is managed server-side.
    """
    if ask_fn is None:
        return {"error": "Ask function not available"}

    loop = asyncio.get_event_loop()

    answer = await loop.run_in_executor(
        None, ask_fn, req.question, req.language
    )

    # Update local conversation history for the web UI
    if state_manager:
        state_manager.add_message_sync("user", req.question)
        state_manager.add_message_sync("charli", answer)

    return {"status": "ok", "question": req.question, "answer": answer}


@app.post("/api/ask-vision")
async def api_ask_vision(req: AskVisionRequest):
    """
    Send a text + image question to CHARLI Server.
    Supports vision queries from the Pi (if a camera is attached).
    """
    # Import here to avoid circular imports
    from src.charli_server_client import ask_charli_vision

    loop = asyncio.get_event_loop()

    answer = await loop.run_in_executor(
        None, ask_charli_vision, req.question, req.language,
        req.image_base64, req.image_mime,
    )

    if state_manager:
        state_manager.add_message_sync("user", req.question)
        state_manager.add_message_sync("charli", answer)

    return {
        "status": "ok",
        "question": req.question,
        "answer": answer,
        "vision": req.image_base64 is not None,
    }
