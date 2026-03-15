# Device Migration Guide

How to point existing CHARLI devices to the new central server.

## Prerequisites

1. CHARLI Server running on Mac Mini (`npm run start:dev` in `charli_server/`)
2. Python sidecar running (`python3 sidecar.py` in `charli_server/sidecar/`)
3. Devices registered and API keys generated (`npx ts-node prisma/seed.ts`)

## Pi Desk Hub (charli-home)

### What Changed

The Pi is now a **thin client**. It keeps:
- Wake word detection (Porcupine)
- Audio recording (USB mic)
- Audio playback (Bluetooth speaker)
- JARVIS web UI (touchscreen — connects to server via Socket.IO)
- System monitoring (CPU, RAM)
- Mac Link (WebSocket to Mac)

It no longer runs locally:
- ~~faster-whisper~~ (STT now on server via sidecar)
- ~~OpenAI client~~ (LLM queries now on server via OpenClaw)
- ~~espeak-ng for pipeline~~ (TTS now on server — local espeak kept only for push-to-speak fallback)

### Setup

1. **Add environment variables** to `~/.bashrc` on the Pi:

```bash
# New: CHARLI Server connection
export CHARLI_SERVER_URL="http://charli-server:3000"   # Mac Mini Tailscale address
export CHARLI_API_KEY="chk_your_desk_hub_key_here"     # From server seed output

# Keep: Wake word
export PICOVOICE_ACCESS_KEY="your_key"
export CHARLI_KEYWORD_PATH="/path/to/hey-charli.ppn"

# Remove (no longer needed):
# export CHARLI_HOST=...
# export CHARLI_TOKEN=...
```

2. **Update requirements** (lighter install):

```bash
cd ~/charli-home
source .venv/bin/activate
pip install -r requirements.txt  # faster-whisper and openai removed from deps
```

3. **Test the connection**:

```bash
python3 src/charli_server_client.py
# Should print: "✅ Server is reachable!" and a response from CHARLI
```

4. **Run as usual**:

```bash
python3 charli_home.py
# Now says "CHARLI Home v3.0 — Desk Hub (Thin Client)"
```

### Voice Pipeline Flow

```
Before: wake word → record → transcribe (local) → ask (OpenClaw) → speak (local)
After:  wake word → record → POST /api/pipeline/voice → play returned audio
```

The server returns a WAV file. The Pi just plays it through the speaker.

### JARVIS Web UI

The JARVIS UI (`web/static/`) now uses Socket.IO to connect directly to `charli_server:3000/events` for real-time state and conversation updates. The Pi serves the static HTML files using Python's built-in `http.server` (no more FastAPI dependency).

### Image Support (Future)

The Pi can send images alongside audio for vision queries. If you attach a camera:

```python
# In charli_home.py voice_pipeline(), uncomment:
# image_path = capture_image()
```

The server handles vision detection and routing automatically.

---

## iPhone (CHARLI Glasses)

### What Changed

The iOS app's `CHARLIAPIClient.swift` now points to the central server instead of the glasses-specific Python API. The glasses Python API server (`charli_glasses/api/`) has been **removed** — it's no longer needed.

### Endpoint Mapping

| Old (glasses API) | New (charli_server) |
|---|---|
| `POST /api/voice-query` | `POST /api/pipeline/voice` |
| `POST /api/voice-query-text` | `POST /api/pipeline/voice-text` |
| `POST /api/ask-vision` | `POST /api/ask/vision` |
| `POST /api/ask` | `POST /api/ask` |
| `GET /api/conversation` | `GET /api/conversation` |
| `DELETE /api/conversation` | `DELETE /api/conversation` |
| `GET /health` | `GET /health` |

### Setup

1. **In the iOS app** (or via UserDefaults), set:
   - `charli_server_url` = `http://charli-server:3000` (Mac Mini Tailscale address)
   - `charli_api_key` = `chk_your_glasses_key_here` (from server seed output)

2. The old glasses API server is gone:
   ```bash
   # charli_glasses/api/ has been removed entirely.
   # All backend logic now lives in charli_server/.
   ```

### New Capabilities

- **`sendVisionQuery()`** — Send text + image as JSON (base64). Use for vision queries when you have the image in memory.
- **`sendVoiceQuery()` with image** — Send audio + image as multipart. Full pipeline returns audio.
- **`clearConversation()`** — Clear server-side conversation history.

### Text vs Image: When to Use What

| Scenario | Method | Endpoint |
|---|---|---|
| Voice only (normal question) | `sendVoiceQuery(audioURL:)` | `/api/pipeline/voice` |
| Voice + vision (camera image) | `sendVoiceQuery(audioURL:imageData:)` | `/api/pipeline/voice` |
| Text only (typed question) | `sendTextQuery(question:)` | `/api/ask` |
| Text + image (camera snapshot) | `sendVisionQuery(question:imageData:)` | `/api/ask/vision` |
