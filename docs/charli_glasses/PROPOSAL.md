# CHARLI Glasses — Meta Ray-Ban Smart Glasses Integration

## Vision

Extend CHARLI from a desk-bound assistant into a wearable companion. The Meta Ray-Ban Display smart glasses become CHARLI's eyes, ears, and mouth in the real world — connected to CHARLI's brain (OpenClaw on Mac Mini) through an iPhone relay.

**The Tony Stark experience:** Tony's glasses were eyes + ears + mouth connected to FRIDAY's brain. That's exactly what this is — Meta Ray-Ban Display glasses connected to CHARLI's brain, with the iPhone as the relay station.

## What's Possible Today

### Meta Wearables Device Access Toolkit (Public Preview since Dec 2025)

| Capability | Status | Access Method |
|-----------|--------|---------------|
| Camera (12MP, 720p/30fps) | Available | Native SDK (iOS/Android) |
| Microphone (5-mic array) | Available | Bluetooth audio profile + SDK |
| Speakers (open-ear) | Available | Bluetooth audio profile |
| Display (HUD on new model) | Coming soon | Not yet in SDK |
| Custom AI assistant | Not yet in SDK | Workaround via Bluetooth |

**Key insight:** The glasses' mic and speakers are accessible via standard Bluetooth audio profiles. A companion phone app can bridge them to CHARLI without needing Meta's AI pipeline.

## Architecture

> **Updated:** The dedicated glasses API server has been replaced by the central CHARLI Server. Both the desk hub and glasses now connect to the same NestJS backend.

```
Meta Ray-Ban Glasses ──── Bluetooth ────→ iPhone Companion App
   (eyes + ears + mouth)                  (thin client)
                                              │
                                     WiFi / Tailscale
                                              │
                                    CHARLI Server (NestJS :3000)
                                    ├── Auth, Pipeline, Conversation
                                    ├── Python Sidecar (STT + TTS)
                                    └── OpenClaw (LLM brain)
```

This fits perfectly into CHARLI's "distributed nervous system" pattern:
- The **desk hub** (Pi) = ears + mouth + display at the desk
- The **glasses** (iPhone) = eyes + ears + mouth on the go
- The **CHARLI Server** (Mac Mini) = brain + memory (always)

## Three Approaches

### Approach 1: Bluetooth Audio Bridge (No SDK needed) ← START HERE
- Pair glasses to iPhone as Bluetooth headset
- iOS app records from Bluetooth mic, sends to CHARLI API
- CHARLI API returns audio, iOS app plays through Bluetooth speakers
- **Works today.** No Meta SDK needed.

### Approach 2: Full Vision Experience (Meta SDK)
- Build iOS app using Meta's Wearables Device Access Toolkit
- Access camera for "what am I looking at?" queries
- Send POV photos to vision-capable model via CHARLI API

### Approach 3: HUD Display (Future)
- When Meta opens display APIs
- CHARLI responses as text overlay in glasses
- Full hands-free, eyes-up experience

## Voice Pipeline (Glasses)

```
Glasses mic → Bluetooth → iPhone app → HTTP POST audio
                                              │
                                              ↓
                                    CHARLI Glasses API
                                    ┌──────────────────┐
                                    │ 1. Transcribe     │ (Whisper)
                                    │ 2. Ask CHARLI     │ (OpenClaw)
                                    │ 3. Text-to-Speech │ (espeak/Piper)
                                    └──────────────────┘
                                              │
                                              ↓
                                    HTTP response (WAV audio)
                                              │
                                              ↓
iPhone app → Bluetooth → Glasses speakers → User hears response
```

## Implementation Phases

### Phase 1 — Backend + iOS Scaffold (DONE)
- CHARLI Glasses API server with `/api/voice-query` endpoint
- Vision-capable `ask_charli` with image support
- iOS companion app scaffold with Bluetooth audio routing

### Phase 2 — Hardware + Wake Word
- Purchase Meta Ray-Ban Display glasses ($799)
- Pair and verify Bluetooth audio routing works
- Integrate Porcupine wake word detection on iOS
- End-to-end test: "Hey Charli" → response through glasses

### Phase 3 — Vision
- Register for Meta Wearables Device Access Toolkit
- Add camera capture to iOS app
- Detect vision keywords ("what am I looking at?")
- Capture POV photo + send to vision model via API

### Phase 4 — Polish
- Upgrade TTS to Piper for natural voice
- Add conversation context awareness
- Optimize latency (target: < 3 seconds end-to-end)

### Phase 5 — HUD Display (when available)
- Text overlays in glasses display
- Contextual information cards
- Directions and translations

## Hardware Checklist

| Item | Status | Cost |
|------|--------|------|
| Meta Ray-Ban Display (Shiny Sand + Neural Band) | Need to purchase | $799 |
| iPhone | Already have | — |
| Mac Mini (OpenClaw brain) | Already have | — |
| Tailscale network | Already configured | — |
| Picovoice access key | Already have | — |

## Sources

- [Meta Wearables Device Access Toolkit](https://developers.meta.com/blog/introducing-meta-wearables-device-access-toolkit/)
- [Meta Wearables Developer FAQ](https://developers.meta.com/wearables/faq/)
- [Meta Ray-Ban Developer Features Guide](https://www.lushbinary.com/blog/meta-rayban-glasses-developer-features-gen-1-gen-2/)
- [Porcupine Wake Word — iOS SDK](https://picovoice.ai/docs/porcupine/)
