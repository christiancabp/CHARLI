#!/usr/bin/env python3
"""
CHARLI Home - Mac Link (Pi↔Mac Nervous System)

Maintains a persistent WebSocket connection from the Pi to the Mac Mini.
This is the "nervous system" — it lets the Mac Mini know what the Pi is
doing (state changes) and lets the Mac push commands to the Pi (speak, etc.).

Features:
  - Auto-reconnect with exponential backoff
  - Heartbeat every 30 seconds to keep connection alive
  - Relays state changes from StateManager to Mac
  - Accepts commands from Mac (speak, status)

Think of it like a phone line between two offices that's always open.
If someone hangs up, it automatically redials.
"""

import asyncio
import json
import os
import time

# websocket-client is the sync library; we use it via run_in_executor
# for compatibility. For a future upgrade, consider using `websockets` async.
import websocket

# Mac Mini WebSocket URL (via Tailscale)
MAC_WS_URL = os.environ.get("CHARLI_MAC_WS_URL", "")

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 30

# Reconnect backoff settings
RECONNECT_MIN = 2
RECONNECT_MAX = 60


class MacLink:
    """
    Persistent connection from Pi to Mac Mini.

    Usage:
        link = MacLink(state_manager)
        await link.run()  # runs forever, auto-reconnects
    """

    def __init__(self, state_manager):
        self._state = state_manager
        self._ws = None
        self._connected = False
        self._backoff = RECONNECT_MIN
        self._speak_fn = None  # injected by charli_home.py

    @property
    def connected(self) -> bool:
        return self._connected

    async def run(self):
        """Main loop — connects, relays, reconnects on failure."""
        if not MAC_WS_URL:
            print("ℹ️ CHARLI_MAC_WS_URL not set — Mac Link disabled")
            return

        loop = asyncio.get_event_loop()

        while True:
            try:
                print(f"🔗 Connecting to Mac Mini at {MAC_WS_URL}...")
                self._ws = await loop.run_in_executor(
                    None, self._connect
                )

                if self._ws:
                    self._connected = True
                    self._backoff = RECONNECT_MIN
                    print("✅ Mac Link connected!")

                    # Run heartbeat and message handler concurrently
                    await asyncio.gather(
                        self._heartbeat_loop(),
                        self._receive_loop(),
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Mac Link error: {e}")

            # Disconnected — wait and retry
            self._connected = False
            print(f"🔄 Reconnecting in {self._backoff}s...")
            await asyncio.sleep(self._backoff)
            self._backoff = min(self._backoff * 2, RECONNECT_MAX)

    def _connect(self):
        """Synchronous WebSocket connect (runs in executor)."""
        try:
            ws = websocket.create_connection(
                MAC_WS_URL,
                timeout=10,
            )
            # Send initial hello with Pi identity
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

    async def _heartbeat_loop(self):
        """Send periodic heartbeat to keep connection alive."""
        loop = asyncio.get_event_loop()
        while self._connected:
            try:
                await loop.run_in_executor(
                    None, self._send, {
                        "type": "heartbeat",
                        "state": self._state.state.value,
                        "timestamp": time.time(),
                    }
                )
            except Exception:
                self._connected = False
                break
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def _receive_loop(self):
        """Listen for commands from Mac Mini."""
        loop = asyncio.get_event_loop()
        while self._connected:
            try:
                raw = await loop.run_in_executor(None, self._recv)
                if raw is None:
                    self._connected = False
                    break

                msg = json.loads(raw)
                await self._handle_command(msg)

            except json.JSONDecodeError:
                continue
            except Exception:
                self._connected = False
                break

    async def _handle_command(self, msg: dict):
        """Process a command from the Mac Mini."""
        cmd_type = msg.get("type", "")

        if cmd_type == "speak" and self._speak_fn:
            text = msg.get("text", "")
            language = msg.get("language", "en")
            if text:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, self._speak_fn, text, language
                )

        elif cmd_type == "status":
            self._send({
                "type": "status_response",
                "state": self._state.state.value,
                "conversation_length": len(self._state.conversation),
                "timestamp": time.time(),
            })

        elif cmd_type == "ping":
            self._send({"type": "pong", "timestamp": time.time()})

    def send_state(self, state_value: str):
        """Called by StateManager when state changes — relays to Mac."""
        if self._connected:
            self._send({
                "type": "state",
                "state": state_value,
                "timestamp": time.time(),
            })

    def _send(self, data: dict):
        """Send a JSON message to Mac Mini."""
        if self._ws:
            try:
                self._ws.send(json.dumps(data))
            except Exception:
                self._connected = False

    def _recv(self) -> str | None:
        """Receive a message from Mac Mini (blocking)."""
        if self._ws:
            try:
                self._ws.settimeout(HEARTBEAT_INTERVAL + 5)
                return self._ws.recv()
            except websocket.WebSocketTimeoutException:
                return '{"type": "timeout"}'
            except Exception:
                return None
        return None

    def stop(self):
        """Clean shutdown."""
        self._connected = False
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None


if __name__ == "__main__":
    # Quick test — tries to connect once
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
