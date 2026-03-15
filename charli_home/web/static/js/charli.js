/**
 * CHARLI Home — WebSocket Client & UI Logic (Thin Client)
 *
 * Connects to the central CHARLI Server via Socket.IO for real-time
 * state updates. The server broadcasts state changes and messages
 * from ALL devices — we filter for our desk hub's events.
 *
 * The server URL and API key are configured below. On the Pi, these
 * match the CHARLI_SERVER_URL and CHARLI_API_KEY env vars.
 */

(() => {
    // ── Configuration ─────────────────────────────────────────────
    // The CHARLI Server URL. On the Pi, this is the Mac Mini's
    // Tailscale address. For local dev, use localhost.
    //
    // To override: set window.CHARLI_SERVER_URL before this script loads,
    // or edit this default value.
    const SERVER_URL = window.CHARLI_SERVER_URL || 'http://charli-server:3000';
    const API_KEY = window.CHARLI_API_KEY || '';

    // ── DOM elements ────────────────────────────────────────────────
    const transcript    = document.getElementById('transcript');
    const stateLabel    = document.getElementById('stateLabel');
    const connectionDot = document.getElementById('connectionDot');
    const clockEl       = document.getElementById('clock');

    // ── State color map (matches CSS vars) ──────────────────────────
    const STATE_COLORS = {
        idle:      '#0088cc',
        listening: '#00d4ff',
        thinking:  '#ff8c00',
        speaking:  '#ffc845',
    };

    const STATE_LABELS = {
        idle:      'IDLE',
        listening: 'LISTENING',
        thinking:  'THINKING',
        speaking:  'SPEAKING',
    };

    let socket = null;

    // ── Clock ───────────────────────────────────────────────────────
    function updateClock() {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit', second: '2-digit',
            hour12: false,
        });
    }
    setInterval(updateClock, 1000);
    updateClock();

    // ── Transcript management ───────────────────────────────────────
    function addTranscriptEntry(role, text) {
        const entry = document.createElement('div');
        entry.className = `transcript-entry ${role}`;

        const tag = document.createElement('span');
        tag.className = 'role-tag';
        tag.textContent = role === 'user' ? 'YOU' : 'CHARLI';

        const body = document.createElement('span');
        body.textContent = text;

        entry.appendChild(tag);
        entry.appendChild(body);
        transcript.appendChild(entry);

        // Auto-scroll to bottom
        transcript.scrollTop = transcript.scrollHeight;
    }

    function loadConversation(messages) {
        // Clear everything except the initial system message
        while (transcript.children.length > 1) {
            transcript.removeChild(transcript.lastChild);
        }
        messages.forEach(msg => {
            // Server uses "role" + "content", local uses "role" + "text"
            const role = msg.role === 'assistant' ? 'charli' : msg.role;
            const text = msg.content || msg.text;
            if (text) addTranscriptEntry(role, text);
        });
    }

    // ── State updates ───────────────────────────────────────────────
    function applyState(state) {
        stateLabel.textContent = STATE_LABELS[state] || state.toUpperCase();

        const color = STATE_COLORS[state] || STATE_COLORS.idle;
        stateLabel.style.color = color;
        stateLabel.style.textShadow = `0 0 8px ${color}60`;

        document.body.className = `state-${state}`;
        Orb.setState(state);
    }

    // ── Socket.IO connection to CHARLI Server ────────────────────────
    function connect() {
        console.log(`Connecting to CHARLI Server: ${SERVER_URL}/events`);

        socket = io(`${SERVER_URL}/events`, {
            auth: { apiKey: API_KEY },
            query: { apiKey: API_KEY },
            transports: ['websocket', 'polling'],
            reconnection: true,
            reconnectionDelay: 2000,
            reconnectionAttempts: Infinity,
        });

        socket.on('connect', () => {
            console.log('Connected to CHARLI Server');
            connectionDot.classList.add('connected');
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from CHARLI Server');
            connectionDot.classList.remove('connected');
        });

        // ── Server Events ────────────────────────────────────────

        // Snapshot: full state + conversation on first connect
        socket.on('snapshot', (data) => {
            applyState(data.state);
            if (data.conversation && data.conversation.length > 0) {
                loadConversation(data.conversation);
            }
        });

        // Device state change (from any device)
        socket.on('device:state', (data) => {
            applyState(data.state);
        });

        // New message (from any device)
        socket.on('device:message', (data) => {
            const role = data.role === 'assistant' ? 'charli' : data.role;
            addTranscriptEntry(role, data.content);
        });

        // Speak command from server (e.g., another device pushing audio)
        socket.on('command:speak', (data) => {
            console.log('Speak command:', data.text);
            // The Pi handles this in charli_home.py, not the UI
        });
    }

    // ── Initialize ──────────────────────────────────────────────────
    Orb.init('orbCanvas');
    connect();
})();
