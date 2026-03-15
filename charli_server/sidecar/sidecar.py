#!/usr/bin/env python3
"""
CHARLI Server — Python ML Sidecar

A minimal FastAPI server with exactly 2 endpoints:
  POST /transcribe — Speech-to-text via faster-whisper
  POST /tts        — Text-to-speech via espeak-ng (or Piper TTS)

This runs alongside the NestJS server on the Mac Mini.
The Whisper model loads once at startup and stays in memory (~200MB),
so every request is fast (~1-3s for transcription, ~200ms for TTS).

NestJS calls this over localhost — devices never talk to it directly.
"""

import os
import subprocess
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from faster_whisper import WhisperModel

# ── Configuration ────────────────────────────────────────────────────

MODEL_SIZE = os.environ.get("CHARLI_WHISPER_MODEL", "base")
PIPER_MODEL_PATH = os.environ.get("CHARLI_PIPER_MODEL", "")
SIDECAR_PORT = int(os.environ.get("CHARLI_SIDECAR_PORT", "3001"))

ESPEAK_VOICES = {"en": "en", "es": "es"}

# ── Model Loading ────────────────────────────────────────────────────
# Load the Whisper model once at startup — it stays in memory.
# This is why we use a sidecar instead of spawning Python per request.

whisper_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global whisper_model
    print(f"Loading faster-whisper model ({MODEL_SIZE}, INT8)...")
    whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("  faster-whisper is ready!")
    yield
    print("Sidecar shutting down.")


app = FastAPI(title="CHARLI Sidecar", lifespan=lifespan)


# ── POST /transcribe ─────────────────────────────────────────────────

@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    Transcribe an audio file to text using faster-whisper.

    Accepts: WAV, M4A, WebM audio files (multipart upload)
    Returns: { "text": "...", "language": "en" }
    """
    # Save uploaded audio to a temp file (faster-whisper needs a file path)
    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    try:
        content = await audio.read()
        os.write(fd, content)
        os.close(fd)

        segments, info = whisper_model.transcribe(temp_path, beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        language = info.language or "en"

        print(f"  Transcribed: '{text}' ({language})")
        return {"text": text, "language": language}

    except Exception as e:
        print(f"  Transcription error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "text": "", "language": "en"},
        )
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


# ── POST /tts ────────────────────────────────────────────────────────

@app.post("/tts")
async def tts(body: dict):
    """
    Convert text to speech, returning a WAV audio file.

    Accepts: { "text": "Hello", "language": "en" }
    Returns: WAV audio file
    """
    text = body.get("text", "")
    language = body.get("language", "en")

    if not text:
        return JSONResponse(status_code=400, content={"error": "No text provided"})

    # Try Piper first, fall back to espeak-ng
    if PIPER_MODEL_PATH and os.path.exists(PIPER_MODEL_PATH):
        output_path = _tts_piper(text, language)
    else:
        output_path = _tts_espeak(text, language)

    if not output_path:
        return JSONResponse(status_code=500, content={"error": "TTS failed"})

    return FileResponse(
        output_path,
        media_type="audio/wav",
        filename="response.wav",
        background=None,  # Don't delete before sending
    )


def _tts_espeak(text: str, language: str) -> str:
    """Generate speech using espeak-ng (writes to a WAV file)."""
    voice = ESPEAK_VOICES.get(language, "en")
    fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="charli_tts_")
    os.close(fd)

    try:
        subprocess.run(
            ["espeak-ng", "-v", voice, "-w", output_path, text],
            check=True,
            capture_output=True,
        )
        print(f"  TTS (espeak-ng): {len(text)} chars → {output_path}")
        return output_path
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"  espeak-ng error: {e}")
        if os.path.exists(output_path):
            os.unlink(output_path)
        return ""


def _tts_piper(text: str, language: str) -> str:
    """Generate speech using Piper TTS (higher quality, runs locally)."""
    fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="charli_tts_")
    os.close(fd)

    try:
        subprocess.run(
            ["piper", "--model", PIPER_MODEL_PATH, "--output_file", output_path],
            input=text.encode("utf-8"),
            check=True,
            capture_output=True,
        )
        print(f"  TTS (piper): {len(text)} chars → {output_path}")
        return output_path
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"  Piper failed ({e}), falling back to espeak-ng")
        if os.path.exists(output_path):
            os.unlink(output_path)
        return _tts_espeak(text, language)


# ── GET /health ──────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_SIZE,
        "piper": bool(PIPER_MODEL_PATH),
    }


# ── Run ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print(f"\n CHARLI Sidecar starting on port {SIDECAR_PORT}")
    print(f"   Whisper model: {MODEL_SIZE}")
    print(f"   Piper TTS:     {'yes' if PIPER_MODEL_PATH else 'no (using espeak-ng)'}\n")
    uvicorn.run(app, host="0.0.0.0", port=SIDECAR_PORT)
