#!/usr/bin/env python3
"""
CHARLI Home - TUI Companion (Terminal User Interface)

A terminal-based monitoring dashboard that connects to CHARLI's WebSocket
and displays live state, conversation transcript, and system metrics.
Perfect for SSH sessions — no browser needed!

Think of it like the JARVIS web UI, but running in your terminal.
Both connect to the same /ws WebSocket endpoint, so they always
show the same data.

Aesthetic: "Cyberdeck" — Copper/Brass, Amber, Deep Space Blue.
Inspired by retro-futuristic terminal interfaces.

Usage:
    python3 tui/charli_tui.py                      # connects to localhost:8080
    python3 tui/charli_tui.py --host charli-home    # remote Pi via Tailscale
    python3 tui/charli_tui.py --host 192.168.1.5    # remote Pi via IP

Keyboard shortcuts:
    q — Quit the TUI
    c — Clear the transcript

Learning moment:
    Textual uses CSS-like styling — just like your web work!
    Compare the CHARLI_CSS string below with the web UI's charli.css.
    Same concepts (colors, padding, layout), different target (terminal vs browser).
    Textual is like React for the terminal — components, state, event handlers.
"""

import argparse   # Parse command-line arguments (like yargs/commander in Node)
import asyncio
import json
import sys
import os

# ── Textual Imports ───────────────────────────────────────────────────
# Textual is a Python TUI framework. Think of it like React for the terminal:
#   - App         = your React App component
#   - compose()   = your render() method — returns the widget tree
#   - reactive()  = useState() — triggers re-renders when values change
#   - CSS         = styled-components but for terminal widgets
#   - Widgets     = built-in components (Label, Header, Footer, etc.)
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Static, RichLog, Label
from textual.reactive import reactive

# Add parent dir to path so we can import from src/ if needed.
# sys.path is like NODE_PATH — it tells Python where to find modules.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =====================================================================
# THEME — Cyberdeck CSS for the Terminal
# =====================================================================
# This CSS is applied to the terminal widgets, just like how charli.css
# is applied to HTML elements in the browser. Same concepts!
#
# Key differences from web CSS:
#   - Colors work the same way (hex codes, color names)
#   - "dock: top" is like "position: fixed; top: 0"
#   - "height: 1fr" is like "flex: 1" (take remaining space)
#   - "#id" selectors work the same as web CSS
#   - ".class" selectors work the same as web CSS
#
# Cyberdeck palette:
#   Copper/Brass:  #B87333  (status bar text, headers)
#   Amber:         #FFB000  (CHARLI's messages, state display)
#   Deep Space:    #0B1026  (background)
#   Cyan accent:   #00d4ff  (user messages, listening state)

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

# ── State Display Styles ─────────────────────────────────────────────
# Maps each state to a (label, color) tuple.
# These match the web UI's orb colors:
#   idle     = blue    (waiting for wake word)
#   listening = cyan   (recording your voice)
#   thinking = orange  (processing with Whisper + LLM)
#   speaking = gold    (playing back the response)
STATE_STYLES = {
    "idle":      ("IDLE", "#0088cc"),
    "listening": ("LISTENING", "#00d4ff"),
    "thinking":  ("THINKING", "#ff8c00"),
    "speaking":  ("SPEAKING", "#ffc845"),
}


# =====================================================================
# THE TUI APP
# =====================================================================

