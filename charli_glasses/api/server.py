#!/usr/bin/env python3
"""
CHARLI Glasses - API Server

FastAPI server that powers the CHARLI Glasses experience. This is the bridge
between the iOS companion app (which talks to the Meta Ray-Ban glasses) and
CHARLI's brain (OpenClaw on Mac Mini).

The iOS app sends audio (and optionally images) here, and gets back audio
(TTS response) or text. This server can run on:
  - The Raspberry Pi (alongside the desk hub)
  - The Mac Mini (closer to the brain, less network hops)
  - Any machine on the Tailscale network

Endpoints:
  POST /api/voice-query     — Full pipeline: audio in → audio out
  POST /api/voice-query-text — Full pipeline: audio in → text out
  POST /api/ask-vision      — Text + optional image → text response
  GET  /health              — Health check

The full voice pipeline:
  1. Receive audio from iOS app (recorded from glasses mic)
  2. Transcribe with Whisper (speech-to-text)
  3. Send text (+ optional image) to OpenClaw (the brain)
  4. Convert response to audio with TTS
  5. Return audio to iOS app (plays through glasses speakers)

Usage:
  python3 server.py                          # Run on default port 8090
  CHARLI_GLASSES_PORT=9000 python3 server.py  # Custom port
"""

import os
import time
import base64
import tempfile
import asyncio

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

# Import our building blocks
from src.transcribe import transcribe
from src.ask_charli_vision import ask_charli
from src.tts import text_to_speech_file

# ── Create the App ───────────────────────────────────────────────────
app = FastAPI(
    title="CHARLI Glasses API",
    description="Voice + Vision API for CHARLI's smart glasses interface",
    version="0.1.0",
)

_start_time = time.time()

# In-memory conversation history for the glasses session.
# Separate from the desk hub's conversation — glasses are a different "room".
conversation_history = []

# Max conversation turns to keep in memory
MAX_HISTORY = 20


# ── Request Models ───────────────────────────────────────────────────

class AskVisionRequest(BaseModel):
    """Request body for /api/ask-vision (text + optional image)."""
    question: str
    language: str = "en"
    image_base64: Optional[str] = None  # Base64-encoded image from glasses camera
    image_mime: str = "image/jpeg"


class AskTextRequest(BaseModel):
    """Request body for simple text questions (no audio, no image)."""
    question: str
    language: str = "en"


# =====================================================================
# ENDPOINTS
# =====================================================================

@app.get("/health")
async def health():
    """Health check — is the glasses API server alive?"""
    return {
        "status": "ok",
        "service": "charli-glasses",
        "uptime_seconds": round(time.time() - _start_time),
    }


