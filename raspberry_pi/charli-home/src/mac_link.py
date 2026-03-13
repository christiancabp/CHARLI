#!/usr/bin/env python3
"""
CHARLI Home - Mac Link (Pi↔Mac Nervous System)

Maintains a persistent WebSocket connection from the Pi to the Mac Mini.
This is the "nervous system" — it lets the Mac Mini know what the Pi is
doing (state changes) and lets the Mac push commands to the Pi.

Think of it like a phone line between two offices that's always open:
  - Pi can tell Mac: "I'm now LISTENING" or "I'm now THINKING"
  - Mac can tell Pi: "Say this out loud" or "What's your status?"
  - If the line drops, the Pi automatically redials

Features:
  - Auto-reconnect with exponential backoff
    (waits 2s, then 4s, then 8s, then 16s... up to 60s between retries)
  - Heartbeat every 30 seconds to keep the connection alive
    (some firewalls/routers close idle connections after a timeout)
  - Relays state changes from StateManager to Mac
  - Accepts commands from Mac (speak text, check status, ping)

Requires:
  CHARLI_MAC_WS_URL — WebSocket URL of the Mac Mini
  (e.g., ws://100.91.206.1:18790/ws)
  If not set, this module gracefully disables itself.
"""

import asyncio
import json
import os
import time

# websocket-client is a SYNCHRONOUS WebSocket library.
# We wrap its calls in run_in_executor() to make them non-blocking.
# In a future upgrade, we could switch to the `websockets` async library
# for a cleaner async experience.
import websocket

# ── Configuration ─────────────────────────────────────────────────────

# The Mac Mini's WebSocket URL, accessible via Tailscale.
# Empty string means "not configured" — Mac Link will be disabled.
MAC_WS_URL = os.environ.get("CHARLI_MAC_WS_URL", "")

# Send a heartbeat every 30 seconds to keep the connection alive.
# Without heartbeats, NAT routers and firewalls may close the connection
# after a period of inactivity (typically 60-300 seconds).
HEARTBEAT_INTERVAL = 30

# Reconnect backoff: start at 2 seconds, double each time, max 60 seconds.
# This is "exponential backoff" — a common pattern for retrying connections:
#   Attempt 1: wait 2s
#   Attempt 2: wait 4s
#   Attempt 3: wait 8s
#   Attempt 4: wait 16s
#   Attempt 5: wait 32s
#   Attempt 6+: wait 60s (capped)
# This prevents hammering a down server with rapid reconnect attempts.
RECONNECT_MIN = 2
RECONNECT_MAX = 60


