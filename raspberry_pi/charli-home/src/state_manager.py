#!/usr/bin/env python3
"""
CHARLI Home - State Manager

Central source of truth for the assistant's current state.
Broadcasts state changes to all connected WebSocket clients
so the JARVIS UI stays in sync.

States:
  IDLE            - Waiting for wake word
  LISTENING       - Recording the user's voice
  THINKING        - Transcribing + querying CHARLI
  SPEAKING        - Playing back the response
"""

import asyncio
import json
from enum import Enum
from typing import Optional


class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class StateManager:
    """
    Holds the current state and conversation history.
    Notifies all connected WebSocket clients on every change.
    """

    def __init__(self):
        self.state: State = State.IDLE
        self.conversation: list[dict] = []   # [{role: "user"|"charli", text: "..."}]
        self._clients: set = set()           # connected WebSocket objects
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ── WebSocket client management ──────────────────────────────────

    def register(self, ws):
        """Add a WebSocket client to receive broadcasts."""
        self._clients.add(ws)

    def unregister(self, ws):
        """Remove a disconnected client."""
        self._clients.discard(ws)

    # ── State changes ────────────────────────────────────────────────

    async def set_state(self, new_state: State):
        """Update state and broadcast to all clients (call from async code)."""
        self.state = new_state
        await self._broadcast({"type": "state", "state": new_state.value})

    def set_state_sync(self, new_state: State):
        """
        Thread-safe wrapper — call from the voice pipeline thread.
        Schedules the async broadcast on the event loop.
        """
        self.state = new_state
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "state", "state": new_state.value}),
                self._loop,
            )

    # ── Conversation history ─────────────────────────────────────────

    async def add_message(self, role: str, text: str):
        """Append a message and broadcast it to clients."""
        entry = {"role": role, "text": text}
        self.conversation.append(entry)
        await self._broadcast({"type": "message", **entry})

    def add_message_sync(self, role: str, text: str):
        """Thread-safe wrapper for adding messages from the voice thread."""
        entry = {"role": role, "text": text}
        self.conversation.append(entry)
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "message", **entry}),
                self._loop,
            )

    # ── Broadcast internals ──────────────────────────────────────────

    async def _broadcast(self, data: dict):
        """Send a JSON message to every connected client."""
        if not self._clients:
            return
        payload = json.dumps(data)
        # Send to all clients; remove any that have disconnected
        dead = set()
        for ws in self._clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        self._clients -= dead

    async def snapshot(self) -> dict:
        """Full state snapshot for newly connected clients."""
        return {
            "type": "snapshot",
            "state": self.state.value,
            "conversation": self.conversation,
        }
