#!/usr/bin/env python3
"""
CHARLI Home - State Manager

The "single source of truth" for the entire system.
Every subsystem reads from and writes to this one object.

Think of it like a Redux store in React:
  - There's ONE state object (not copies scattered everywhere)
  - When state changes, all "subscribers" (WebSocket clients) get notified
  - State transitions follow a predictable pattern:
      IDLE → LISTENING → THINKING → SPEAKING → IDLE → ...

This module also tracks conversation history (what you said and what
CHARLI replied), which the JARVIS UI displays as a scrolling transcript.

States:
  IDLE            - Waiting for wake word (orb = blue)
  LISTENING       - Recording the user's voice (orb = cyan)
  THINKING        - Transcribing + querying CHARLI (orb = orange)
  SPEAKING        - Playing back the response (orb = gold)
"""

import asyncio
import json
from enum import Enum        # Python's way to define a fixed set of constants
from typing import Optional   # Type hints (like TypeScript's `string | null`)


# ── State Enum ────────────────────────────────────────────────────────
# An Enum is like a TypeScript enum:
#   enum State { IDLE = "idle", LISTENING = "listening", ... }
#
# By inheriting from BOTH str and Enum, we get string-compatible values.
# This means State.IDLE == "idle" is True, which is handy for JSON.
class State(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class StateManager:
    """
    Holds the current state and conversation history.
    Notifies all connected WebSocket clients on every change.

    Two sets of methods exist for the same operations:
      - ASYNC versions: set_state(), add_message()
        → Used from async code (web server, orchestrator after await)
      - SYNC versions: set_state_sync(), add_message_sync()
        → Used from blocking code running in background threads
        → These safely schedule the WebSocket broadcast on the event loop

    Why two versions?
      Python has a strict rule: you can only use `await` inside async functions.
      The voice pipeline's blocking functions (record, transcribe, speak) run
      in background threads via run_in_executor(). From those threads, you
      CAN'T use await. So the _sync versions use asyncio.run_coroutine_threadsafe()
      to "throw the message over the fence" to the event loop thread.

      In JavaScript, you don't need this because everything runs on one thread.
      Python's threading model requires this extra care.
    """

    def __init__(self):
        # Current state of the assistant (starts idle, waiting for wake word)
        self.state: State = State.IDLE

        # Conversation history — a list of messages like:
        #   [{"role": "user", "text": "What's the weather?"},
        #    {"role": "charli", "text": "It's 72 degrees."}]
        # This is similar to a chat messages array in a React app.
        self.conversation: list[dict] = []

        # Set of connected WebSocket objects (browsers, TUI clients).
        # When state changes, we loop through this set and send updates.
        # A set (not list) because we need fast add/remove and no duplicates.
        self._clients: set = set()

        # Reference to the asyncio event loop. Needed by the _sync methods
        # to schedule broadcasts from background threads.
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ── WebSocket Client Management ───────────────────────────────────
    # These are called by the web server when browsers connect/disconnect.

    def register(self, ws):
        """
        Add a WebSocket client to receive broadcasts.
        Called when a browser opens the JARVIS UI or TUI connects.
        Like: eventEmitter.on('stateChange', ws.send)
        """
        self._clients.add(ws)

    def unregister(self, ws):
        """
        Remove a disconnected client.
        .discard() is like .delete() in JS Sets — doesn't error if missing.
        """
        self._clients.discard(ws)

    # ── State Changes ─────────────────────────────────────────────────

    async def set_state(self, new_state: State):
        """
        Update state and broadcast to all clients.
        Call this from ASYNC code (like the voice_pipeline after an await).

        When this runs, every connected browser/TUI instantly receives:
          {"type": "state", "state": "listening"}
        and updates their UI accordingly.
        """
        self.state = new_state
        await self._broadcast({"type": "state", "state": new_state.value})

    def set_state_sync(self, new_state: State):
        """
        Thread-safe version — call from blocking code in background threads.

        The voice pipeline runs blocking functions (like record_audio) in
        a thread pool via run_in_executor(). From that thread, we can't
        use `await`. Instead, we use asyncio.run_coroutine_threadsafe()
        to schedule the broadcast on the main event loop.

        It's like postMessage() in a Web Worker — you can't directly
        call DOM methods from a worker, so you send a message to the
        main thread which handles it.
        """
        self.state = new_state
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "state", "state": new_state.value}),
                self._loop,
            )

    # ── Conversation History ──────────────────────────────────────────

    async def add_message(self, role: str, text: str):
        """
        Append a message to the conversation and broadcast it.
        role is "user" or "charli".

        The broadcast sends it to all connected UIs, which append it
        to their transcript display in real time.
        """
        entry = {"role": role, "text": text}
        self.conversation.append(entry)
        await self._broadcast({"type": "message", **entry})

    def add_message_sync(self, role: str, text: str):
        """
        Thread-safe version — same as set_state_sync() pattern.
        Used by the voice pipeline thread to record what was said.
        """
        entry = {"role": role, "text": text}
        self.conversation.append(entry)
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "message", **entry}),
                self._loop,
            )

    # ── Broadcast (Internal) ──────────────────────────────────────────

    async def _broadcast(self, data: dict):
        """
        Send a JSON message to EVERY connected WebSocket client.

        This is like a pub/sub pattern:
          - Clients subscribe by connecting to /ws
          - Every state change or new message gets published to all of them

        If a client has disconnected (e.g., browser tab closed), the
        send will fail. We collect those "dead" clients and remove them.
        We use a separate set to avoid modifying self._clients while
        iterating over it (that would cause a RuntimeError in Python).
        """
        if not self._clients:
            return

        # Convert the Python dict to a JSON string once, then send
        # the same string to everyone (more efficient than converting N times)
        payload = json.dumps(data)

        # Track clients that have disconnected so we can clean them up
        dead = set()
        for ws in self._clients:
            try:
                await ws.send_text(payload)
            except Exception:
                # Client disconnected — mark for removal
                dead.add(ws)

        # Remove dead clients (set subtraction: A -= B removes all B items from A)
        self._clients -= dead

    async def snapshot(self) -> dict:
        """
        Full state snapshot for newly connected clients.

        When a browser first opens the JARVIS UI, it needs to know:
          - What state are we in? (IDLE? SPEAKING?)
          - What's been said so far? (the conversation history)

        This is like the "initial state" in Redux — the first render
        gets the full picture, then subsequent updates are incremental.
        """
        return {
            "type": "snapshot",
            "state": self.state.value,
            "conversation": self.conversation,
        }