@app.post("/api/voice-query")
async def voice_query(
    audio: UploadFile = File(..., description="Audio file from glasses mic (WAV or M4A)"),
    image: Optional[UploadFile] = File(None, description="Optional POV image from glasses camera"),
):
    """
    Full voice pipeline: audio in → audio out.

    This is THE main endpoint for the glasses experience.
    The iOS app sends a recorded audio clip (from the glasses mic),
    and gets back a WAV audio file (CHARLI's spoken response).

    Optionally accepts an image for vision queries ("what am I looking at?").

    Pipeline:
      1. Save uploaded audio to temp file
      2. Transcribe with Whisper → text
      3. If image provided, encode to base64
      4. Send text (+image) to OpenClaw → answer text
      5. Convert answer to speech → WAV file
      6. Return WAV file to iOS app
    """
    loop = asyncio.get_event_loop()

    # ── Step 1: Save audio to temp file ──────────────────────────
    audio_data = await audio.read()
    suffix = ".m4a" if audio.content_type == "audio/m4a" else ".wav"
    fd, audio_path = tempfile.mkstemp(suffix=suffix, prefix="glasses_in_")
    os.close(fd)

    with open(audio_path, "wb") as f:
        f.write(audio_data)

    try:
        # ── Step 2: Transcribe ───────────────────────────────────
        text, language = await loop.run_in_executor(None, transcribe, audio_path)

        if not text:
            # Clean up and return error
            os.unlink(audio_path)
            raise HTTPException(status_code=400, detail="Could not understand audio. Please try again.")

        # ── Step 3: Process image (if provided) ──────────────────
        image_b64 = None
        image_mime = "image/jpeg"
        if image:
            image_data = await image.read()
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            # Detect MIME from filename
            if image.filename and image.filename.lower().endswith(".png"):
                image_mime = "image/png"

        # ── Step 4: Ask CHARLI ───────────────────────────────────
        answer = await loop.run_in_executor(
            None, ask_charli, text, language, conversation_history,
            image_b64, image_mime
        )

        # Save to conversation history
        conversation_history.append({"role": "user", "text": text})
        conversation_history.append({"role": "charli", "text": answer})
        # Trim history if it gets too long
        while len(conversation_history) > MAX_HISTORY * 2:
            conversation_history.pop(0)

        # ── Step 5: Text-to-Speech ───────────────────────────────
        tts_path = await loop.run_in_executor(None, text_to_speech_file, answer, language)

        if not tts_path:
            os.unlink(audio_path)
            raise HTTPException(status_code=500, detail="TTS failed to generate audio.")

        # ── Step 6: Return audio ─────────────────────────────────
        os.unlink(audio_path)  # Clean up input audio

        # Return the TTS audio file. The iOS app plays this through
        # the glasses speakers via Bluetooth.
        return FileResponse(
            path=tts_path,
            media_type="audio/wav",
            filename="charli_response.wav",
            # Clean up temp file after sending
            background=_cleanup_file(tts_path),
        )

    except HTTPException:
        raise
    except Exception as e:
        # Clean up on error
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        print(f"❌ Voice query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-query-text")
async def voice_query_text(
    audio: UploadFile = File(..., description="Audio file from glasses mic"),
    image: Optional[UploadFile] = File(None, description="Optional POV image from glasses camera"),
):
    """
    Full voice pipeline but returns TEXT instead of audio.

    Same as /api/voice-query but returns JSON with the transcription
    and answer text. Useful for debugging or when the iOS app wants
    to handle TTS on-device.
    """
    loop = asyncio.get_event_loop()

    # Save audio
    audio_data = await audio.read()
    suffix = ".m4a" if audio.content_type == "audio/m4a" else ".wav"
    fd, audio_path = tempfile.mkstemp(suffix=suffix, prefix="glasses_in_")
    os.close(fd)

    with open(audio_path, "wb") as f:
        f.write(audio_data)

    try:
        # Transcribe
        text, language = await loop.run_in_executor(None, transcribe, audio_path)

        if not text:
            os.unlink(audio_path)
            raise HTTPException(status_code=400, detail="Could not understand audio.")

        # Process image
        image_b64 = None
        image_mime = "image/jpeg"
        if image:
            image_data = await image.read()
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            if image.filename and image.filename.lower().endswith(".png"):
                image_mime = "image/png"

        # Ask CHARLI
        answer = await loop.run_in_executor(
            None, ask_charli, text, language, conversation_history,
            image_b64, image_mime
        )

        # Save to history
        conversation_history.append({"role": "user", "text": text})
        conversation_history.append({"role": "charli", "text": answer})
        while len(conversation_history) > MAX_HISTORY * 2:
            conversation_history.pop(0)

        os.unlink(audio_path)

        return {
            "status": "ok",
            "transcription": text,
            "language": language,
            "answer": answer,
        }

    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(audio_path):
            os.unlink(audio_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask-vision")
async def ask_vision(req: AskVisionRequest):
    """
    Text + optional image → text response.

    For when the iOS app handles transcription on-device and just needs
    to send the question (and optionally an image) to CHARLI.

    This is also useful for testing vision queries without audio:
      curl -X POST http://localhost:8090/api/ask-vision \
           -H 'Content-Type: application/json' \
           -d '{"question": "What is the capital of France?"}'
    """
    loop = asyncio.get_event_loop()

    answer = await loop.run_in_executor(
        None, ask_charli, req.question, req.language, conversation_history,
        req.image_base64, req.image_mime
    )

    conversation_history.append({"role": "user", "text": req.question})
    conversation_history.append({"role": "charli", "text": answer})
    while len(conversation_history) > MAX_HISTORY * 2:
        conversation_history.pop(0)

    return {
        "status": "ok",
        "question": req.question,
        "answer": answer,
        "vision": req.image_base64 is not None,
    }


@app.post("/api/ask")
async def ask_text(req: AskTextRequest):
    """
    Simple text question → text response.

    Same as the desk hub's /api/ask endpoint. For simple text queries
    without vision or audio.
    """
    loop = asyncio.get_event_loop()

    answer = await loop.run_in_executor(
        None, ask_charli, req.question, req.language, conversation_history
    )

    conversation_history.append({"role": "user", "text": req.question})
    conversation_history.append({"role": "charli", "text": answer})
    while len(conversation_history) > MAX_HISTORY * 2:
        conversation_history.pop(0)

    return {
        "status": "ok",
        "question": req.question,
        "answer": answer,
    }


@app.get("/api/conversation")
async def get_conversation():
    """Return the current glasses conversation history."""
    return {
        "conversation": conversation_history,
        "length": len(conversation_history),
    }


@app.delete("/api/conversation")
async def clear_conversation():
    """Clear the glasses conversation history."""
    conversation_history.clear()
    return {"status": "ok", "message": "Conversation cleared."}


# ── Helpers ──────────────────────────────────────────────────────────

class _cleanup_file:
    """Background task to delete a temp file after the response is sent."""
    def __init__(self, path: str):
        self.path = path

    async def __call__(self):
        try:
            if os.path.exists(self.path):
                os.unlink(self.path)
        except OSError:
            pass


# ── Run the Server ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("CHARLI_GLASSES_PORT", "8090"))
    print(f"\n🕶️ CHARLI Glasses API starting on port {port}...")
    print(f"   Health check: http://localhost:{port}/health")
    print(f"   Voice query:  POST http://localhost:{port}/api/voice-query")
    print(f"   Vision query: POST http://localhost:{port}/api/ask-vision")
    print(f"   API docs:     http://localhost:{port}/docs\n")

    uvicorn.run(app, host="0.0.0.0", port=port)
