/**
 * CHARLI Home — WebSocket Client & UI Logic
 *
 * Connects to the FastAPI WebSocket at /ws and keeps the JARVIS
 * touchscreen UI in sync with the assistant's state.
 */

(() => {
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

    let ws = null;
    let reconnectTimer = null;

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
        messages.forEach(msg => addTranscriptEntry(msg.role, msg.text));
    }

    // ── State updates ───────────────────────────────────────────────
    function applyState(state) {
        // Update label
        stateLabel.textContent = STATE_LABELS[state] || state.toUpperCase();

        // Update label color
        const color = STATE_COLORS[state] || STATE_COLORS.idle;
        stateLabel.style.color = color;
        stateLabel.style.textShadow = `0 0 8px ${color}60`;

        // Update body class for CSS overrides
        document.body.className = `state-${state}`;

        // Tell the orb to transition
        Orb.setState(state);
    }

    // ── WebSocket connection ────────────────────────────────────────
    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${window.location.host}/ws`;

        ws = new WebSocket(url);

        ws.onopen = () => {
            console.log('WebSocket connected');
            connectionDot.classList.add('connected');
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case 'snapshot':
                    applyState(data.state);
                    if (data.conversation && data.conversation.length > 0) {
                        loadConversation(data.conversation);
                    }
                    break;

                case 'state':
                    applyState(data.state);
                    break;

                case 'message':
                    addTranscriptEntry(data.role, data.text);
                    break;
            }
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            connectionDot.classList.remove('connected');
            scheduleReconnect();
        };

        ws.onerror = (err) => {
            console.error('WebSocket error:', err);
            ws.close();
        };
    }

    function scheduleReconnect() {
        if (!reconnectTimer) {
            reconnectTimer = setTimeout(() => {
                reconnectTimer = null;
                connect();
            }, 2000);
        }
    }

    // ── Initialize ──────────────────────────────────────────────────
    Orb.init('orbCanvas');
    connect();
})();
