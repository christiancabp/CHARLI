# CHARLI Server — Future Improvements

Ideas and upgrade paths, roughly ordered by impact and effort.

---

## Short Term (Low Effort, High Value)

### 1. Piper TTS — Natural Voice

Replace espeak-ng's robotic voice with Piper TTS for natural-sounding speech.

**What to change:**
- Download a Piper model (e.g., `en_US-lessac-medium.onnx` — ~60MB)
- Set `CHARLI_PIPER_MODEL=/path/to/model.onnx` in the sidecar's env
- The sidecar already has Piper support built in — it tries Piper first, falls back to espeak-ng

**Impact:** Massive UX improvement. Piper runs locally, ~200ms latency, zero cost.

### 2. Voice Activity Detection (VAD)

Stop recording when the user finishes talking instead of a fixed 5-second window.

**What to change:**
- Add Silero VAD or WebRTC VAD to the Pi's `src/record.py`
- Record until silence is detected (with a max timeout)
- Send shorter, cleaner audio to the server

**Impact:** Faster responses (no waiting for 5s to elapse), better transcription accuracy.

### 3. Streaming TTS

Return audio chunks as they're generated instead of waiting for the full response.

**What to change:**
- Sidecar: stream Piper TTS output as it generates
- NestJS: use chunked transfer encoding or Server-Sent Events
- Pi/iOS: start playback as chunks arrive

**Impact:** Perceived latency drops significantly — first words play within ~500ms.

### 4. Whisper Model Upgrade

The sidecar runs Whisper "base" (~200MB). On the Mac Mini, we can afford larger models.

| Model | Size | Accuracy | Speed (Mac Mini) |
|-------|------|----------|-----------------|
| base | 150MB | Good | ~1s |
| small | 500MB | Better | ~2s |
| medium | 1.5GB | Great | ~4s |

**What to change:** Set `CHARLI_WHISPER_MODEL=small` (or `medium`) in sidecar env.

---

## Medium Term (Moderate Effort)

### 5. Postgres Migration

SQLite works great for a single-server setup. Postgres adds concurrency and remote access.

**What to change (Prisma 7):**
- `prisma/schema.prisma`: change `provider = "sqlite"` to `provider = "postgresql"`
- Replace `@prisma/adapter-better-sqlite3` with `@prisma/adapter-pg` in `prisma.service.ts` and `prisma/seed.ts`
- Update `DATABASE_URL` in `.env` to a Postgres connection string
- Run `npx prisma db push` (or `npx prisma migrate dev` for production migrations)

**Impact:** Better concurrent writes, full-text search, easier backups, remote DB access.

### 6. Pi Camera Support

Add a camera module to the Pi for vision queries from the desk hub.

**What to change:**
- Add `picamera2` or `libcamera-still` to capture images on the Pi
- In `charli_home.py`, capture an image when the wake word is detected
- Pass `image_path` to `server_voice_pipeline()` — the server handles the rest

**Impact:** Desk hub can answer "what's on my desk?" style questions.

### 7. Multi-Language Auto-Detection

Currently the system prompt language is set by the `language` field. The server could auto-detect and respond in the same language.

**What to change:**
- Whisper already detects the language — it's returned in the `language` field
- Pass the detected language to the system prompt template
- The `{lang_name}` placeholder is already in all prompts

**Impact:** Seamless bilingual conversations without manual language switching.

### 8. Rate Limiting

Protect against runaway requests (e.g., a malfunctioning device in a loop).

**What to change:**
- Add `@nestjs/throttler` to NestJS
- Configure per-device rate limits (e.g., 10 requests/minute)
- Return 429 Too Many Requests when exceeded

### 9. Request Logging + Analytics

Track usage per device for insights and debugging.

**What to change:**
- Add a `RequestLog` Prisma model (deviceId, endpoint, latency, timestamp)
- NestJS interceptor to log every request
- Simple dashboard endpoint: `GET /api/analytics`

---

## Long Term (High Effort, High Value)

### 10. Streaming LLM Responses

Stream the LLM's response word-by-word to the device via WebSocket.