class MacLink:
    """
    Persistent WebSocket connection from Pi to Mac Mini.

    This class manages the entire connection lifecycle:
      1. Connect to Mac Mini
      2. Send heartbeats to keep connection alive
      3. Listen for commands from Mac (speak, status, ping)
      4. If disconnected, wait and reconnect with exponential backoff
      5. Repeat forever

    Usage:
        link = MacLink(state_manager)
        link._speak_fn = speak          # inject the TTS function
        await link.run()                # runs forever, auto-reconnects
    """

    def __init__(self, state_manager):
        self._state = state_manager      # Shared state manager
        self._ws = None                  # The WebSocket connection object
        self._connected = False          # Are we currently connected?
        self._backoff = RECONNECT_MIN    # Current retry wait time (seconds)
        self._speak_fn = None            # TTS function, injected by charli_home.py

    @property
    def connected(self) -> bool:
        """Read-only property to check connection status from outside."""
        return self._connected

    # =================================================================
    # MAIN LOOP — Connect, run, reconnect forever
    # =================================================================

    async def run(self):
        """
        Main loop — connects, relays messages, reconnects on failure.
        This runs forever as one of the concurrent tasks in asyncio.gather().

        If CHARLI_MAC_WS_URL is not set, this immediately returns
        (prints a message and exits). The other subsystems keep running
        fine without the Mac Link.
        """

        # If no Mac URL configured, disable Mac Link gracefully
        if not MAC_WS_URL:
            print("ℹ️ CHARLI_MAC_WS_URL not set — Mac Link disabled")
            return

        loop = asyncio.get_event_loop()

        while True:
            try:
                print(f"🔗 Connecting to Mac Mini at {MAC_WS_URL}...")

                # _connect() is BLOCKING (it opens a TCP connection).
                # run_in_executor moves it to a background thread.
                self._ws = await loop.run_in_executor(
                    None, self._connect
                )

                if self._ws:
                    self._connected = True
                    # Reset backoff on successful connection.
                    # Next disconnect will start at 2s again.
                    self._backoff = RECONNECT_MIN
                    print("✅ Mac Link connected!")

                    # Run TWO tasks concurrently:
                    #   1. Heartbeat loop — sends "I'm alive" every 30s
                    #   2. Receive loop — listens for commands from Mac
                    # When either one fails (connection lost), both stop
                    # and we fall through to the reconnect logic below.
                    await asyncio.gather(
                        self._heartbeat_loop(),
                        self._receive_loop(),
                    )

            except asyncio.CancelledError:
                # Graceful shutdown
                break
            except Exception as e:
                print(f"⚠️ Mac Link error: {e}")

            # If we get here, we disconnected. Wait and retry.
            self._connected = False
            print(f"🔄 Reconnecting in {self._backoff}s...")
            await asyncio.sleep(self._backoff)

            # Exponential backoff: double the wait time, cap at 60s.
            # min() ensures we never wait longer than RECONNECT_MAX.
            self._backoff = min(self._backoff * 2, RECONNECT_MAX)

    # =================================================================
    # CONNECTION — Synchronous WebSocket setup
    # =================================================================

    def _connect(self):
        """
        Open a WebSocket connection to the Mac Mini (synchronous/blocking).
        Runs in a background thread via run_in_executor().

        On success: sends a "hello" message identifying the Pi, returns the ws object.
        On failure: prints error, returns None.
        """
        try:
            # websocket.create_connection() opens a TCP + WebSocket connection.
            # timeout=10 means "give up if the Mac doesn't respond within 10 seconds".
            ws = websocket.create_connection(
                MAC_WS_URL,
                timeout=10,
            )

            # Send a "hello" message so the Mac knows who just connected.
            # This is like a handshake: "Hi, I'm the Pi, and I'm currently IDLE."
            ws.send(json.dumps({
                "type": "hello",
                "device": "charli-home-pi",
                "state": self._state.state.value,
                "timestamp": time.time(),
            }))
            return ws

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None

    # =================================================================
    # HEARTBEAT — Keep the connection alive
    # =================================================================

    async def _heartbeat_loop(self):
        """
        Send a heartbeat message every 30 seconds.

        Why? WebSocket connections can silently die if:
          - A router/firewall closes idle connections
          - The Mac goes to sleep and wakes up
          - A network hiccup drops the TCP connection

        The heartbeat serves two purposes:
          1. Keeps the connection "active" so routers don't close it
          2. Detects dead connections — if the send fails, we know to reconnect
        """
        loop = asyncio.get_event_loop()
        while self._connected:
            try:
                # Send heartbeat in background thread (blocking I/O)
                await loop.run_in_executor(
                    None, self._send, {
                        "type": "heartbeat",
                        "state": self._state.state.value,
                        "timestamp": time.time(),
                    }
                )
            except Exception:
                # Send failed — connection is dead
                self._connected = False
                break

            # Wait 30 seconds before next heartbeat.
            # asyncio.sleep is non-blocking (unlike time.sleep).
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    # =================================================================
    # RECEIVE — Listen for commands from Mac
    # =================================================================

    async def _receive_loop(self):
        """
        Listen for incoming messages (commands) from the Mac Mini.

        The Mac can send commands like:
          {"type": "speak", "text": "Dinner is ready", "language": "en"}
          {"type": "status"}
          {"type": "ping"}

        This loop runs forever until the connection drops.
        """
        loop = asyncio.get_event_loop()
        while self._connected:
            try:
                # _recv() is BLOCKING — it waits for the next message.
                # run_in_executor moves it to a background thread.
                raw = await loop.run_in_executor(None, self._recv)

                if raw is None:
                    # None means the connection was closed
                    self._connected = False
                    break

                # Parse the JSON message and handle it
                msg = json.loads(raw)
                await self._handle_command(msg)

            except json.JSONDecodeError:
                # Received invalid JSON — skip it and keep listening
                continue
            except Exception:
                # Something went wrong — connection is probably dead
                self._connected = False
                break

    async def _handle_command(self, msg: dict):
        """
        Process a command received from the Mac Mini.

        Supported commands:
          "speak"  — Make the Pi say something out loud
          "status" — Respond with current state info
          "ping"   — Respond with "pong" (connection health check)
        """
        cmd_type = msg.get("type", "")

        if cmd_type == "speak" and self._speak_fn:
            # Mac wants Pi to say something through the Bluetooth speaker.
            # Example use: Mac sends "Dinner is ready" and Pi announces it.
            text = msg.get("text", "")
            language = msg.get("language", "en")
            if text:
                loop = asyncio.get_event_loop()
                # speak() is blocking, so run in executor
                await loop.run_in_executor(
                    None, self._speak_fn, text, language
                )

        elif cmd_type == "status":
            # Mac wants to know the Pi's current state.
            # Respond with state and conversation length.
            self._send({
                "type": "status_response",
                "state": self._state.state.value,
                "conversation_length": len(self._state.conversation),
                "timestamp": time.time(),
            })

        elif cmd_type == "ping":
            # Simple health check — Mac says "ping", Pi says "pong".
            # This is the most basic way to verify the connection works.
            self._send({"type": "pong", "timestamp": time.time()})

    # =================================================================
    # LOW-LEVEL I/O — Send and receive JSON messages
    # =================================================================

    def send_state(self, state_value: str):
        """
        Relay a state change to the Mac Mini.
        Called by StateManager when the voice pipeline changes state.
        """
        if self._connected:
            self._send({
                "type": "state",
                "state": state_value,
                "timestamp": time.time(),
            })

    def _send(self, data: dict):
        """
        Send a JSON message to the Mac Mini (synchronous).
        If the send fails, mark the connection as dead.
        """
        if self._ws:
            try:
                self._ws.send(json.dumps(data))
            except Exception:
                self._connected = False

    def _recv(self) -> str | None:
        """
        Receive a message from the Mac Mini (synchronous/blocking).
        Returns the raw JSON string, or None if the connection is dead.

        The timeout is set to HEARTBEAT_INTERVAL + 5 seconds.
        If we don't receive ANYTHING in that time (not even a heartbeat
        from the Mac), something is probably wrong — return a timeout
        message that gets ignored rather than blocking forever.
        """
        if self._ws:
            try:
                # Set a receive timeout slightly longer than the heartbeat interval
                self._ws.settimeout(HEARTBEAT_INTERVAL + 5)
                return self._ws.recv()
            except websocket.WebSocketTimeoutException:
                # No message received within timeout — not necessarily an error,
                # just nothing to process. Return a harmless "timeout" message.
                return '{"type": "timeout"}'
            except Exception:
                # Connection error — return None to signal "disconnected"
                return None
        return None

    def stop(self):
        """
        Clean shutdown — close the WebSocket connection.
        Called during program exit.
        """
        self._connected = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None


# ── Standalone Test ───────────────────────────────────────────────────
# Test the Mac connection:
#   export CHARLI_MAC_WS_URL=ws://100.x.x.x:18790/ws
#   python3 src/mac_link.py
if __name__ == "__main__":
    if not MAC_WS_URL:
        print("Set CHARLI_MAC_WS_URL to test Mac Link")
        print("Example: export CHARLI_MAC_WS_URL=ws://100.x.x.x:18790/ws")
    else:
        link = MacLink(None)
        print(f"Testing connection to {MAC_WS_URL}...")
        ws = link._connect()
        if ws:
            print("✅ Connected successfully!")
            ws.close()
        else:
            print("❌ Connection failed")
