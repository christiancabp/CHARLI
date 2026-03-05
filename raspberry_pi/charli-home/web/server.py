#!/usr/bin/env python3
"""
CHARLI Home - Web Server

FastAPI application that serves the JARVIS touchscreen UI
and provides a WebSocket endpoint for real-time state updates.
"""

import json
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

# The StateManager instance is injected by charli_home.py at startup
state_manager = None

app = FastAPI(title="CHARLI Home")

# Serve static files (HTML, CSS, JS) from web/static/
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    """Serve the main JARVIS UI page."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r") as f:
        html = f.read()
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


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
