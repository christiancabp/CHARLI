# CHARLI Server — API Reference

All `/api/*` endpoints require `X-API-Key` header.

Interactive Swagger docs available at `http://localhost:3000/docs` when the server is running.

## Pipeline (Main Device Endpoints)

These are the primary endpoints devices call. They orchestrate the full voice pipeline.

### POST `/api/pipeline/voice`
Full voice pipeline: send audio, get spoken audio response.

**Input:** multipart form
- `audio` (required) — audio file (WAV, M4A, WebM)
- `image` (optional) — image file for vision queries

**Output:** WAV audio file
- Headers: `X-Transcription`, `X-Language`, `X-Answer` (URL-encoded)
- If no speech detected: returns JSON `{ transcription: "", answer: "" }` instead

### POST `/api/pipeline/voice-text`
Same as above, but returns JSON instead of audio. Useful for debugging or when the device handles TTS locally.

**Input:** same as `/api/pipeline/voice`

**Output:**
```json
{
  "transcription": "What's the weather?",
  "language": "en",
  "answer": "It's sunny and 72 degrees today."
}
```

## Ask (Text Queries)

For when you already have text (typed input, pre-transcribed audio). Conversation history is tracked per device.

### POST `/api/ask`
Send a text question.

**Input:**
```json
{ "question": "What's the weather?", "language": "en" }
```

**Output:**
```json
{
  "question": "What's the weather?",
  "answer": "It's sunny and warm today.",
  "conversationId": "uuid"
}
```

### POST `/api/ask/vision`
Send a text question with an image. Uses a vision-optimized system prompt when the question contains vision keywords ("what am I looking at", "read this", etc.).

**Input:**
```json
{
  "question": "What am I looking at?",
  "language": "en",
  "imageBase64": "<base64-encoded-image>",
  "imageMime": "image/jpeg"
}
```

**Output:**
```json
{
  "question": "What am I looking at?",
  "answer": "You're looking at a coffee mug on a desk.",
  "vision": true
}
```

## Individual Services

These proxy directly to the Python sidecar. Useful for testing or when you want just one step of the pipeline.

### POST `/api/transcribe`
Speech-to-text only. Proxies to sidecar `POST /transcribe`.

**Input:** multipart form with `audio` file

**Output:**
```json
{ "text": "Hello world", "language": "en" }
```

### POST `/api/tts`
Text-to-speech only. Proxies to sidecar `POST /tts`.

**Input:**
```json
{ "text": "Hello world", "language": "en" }
```

**Output:** WAV audio file (binary)

## Conversation

Server tracks one active conversation per device for context-aware follow-ups.

### GET `/api/conversation`
Get the active conversation for the calling device (identified by API key).

### DELETE `/api/conversation`
Clear the active conversation. A new one is created automatically on the next question.

## Devices

### GET `/api/devices`
List all registered devices. **API keys are NOT included** in the response for security.

### POST `/api/devices`
Register a new device. Returns the full device record **including the API key** — this is the only time the key is visible, so save it.

Requires admin API key (`ADMIN_API_KEY` env var).

**Input:**
```json
{
  "name": "my-new-device",
  "type": "phone",
  "systemPrompt": "Optional custom prompt",
  "maxTokens": 150
}
```

**Valid device types:** `desk-hub`, `smart-glasses`, `phone`

### PATCH `/api/devices/:id`
Update device configuration. API key cannot be changed.

**Input:**
```json
{ "systemPrompt": "Updated prompt", "maxTokens": 200 }
```

## Health

### GET `/health` (no auth)
```json
{ "status": "ok", "uptime": 3600, "version": "0.1.0" }
```

## WebSocket

Real-time events via Socket.IO. Used by the JARVIS desk hub UI and any client that wants live updates.

Connect: `ws://server:3000/events?apiKey=<key>`

### Server → Client Events
| Event | Payload | Description |
|-------|---------|-------------|
| `snapshot` | `{ deviceId, state, conversation }` | Sent on connect — full current state |
| `device:state` | `{ deviceId, state }` | State change (idle/listening/thinking/speaking) |
| `device:message` | `{ deviceId, role, content }` | New conversation message |
| `command:speak` | `{ text, language }` | Tell device to speak text |

### Client → Server Events
| Event | Payload | Description |
|-------|---------|-------------|
| `state` | `{ state }` | Report device state |
| `heartbeat` | `{ timestamp }` | Keep-alive |
| `metrics` | `{ cpu, ram }` | System metrics (Pi) |
