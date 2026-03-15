# CHARLI Glasses

**Meta Ray-Ban Smart Glasses integration for CHARLI** — extending CHARLI's reach from the desk into the real world.

> *"Hey Charli, what am I looking at?"*
> *"That's the Rockefeller Center, sir. Want directions or more info?"*

## What Is This?

CHARLI Glasses turns Meta Ray-Ban Display smart glasses into a wearable CHARLI interface. The glasses become CHARLI's eyes, ears, and mouth — connected to CHARLI's brain via an iPhone companion app and the central CHARLI Server.

Think Tony Stark talking to FRIDAY through his glasses.

## Architecture (Thin Client)

```
Meta Ray-Ban Glasses
    │
    ├── Bluetooth Audio ──→ iPhone Mic Input (voice)
    ├── SDK Camera API ───→ iPhone App (image capture)
    └── Bluetooth Audio ←── iPhone Speaker Output (response)
                              │
                    iPhone Companion App
                    (Swift/SwiftUI)
                              │
                    WiFi / Tailscale
                              │
                    CHARLI Server (NestJS on Mac Mini)
                    ├── Auth (X-API-Key)
                    ├── Pipeline (transcribe → ask → TTS)
                    ├── Conversation history
                    └── WebSocket gateway
```

The iPhone app is a **thin client** — it captures audio/images from the glasses and sends them to the central CHARLI Server. All processing (speech-to-text, LLM queries, text-to-speech) happens on the server.

> **Note:** The old `charli_glasses/api/` Python backend has been removed. All backend logic now lives in `charli_server/`. See `docs/charli_server/device-migration.md` for details.

## Project Structure

```
charli_glasses/
├── README.md                       ← You are here
└── ios/                            ← iOS companion app (thin client)
    └── CHARLIGlasses/
        ├── CHARLIGlassesApp.swift  ← App entry point
        ├── ContentView.swift       ← Main UI (orb, status, transcript)
        ├── AudioManager.swift      ← Bluetooth audio routing + recording
        └── CHARLIAPIClient.swift   ← HTTP client for CHARLI Server
```

**Removed:**
- ~~`api/`~~ — The dedicated Python backend (server.py, transcribe.py, ask_charli_vision.py, tts.py) has been deleted. All endpoints are now served by `charli_server/`.

## iOS App — CHARLIAPIClient

The iOS app talks to the central CHARLI Server using `CHARLIAPIClient.swift`:

| Method | Server Endpoint | Description |
|--------|----------------|-------------|
| `sendVoiceQuery(audioURL:)` | `POST /api/pipeline/voice` | Audio in → audio out (full pipeline) |
| `sendVoiceQuery(audioURL:imageData:)` | `POST /api/pipeline/voice` | Audio + image → audio out (vision) |
| `sendTextQuery(question:)` | `POST /api/ask` | Text in → text out |
| `sendVisionQuery(question:imageData:)` | `POST /api/ask/vision` | Text + image → text out |
| `clearConversation()` | `DELETE /api/conversation` | Clear server-side history |
| `checkHealth()` | `GET /health` | Server health check |

All requests include `X-API-Key` header for authentication.

### Configuration

Set in the app (UserDefaults or hardcode):
- `charli_server_url` = `http://charli-server:3000` (Mac Mini Tailscale address)
- `charli_api_key` = `chk_your_glasses_key_here` (from server seed output)

### When to Use What

| Scenario | Method | Endpoint |
|---|---|---|
| Voice only (normal question) | `sendVoiceQuery(audioURL:)` | `/api/pipeline/voice` |
| Voice + vision (camera image) | `sendVoiceQuery(audioURL:imageData:)` | `/api/pipeline/voice` |
| Text only (typed question) | `sendTextQuery(question:)` | `/api/ask` |
| Text + image (camera snapshot) | `sendVisionQuery(question:imageData:)` | `/api/ask/vision` |

## Quick Start

### Prerequisites

1. **CHARLI Server** running on Mac Mini:
   - NestJS at `http://charli-server:3000`
   - Python sidecar at `http://charli-server:3001`
   - Glasses device registered: `npx ts-node prisma/seed.ts` (save the `charli-glasses` API key)

2. **Xcode** installed on your Mac

3. **iPhone** on the same Tailscale network as the Mac Mini

### Setup

1. Open `charli_glasses/ios/CHARLIGlasses.xcodeproj` in Xcode
2. Set the server URL and API key in `CHARLIAPIClient.swift`
3. Build and run on your iPhone
4. Pair Meta Ray-Ban glasses via Bluetooth
5. Test: tap the record button → speak → hear CHARLI's response through the glasses

## Roadmap

### Phase 1 — Bluetooth Audio Bridge (current)
- [x] iOS companion app scaffold
- [x] HTTP client pointing to central CHARLI Server
- [x] Vision-capable queries (text + image)
- [ ] Purchase Meta Ray-Ban Display glasses
- [ ] Pair glasses and verify Bluetooth audio routing
- [ ] Integrate Porcupine wake word on iOS

### Phase 2 — Camera Vision
- [ ] Register for Meta Wearables Device Access Toolkit
- [ ] Integrate camera capture in iOS app
- [ ] "What am I looking at?" with real POV photos

### Phase 3 — HUD Display
- [ ] When Meta's display APIs become available
- [ ] Show CHARLI responses as text overlay in glasses
- [ ] Contextual information overlays

## Hardware

| Item | Status |
|------|--------|
| Meta Ray-Ban Display (Shiny Sand + Neural Band) | Need to purchase ($799) |
| iPhone | Already have |
| Mac Mini (CHARLI Server + OpenClaw brain) | Already have |
| Tailscale network | Already configured |
| Picovoice access key | Already have |

## Related Docs

- `docs/charli_server/` — Server setup, API reference, architecture
- `docs/charli_server/device-migration.md` — Migration details from old glasses API
- `docs/charli_glasses/PROPOSAL.md` — Original proposal and architecture deep-dive
