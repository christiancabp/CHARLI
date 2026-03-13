#!/usr/bin/env python3
"""
CHARLI Home - TUI Companion

A Textual-based Terminal UI that connects to the same /ws WebSocket
as the browser UI. Displays live state, conversation transcript, and
system metrics — all from the comfort of an SSH session.

Aesthetic: "Cyberdeck" — Copper/Brass, Amber, Deep Space Blue.

Usage:
    python3 tui/charli_tui.py                    # connects to localhost:8080
    python3 tui/charli_tui.py --host 192.168.1.5  # connects to remote Pi

Learning moment: Textual uses CSS-like styling (just like your web work!)
but for terminal apps. It's like React for the terminal — components,
state, event handlers, and even hot-reloading CSS.
"""

import argparse
import asyncio
import json
import sys
import os

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, RichLog, Label
from textual.reactive import reactive

# Add parent dir to path so we can run from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Theme Colors ──────────────────────────────────────────────────────
# Cyberdeck palette matching the plan:
#   Copper/Brass: #B87333
#   Amber:        #FFB000
#   Deep Space:   #0B1026
#   Cyan accent:  #00d4ff

CHARLI_CSS = """
Screen {
    background: #0B1026;
}

#status-bar {
    dock: top;
    height: 3;
    background: #111428;
    color: #B87333;
    padding: 0 2;
}

#status-bar .label {
    color: #B87333;
}

#state-display {
    width: 100%;
    height: 3;
    content-align: center middle;
    text-align: center;
    background: #0f1630;
    color: #FFB000;
    text-style: bold;
}

#transcript {
    height: 1fr;
    background: #0B1026;
    border: solid #1a2040;
    padding: 1;
}

#transcript .user-msg {
    color: #00d4ff;
}

#transcript .charli-msg {
    color: #FFB000;
}

#metrics-bar {
    dock: bottom;
    height: 3;
    background: #111428;
    color: #666;
    padding: 0 2;
}
"""

# State display colors
STATE_STYLES = {
    "idle":      ("IDLE", "#0088cc"),
    "listening": ("LISTENING", "#00d4ff"),
    "thinking":  ("THINKING", "#ff8c00"),
    "speaking":  ("SPEAKING", "#ffc845"),
}


class CharliTUI(App):
    """CHARLI Home Terminal UI — connects via WebSocket to the voice pipeline."""

    CSS = CHARLI_CSS
    TITLE = "C.H.A.R.L.I. Home"
    SUB_TITLE = "Desk Hub Monitor"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_transcript", "Clear"),
    ]

    # Reactive state
    current_state = reactive("idle")
    cpu_temp = reactive("-")
    ram_percent = reactive("-")
    tailscale = reactive("-")
    connected = reactive(False)

    def __init__(self, host: str = "localhost", port: int = 8080):
        super().__init__()
        self._host = host
        self._port = port
        self._ws = None

    def compose(self) -> ComposeResult:
        yield Header()

        # Status bar with system metrics
        with Horizontal(id="status-bar"):
            yield Label("CPU: --°C", id="cpu-temp", classes="label")
            yield Label("  |  ", classes="label")
            yield Label("RAM: --%", id="ram-usage", classes="label")
            yield Label("  |  ", classes="label")
            yield Label("NET: --", id="net-status", classes="label")
            yield Label("  |  ", classes="label")
            yield Label("WS: disconnected", id="ws-status", classes="label")

        # State display
        yield Static("[ IDLE ]", id="state-display")

        # Transcript log
        yield RichLog(id="transcript", highlight=True, markup=True)

        # Bottom bar with connection info
        with Horizontal(id="metrics-bar"):
            yield Label(f"🔗 {self._host}:{self._port}", classes="label")

        yield Footer()

    async def on_mount(self) -> None:
        """Start WebSocket connection when the app mounts."""
        self.run_worker(self._ws_loop(), exclusive=True)

    async def _ws_loop(self):
        """Connect to WebSocket and process messages forever."""
        # Import here to avoid issues if websockets isn't installed
        try:
            import websockets
        except ImportError:
            self.query_one("#transcript", RichLog).write(
                "[red]Error: websockets not installed. Run: pip install websockets[/red]"
            )
            return

        while True:
            try:
                url = f"ws://{self._host}:{self._port}/ws"
                self.connected = True
                self.query_one("#ws-status").update("WS: connected")

                async with websockets.connect(url) as ws:
                    self._ws = ws
                    async for raw in ws:
                        msg = json.loads(raw)
                        self._handle_message(msg)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.connected = False
                self.query_one("#ws-status").update("WS: disconnected")
                transcript = self.query_one("#transcript", RichLog)
                transcript.write(f"[dim]Connection lost: {e}. Retrying in 3s...[/dim]")
                await asyncio.sleep(3)

    def _handle_message(self, msg: dict):
        """Process a WebSocket message from the CHARLI server."""
        msg_type = msg.get("type", "")

        if msg_type == "snapshot":
            self._update_state(msg.get("state", "idle"))
            for entry in msg.get("conversation", []):
                self._add_transcript(entry["role"], entry["text"])

        elif msg_type == "state":
            self._update_state(msg.get("state", "idle"))

        elif msg_type == "message":
            self._add_transcript(msg.get("role", "?"), msg.get("text", ""))

        elif msg_type == "system":
            self._update_metrics(msg.get("metrics", {}))

    def _update_state(self, state: str):
        """Update the state display with color."""
        self.current_state = state
        label, color = STATE_STYLES.get(state, ("UNKNOWN", "#888"))
        display = self.query_one("#state-display", Static)
        display.update(f"[ {label} ]")
        display.styles.color = color

    def _add_transcript(self, role: str, text: str):
        """Add a message to the transcript log."""
        transcript = self.query_one("#transcript", RichLog)
        if role == "user":
            transcript.write(f"[cyan]YOU:[/cyan] {text}")
        else:
            transcript.write(f"[#FFB000]CHARLI:[/#FFB000] {text}")

    def _update_metrics(self, metrics: dict):
        """Update system metrics in the status bar."""
        temp = metrics.get("cpu_temp", -1)
        if temp >= 0:
            self.query_one("#cpu-temp").update(f"CPU: {temp}°C")

        ram = metrics.get("ram_percent", -1)
        if ram >= 0:
            self.query_one("#ram-usage").update(f"RAM: {ram}%")

        net = metrics.get("tailscale", "unknown")
        self.query_one("#net-status").update(f"NET: {net}")

    def action_clear_transcript(self):
        """Clear the transcript log."""
        self.query_one("#transcript", RichLog).clear()


def main():
    parser = argparse.ArgumentParser(description="CHARLI Home TUI")
    parser.add_argument("--host", default="localhost", help="Pi hostname/IP")
    parser.add_argument("--port", type=int, default=8080, help="Web server port")
    args = parser.parse_args()

    app = CharliTUI(host=args.host, port=args.port)
    app.run()


if __name__ == "__main__":
    main()