**What to change:**
- AskService: use streaming chat completions from OpenClaw
- EventsGateway: emit `device:token` events as tokens arrive
- Sidecar: accept streaming text for sentence-by-sentence TTS
- Pi/iOS: display words as they arrive, start TTS per sentence

**Impact:** Conversation feels live — words appear immediately instead of waiting for the full response.

### 11. Smart Home Integration

Voice control for lights, music, thermostat via the desk hub.

**What to change:**
- Add a `SmartHome` module to NestJS
- Integrate with Home Assistant API or directly with smart device APIs
- Teach CHARLI to recognize commands ("turn off the lights", "play music")
- Use function calling in the LLM to trigger smart home actions

### 12. Emotional Responses

Change CHARLI's voice tone and orb animation based on conversation context.

**What to change:**
- Add sentiment analysis to the pipeline (or ask the LLM to tag emotions)
- Pass emotion metadata in WebSocket events
- Orb: new animation profiles for happy, thinking, concerned, etc.
- TTS: adjust Piper speech rate/pitch based on emotion

### 13. Wake Word on iPhone

Currently the iOS app uses a manual trigger button. Add always-on wake word detection.

**What to change:**
- Integrate Picovoice Porcupine iOS SDK
- Run wake word detection on the Bluetooth audio stream from glasses
- Trigger recording automatically when "Hey Charli" is heard

### 14. Multi-User Support

Support multiple users, each with their own conversation context and preferences.

**What to change:**
- Add a `User` model to Prisma (linked to devices)
- Voice identification (speaker diarization) to distinguish users
- Per-user conversation history and preferences

### 15. Offline Fallback

When the server is unreachable, fall back to on-device processing.

**What to change:**
- Pi: keep `faster-whisper` and `espeak-ng` installed as fallback
- `charli_server_client.py`: on connection failure, fall back to local modules
- Smaller LLM on Pi (e.g., Phi-3 mini via llama.cpp) for basic offline Q&A

**Impact:** CHARLI still works (with reduced quality) even without network.

---

## Architecture Improvements

### 16. Message Queue (Bull/BullMQ)

For heavy workloads, decouple the pipeline steps with a job queue.

**What to change:**
- Add Redis + BullMQ
- Pipeline steps become jobs: transcribe → ask → tts
- Return a job ID immediately, client polls or gets WebSocket notification when done

**Impact:** Better reliability, automatic retries, progress tracking.

### 17. Multiple Sidecar Instances

Run multiple sidecar processes for parallel transcription.

**What to change:**
- Run 2-3 sidecar instances on different ports
- NestJS: round-robin or load-balance across sidecar instances
- Each sidecar loads its own Whisper model

**Impact:** Handle concurrent requests from multiple devices without queueing.

### 18. ~~Docker Compose~~ (DONE)

Implemented in `charli_server/docker-compose.yml`. One-command deployment for NestJS + sidecar. See [orchestration docs](orchestration.md#docker-compose).

### 19. End-to-End Tests

Automated tests that exercise the full pipeline.

**What to add:**
- `test/e2e/pipeline.e2e-spec.ts` — send a test WAV, verify response
- `test/e2e/ask.e2e-spec.ts` — text query, verify answer format
- Mock the sidecar and OpenClaw for CI
- Run with: `npm run test:e2e`

### 20. CLI Enhancements

The `charli_cli` POC is live with `ask`, `status`, and `init` commands. Next phases:

- **Phase 2 — Interactive REPL:** `charli chat` with persistent readline loop, `/clear`, `/exit`
- **Phase 3 — Voice:** `charli voice` records mic → pipeline → plays audio response
- **Phase 4 — Vision:** `charli ask --image ./photo.jpg "What is this?"`
- **Phase 5 — Streaming:** SSE integration with `POST /api/ask/stream` for real-time token display
- **Phase 6 — Rich TUI:** Migrate to React + Ink for animated UI
- **Phase 7 — npm publish:** Remove `"private": true`, publish as `@charli/cli`

### 21. Admin Dashboard

Web UI for managing devices, viewing conversations, and monitoring health.

**What to build:**
- Simple React/Next.js app (or vanilla HTML like the JARVIS UI)
- Show: device list, last seen, active conversations, system health
- Manage: register devices, edit prompts, clear conversations
- Live: WebSocket feed of all device activity
