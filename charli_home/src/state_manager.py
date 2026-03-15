#!/usr/bin/env python3
"""
CHARLI Home - State Manager (Thin Client)

Holds the local state for pipeline coordination and the JARVIS UI.
State changes are broadcast to the local UI via a simple in-memory
list of WebSocket-like callbacks (for system_monitor compatibility).

The JARVIS UI on the touchscreen gets its real-time updates from
charli_server's WebSocket. This state manager just coordinates the
local voice pipeline steps (IDLE → LISTENING → THINKING → SPEAKING).

States:
  IDLE      - Waiting for wake word (orb = blue)
  LISTENING - Recording the user's voice (orb = cyan)
  THINKING  - Server is processing (orb = orange)
  SPEAKING  - Playing back the response (orb = gold)
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
    Local state tracking for the voice pipeline.

    Keeps conversation history in memory (for display in the JARVIS UI)
    and coordinates state transitions between pipeline steps.
    """

    def __init__(self):
        self.state: State = State.IDLE
        self.conversation: list[dict] = []
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # System metrics (populated by system_monitor.py)
        self.system_metrics: dict = {}

        # Callbacks for local broadcasting (system_monitor uses _broadcast)
        self._clients: set = set()

    # ── WebSocket Client Management ───────────────────────────────────
    # Kept for compatibility with system_monitor.py's _broadcast calls.
    # In the thin client, there are typically no local WS clients.

    def register(self, ws):
        self._clients.add(ws)

    def unregister(self, ws):
        self._clients.discard(ws)

    # ── State Changes ─────────────────────────────────────────────────

    async def set_state(self, new_state: State):
        """Update state and broadcast locally."""
        self.state = new_state
        await self._broadcast({"type": "state", "state": new_state.value})

    def set_state_sync(self, new_state: State):
        """Thread-safe version for blocking code in background threads."""
        self.state = new_state
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "state", "state": new_state.value}),
                self._loop,
            )

    # ── Conversation History ──────────────────────────────────────────

    async def add_message(self, role: str, text: str):
        """Append a message to local conversation history."""
        entry = {"role": role, "text": text}
        self.conversation.append(entry)
        await self._broadcast({"type": "message", **entry})

    def add_message_sync(self, role: str, text: str):
        """Thread-safe version."""
        entry = {"role": role, "text": text}
        self.conversation.append(entry)
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "message", **entry}),
                self._loop,
            )

    # ── Broadcast ─────────────────────────────────────────────────────

    async def _broadcast(self, data: dict):
        """Send a message to any locally connected clients."""
        if not self._clients:
            return

        payload = json.dumps(data)
        dead = set()
        for ws in self._clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        self._clients -= dead

    async def snapshot(self) -> dict:
        """Full state for newly connected clients."""
        return {
            "type": "snapshot",
            "state": self.state.value,
            "conversation": self.conversation,
        }
