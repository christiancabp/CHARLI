# CHARLI Server — Architecture

## Why a Central Server?

Before: each device (Pi desk hub, glasses) duplicated the same backend logic — transcribe, ask LLM, generate TTS. Adding a third device meant a third copy.

Now: **one central backend** that all devices connect to. Devices become thin clients.

## Two-Process Design

```
┌─────────────────────────────────────────────────────────────┐
│ Mac Mini                                                     │
│                                                             │
│  ┌──────────────────────┐    ┌──────────────────────────┐  │
│  │ NestJS (port 3000)   │    │ Python Sidecar (3001)    │  │
│  │                      │    │                          │  │
│  │ • Auth (API keys)    │───→│ • POST /transcribe       │  │
│  │ • REST endpoints     │    │   (faster-whisper)       │  │
│  │ • WebSocket gateway  │←───│                          │  │
│  │ • Database (Prisma)  │    │ • POST /tts              │  │
│  │ • Pipeline logic     │───→│   (espeak-ng / Piper)    │  │
│  │                      │    │                          │  │
│  └──────────┬───────────┘    └──────────────────────────┘  │
│             │                                               │
│             │ localhost                                      │
│             ▼                                               │
│  ┌──────────────────────┐                                   │
│  │ OpenClaw (port 18789)│                                   │
│  │ LLM Gateway          │                                   │
│  └──────────────────────┘                                   │
│                                                             │
│  ┌──────────────────────┐                                   │
│  │ SQLite (charli.db)   │                                   │
│  │ Devices, Convos, Msgs│                                   │
│  └──────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

## Why a Python Sidecar?

The ML models (faster-whisper for STT, espeak-ng/Piper for TTS) are Python-native. Instead of spawning Python per request (3s model load each time), the sidecar:

- Loads the Whisper model once at startup (~200MB)
- Keeps it hot in memory
- Responds in ~1-3s per transcription (vs ~6s with cold start)

NestJS calls the sidecar over localhost (~1-3ms HTTP overhead). Devices never talk to it.

## Voice Pipeline Flow

```
Device → POST /api/pipeline/voice (audio file)
  │
  ├→ AuthGuard: validate X-API-Key → attach device
  │
  └→ PipelineService.voiceQuery()
       │
       ├→ TranscribeService → Sidecar /transcribe → { text, lang }
       ├→ ConversationService → save user message
       ├→ AskService → OpenClaw /v1/chat/completions → answer
       ├→ ConversationService → save assistant response
       ├→ EventsGateway → broadcast to all WebSocket clients
       ├→ TtsService → Sidecar /tts → WAV buffer
       │
       └→ Return WAV audio to device
```

## Auth Model

Simple API key per device, validated via `X-API-Key` header.

- Keys are generated on device creation (format: `chk_<uuid>`)
- An `ADMIN_API_KEY` env var allows bootstrapping (creating first devices)
- No sessions, no JWT — appropriate for a private Tailscale network

## Database Schema

```
Device (id, name, type, apiKey, systemPrompt, maxTokens, lastSeen)
  └── Conversation (id, deviceId, timestamps)
       └── Message (id, conversationId, role, content, createdAt)
```

- Each device has a custom system prompt stored in the DB
- One active conversation per device for context tracking
- Messages cascade-delete when conversation is cleared

## WebSocket Design

Clients connect with their API key: `ws://server:3000/events?apiKey=<key>`

On connect, they receive a `snapshot` with their current conversation. All state changes and messages are broadcast to all connected clients, enabling cross-device awareness (e.g., the desk hub UI shows glasses activity in real time).
