# CHARLI Server — API Reference

All `/api/*` endpoints require `X-API-Key` header.

## Pipeline (Main Device Endpoints)

### POST `/api/pipeline/voice`
Full voice pipeline: send audio, get spoken audio response.

**Input:** multipart form
- `audio` (required) — audio file (WAV, M4A, WebM)
- `image` (optional) — image file for vision queries

**Output:** WAV audio file
- Headers: `X-Transcription`, `X-Language`, `X-Answer` (URL-encoded)

### POST `/api/pipeline/voice-text`
Same as above, but returns JSON instead of audio.

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
Send a text question with an image.

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

### POST `/api/transcribe`
Speech-to-text only.

**Input:** multipart form with `audio` file

**Output:**
```json
{ "text": "Hello world", "language": "en" }
```

### POST `/api/tts`
Text-to-speech only.

**Input:**
```json
{ "text": "Hello world", "language": "en" }
```

**Output:** WAV audio file

## Conversation

### GET `/api/conversation`
Get the active conversation for the calling device.

### DELETE `/api/conversation`
Clear the active conversation.

## Devices

### GET `/api/devices`
List all registered devices.

### POST `/api/devices`
Register a new device. Returns API key.

**Input:**
```json
{
  "name": "my-new-device",
  "type": "phone",
  "systemPrompt": "Optional custom prompt",
  "maxTokens": 150
}
```

### PATCH `/api/devices/:id`
Update device configuration.

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

Connect: `ws://server:3000/events?apiKey=<key>`

### Server → Client Events
| Event | Payload | Description |
|-------|---------|-------------|
| `snapshot` | `{ deviceId, state, conversation }` | Sent on connect |
| `device:state` | `{ deviceId, state }` | State change |
| `device:message` | `{ deviceId, role, content }` | New message |
| `command:speak` | `{ text, language }` | Speak command |

### Client → Server Events
| Event | Payload | Description |
|-------|---------|-------------|
| `state` | `{ state }` | Report device state |
| `heartbeat` | `{ timestamp }` | Keep-alive |
| `metrics` | `{ cpu, ram }` | System metrics |
