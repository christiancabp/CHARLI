# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the CHARLI Glasses app.

## What This Is

iOS companion app for Meta Ray-Ban smart glasses. Pure client — records audio via Bluetooth, sends to CHARLI Server, plays response. No local processing.

## Development

Open `ios/CHARLIGlasses/` in Xcode. Build and run on a physical device (Bluetooth audio doesn't work in simulator).

Configure in UserDefaults (or hardcode for now):
- `charli_server_url` = `http://charli-server:3000`
- `charli_api_key` = `chk_your_glasses_key`

## Architecture

```
ios/CHARLIGlasses/
├── CHARLIGlassesApp.swift   → App entry point
├── ContentView.swift        → UI with animated status orb
├── CHARLIAPIClient.swift    → HTTP client → CHARLI Server (X-API-Key)
└── AudioManager.swift       → Bluetooth audio routing, recording, playback
```

**Flow:** Tap → record audio → `POST /api/pipeline/voice` → play WAV response

**State machine:** Same as all CHARLI devices: `IDLE → LISTENING → THINKING → SPEAKING → IDLE`

## Key Details

- **Swift/SwiftUI** — minimum iOS target in the Xcode project
- **Bluetooth audio** — `AudioManager` handles routing to/from Meta Ray-Ban glasses
- **Device type `smart-glasses`** — gets voice responses (1-3 sentences, no markdown, 150 max tokens)
- **No Python backend** — the old `charli_glasses/api/` directory has been removed
- **Auth:** `X-API-Key` header on all requests to the server