class CharliTUI(App):
    """
    CHARLI Home Terminal UI — connects via WebSocket to the voice pipeline.

    This is a Textual App, which is like a React App component:
      - CSS class property = global styles (like a CSS file)
      - compose() = render() — builds the widget tree
      - on_mount() = componentDidMount() — runs after the UI is ready
      - reactive properties = useState() — auto-update the UI when changed

    The app connects to the same /ws WebSocket as the browser UI and
    processes the same message types: snapshot, state, message, system.
    """

    # CSS for the entire app (applied to all widgets)
    CSS = CHARLI_CSS

    # Title shown in the terminal header bar
    TITLE = "C.H.A.R.L.I. Home"
    SUB_TITLE = "Desk Hub Monitor"

    # Keyboard bindings — like addEventListener('keydown', ...)
    # Each tuple: (key, action_method_name, description_for_footer)
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_transcript", "Clear"),
    ]

    # ── Reactive State ────────────────────────────────────────────
    # These are like useState() in React — when the value changes,
    # Textual automatically re-renders the affected widgets.
    #
    # Example: when self.current_state = "listening", Textual knows
    # to update any widget that depends on current_state.
    current_state = reactive("idle")
    cpu_temp = reactive("-")
    ram_percent = reactive("-")
    tailscale = reactive("-")
    connected = reactive(False)

    def __init__(self, host: str = "localhost", port: int = 8080):
        super().__init__()
        self._host = host    # CHARLI server hostname
        self._port = port    # CHARLI server port (default 8080)
        self._ws = None      # WebSocket connection object

    # ── Build the UI Layout ───────────────────────────────────────
    def compose(self) -> ComposeResult:
        """
        Build the widget tree — like render() in React.

        Layout (top to bottom):
          ┌─────────────────────────────────────────┐
          │ Header (Textual built-in)                │
          ├─────────────────────────────────────────┤
          │ Status Bar: CPU | RAM | NET | WS status  │
          ├─────────────────────────────────────────┤
          │ State Display: [ LISTENING ]             │
          ├─────────────────────────────────────────┤
          │ Transcript Log (scrollable)              │
          │   YOU: What's the weather?               │
          │   CHARLI: It's 72 degrees and sunny.     │
          ├─────────────────────────────────────────┤
          │ Bottom Bar: connection info               │
          ├─────────────────────────────────────────┤
          │ Footer: keyboard shortcuts               │
          └─────────────────────────────────────────┘

        yield is Python's way of "returning" multiple items one at a time.
        In React terms, compose() returns a JSX tree:
          return (<Header/><StatusBar/><StateDisplay/><Transcript/><Footer/>)
        """

        # Built-in header widget (shows app title + subtitle)
        yield Header()

        # Status bar showing system metrics (CPU temp, RAM, network, WS status)
        # Horizontal is like <div style="display: flex; flex-direction: row">
        with Horizontal(id="status-bar"):
            yield Label("CPU: --°C", id="cpu-temp", classes="label")
            yield Label("  |  ", classes="label")
            yield Label("RAM: --%", id="ram-usage", classes="label")
            yield Label("  |  ", classes="label")
            yield Label("NET: --", id="net-status", classes="label")
            yield Label("  |  ", classes="label")
            yield Label("WS: disconnected", id="ws-status", classes="label")

        # Big state display in the center — shows current state with color
        yield Static("[ IDLE ]", id="state-display")

        # Scrollable transcript log — shows conversation messages
        # RichLog supports Rich markup (like HTML but for terminals):
        #   [cyan]text[/cyan] renders as cyan-colored text
        yield RichLog(id="transcript", highlight=True, markup=True)

        # Bottom bar showing which server we're connected to
        with Horizontal(id="metrics-bar"):
            yield Label(f"🔗 {self._host}:{self._port}", classes="label")

        # Built-in footer widget (shows keyboard shortcut hints)
        yield Footer()

    # ── Lifecycle: After Mount ────────────────────────────────────
    async def on_mount(self) -> None:
        """
        Called after the UI is rendered — like componentDidMount() in React.
        Starts the WebSocket connection loop as a background worker.

        run_worker() is Textual's way to run an async task in the background
        without blocking the UI. It's like starting a goroutine or a Web Worker.
        exclusive=True means "cancel any previous worker before starting this one."
        """
        self.run_worker(self._ws_loop(), exclusive=True)

    # ── WebSocket Connection Loop ─────────────────────────────────
    async def _ws_loop(self):
        """
        Connect to CHARLI's WebSocket and process messages forever.
        Auto-reconnects every 3 seconds if the connection drops.

        This is the TUI equivalent of the WebSocket client in charli.js:
          const ws = new WebSocket('ws://localhost:8080/ws');
          ws.onmessage = (event) => { handleMessage(JSON.parse(event.data)) };
        """

        # Import websockets here (not at top of file) so the app can still
        # load and show a helpful error if the package isn't installed.
        try:
            import websockets
        except ImportError:
            self.query_one("#transcript", RichLog).write(
                "[red]Error: websockets not installed. Run: pip install websockets[/red]"
            )
            return

        # Infinite reconnection loop
        while True:
            try:
                # Build the WebSocket URL from host and port
                url = f"ws://{self._host}:{self._port}/ws"
                self.connected = True
                self.query_one("#ws-status").update("WS: connected")

                # Connect and listen for messages.
                # `async with` automatically closes the connection when done.
                # `async for raw in ws` yields each message as it arrives.
                # This is like: ws.addEventListener('message', callback)
                async with websockets.connect(url) as ws:
                    self._ws = ws
                    async for raw in ws:
                        msg = json.loads(raw)
                        self._handle_message(msg)

            except asyncio.CancelledError:
                # TUI is shutting down — stop reconnecting
                break
            except Exception as e:
                # Connection lost — show error and retry in 3 seconds
                self.connected = False
                self.query_one("#ws-status").update("WS: disconnected")
                transcript = self.query_one("#transcript", RichLog)
                transcript.write(f"[dim]Connection lost: {e}. Retrying in 3s...[/dim]")
                await asyncio.sleep(3)

    # ── Message Handler ───────────────────────────────────────────
    def _handle_message(self, msg: dict):
        """
        Process a WebSocket message from the CHARLI server.

        Message types (same as what the browser UI receives):
          "snapshot" — Full state + conversation history (sent on connect)
          "state"    — State change (e.g., idle → listening)
          "message"  — New conversation message (user said X, CHARLI said Y)
          "system"   — System metrics update (CPU temp, RAM, etc.)
        """
        msg_type = msg.get("type", "")

        if msg_type == "snapshot":
            # Initial state dump — update everything at once.
            # This ensures the TUI shows the correct state even if
            # you connect mid-conversation.
            self._update_state(msg.get("state", "idle"))
            for entry in msg.get("conversation", []):
                self._add_transcript(entry["role"], entry["text"])

        elif msg_type == "state":
            # Voice pipeline state changed (e.g., IDLE → LISTENING)
            self._update_state(msg.get("state", "idle"))

        elif msg_type == "message":
            # New message in the conversation
            self._add_transcript(msg.get("role", "?"), msg.get("text", ""))

        elif msg_type == "system":
            # System metrics update from system_monitor.py
            self._update_metrics(msg.get("metrics", {}))

    # ── UI Update Methods ─────────────────────────────────────────

    def _update_state(self, state: str):
        """
        Update the state display with the appropriate label and color.
        For example: state="listening" → shows "[ LISTENING ]" in cyan.
        """
        self.current_state = state

        # Look up the label and color for this state
        label, color = STATE_STYLES.get(state, ("UNKNOWN", "#888"))

        # Update the Static widget's text and color
        display = self.query_one("#state-display", Static)
        display.update(f"[ {label} ]")
        display.styles.color = color

    def _add_transcript(self, role: str, text: str):
        """
        Add a message to the transcript log.
        User messages appear in cyan, CHARLI messages in amber.

        Rich markup tags [cyan]...[/cyan] work like HTML tags but
        for terminal rendering. They're part of the Rich library
        that Textual is built on.
        """
        transcript = self.query_one("#transcript", RichLog)
        if role == "user":
            transcript.write(f"[cyan]YOU:[/cyan] {text}")
        else:
            transcript.write(f"[#FFB000]CHARLI:[/#FFB000] {text}")

    def _update_metrics(self, metrics: dict):
        """
        Update system metrics in the status bar.
        Called every 10 seconds when system_monitor broadcasts metrics.
        """
        # CPU temperature (only update if we got a valid reading)
        temp = metrics.get("cpu_temp", -1)
        if temp >= 0:
            self.query_one("#cpu-temp").update(f"CPU: {temp}°C")

        # RAM usage percentage
        ram = metrics.get("ram_percent", -1)
        if ram >= 0:
            self.query_one("#ram-usage").update(f"RAM: {ram}%")

        # Tailscale VPN status
        net = metrics.get("tailscale", "unknown")
        self.query_one("#net-status").update(f"NET: {net}")

    # ── Actions (triggered by keyboard shortcuts) ─────────────────

    def action_clear_transcript(self):
        """Clear the transcript log. Triggered by pressing 'c'."""
        self.query_one("#transcript", RichLog).clear()


# =====================================================================
# ENTRY POINT
# =====================================================================

def main():
    """
    Parse command-line arguments and start the TUI app.

    argparse is Python's built-in argument parser — like yargs or
    commander in Node.js.

    Examples:
      python3 tui/charli_tui.py                    # localhost:8080
      python3 tui/charli_tui.py --host charli-home  # remote Pi
      python3 tui/charli_tui.py --port 9090         # custom port
    """
    parser = argparse.ArgumentParser(description="CHARLI Home TUI")
    parser.add_argument("--host", default="localhost", help="Pi hostname/IP")
    parser.add_argument("--port", type=int, default=8080, help="Web server port")
    args = parser.parse_args()

    # Create and run the Textual app.
    # app.run() starts the terminal UI event loop (blocks until quit).
    # This is like ReactDOM.render(<App/>) — it takes over the terminal.
    app = CharliTUI(host=args.host, port=args.port)
    app.run()


# This block runs when you execute the file directly:
#   python3 tui/charli_tui.py
# But NOT when it's imported as a module by another file.
if __name__ == "__main__":
    main()
