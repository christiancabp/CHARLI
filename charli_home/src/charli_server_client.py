#!/usr/bin/env python3
"""
CHARLI Home - Server Client

HTTP client that calls the central CHARLI Server (NestJS on Mac Mini)
instead of running transcription, LLM queries, and TTS locally.

Before (local pipeline):
  record → transcribe (local Whisper) → ask (HTTP to OpenClaw) → speak (local espeak)

After (server pipeline):
  record → POST /api/pipeline/voice (sends audio, gets audio back) → play audio

The Pi becomes a thin client: capture audio, send to server, play response.
All heavy processing (Whisper, LLM, TTS) happens on the Mac Mini.

Environment Variables:
  CHARLI_SERVER_URL  — URL of the central server (default: http://charli-server:3000)
  CHARLI_API_KEY     — API key for this device (from server's device registration)
"""

import os
import requests
import tempfile

# ── Configuration ────────────────────────────────────────────────────

CHARLI_SERVER_URL = os.environ.get("CHARLI_SERVER_URL", "http://charli-server:3000")
CHARLI_API_KEY = os.environ.get("CHARLI_API_KEY", "")


def _headers():
    """Common headers for all requests to the CHARLI Server."""
    return {"X-API-Key": CHARLI_API_KEY}


# ── Full Voice Pipeline ──────────────────────────────────────────────

def voice_pipeline(audio_path: str, image_path: str = None) -> tuple:
    """
    Send audio (and optional image) to the CHARLI Server and get back:
      - A WAV audio file path (CHARLI's spoken response)
      - The transcription text
      - The answer text
      - The detected language

    This replaces the entire local pipeline: transcribe → ask → tts.

    Args:
        audio_path:  Path to the recorded WAV file
        image_path:  Optional path to an image file (for vision queries)

    Returns:
        (audio_path, transcription, answer, language)
        Returns ("", "", "", "en") on error.
    """
    url = f"{CHARLI_SERVER_URL}/api/pipeline/voice"

    try:
        # Build multipart form data
        files = {"audio": ("recording.wav", open(audio_path, "rb"), "audio/wav")}

        if image_path and os.path.exists(image_path):
            # Detect MIME type from extension
            ext = os.path.splitext(image_path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            files["image"] = ("capture" + ext, open(image_path, "rb"), mime)

        print(f"📡 Sending to CHARLI Server...")
        response = requests.post(url, headers=_headers(), files=files, timeout=30)

        # Close file handles
        for f in files.values():
            f[1].close()

        if response.status_code != 200:
            # Try to parse JSON error
            try:
                error = response.json()
                print(f"❌ Server error: {error}")
            except Exception:
                print(f"❌ Server returned {response.status_code}")
            return "", "", "", "en"

        # Check if we got audio back (Content-Type: audio/wav)
        content_type = response.headers.get("Content-Type", "")

        if "audio/wav" in content_type:
            # Save the response audio to a temp file
            fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="charli_response_")
            os.close(fd)
            with open(output_path, "wb") as f:
                f.write(response.content)

            # Extract metadata from response headers
            transcription = _decode_header(response.headers.get("X-Transcription", ""))
            language = response.headers.get("X-Language", "en")
            answer = _decode_header(response.headers.get("X-Answer", ""))

            print(f"💬 Heard: '{transcription}'")
            print(f"🤖 CHARLI: '{answer}'")
            return output_path, transcription, answer, language

        else:
            # JSON response (e.g., empty transcription)
            data = response.json()
            print(f"ℹ️ Server response: {data}")
            return "", data.get("transcription", ""), data.get("answer", ""), data.get("language", "en")

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to CHARLI Server at {CHARLI_SERVER_URL}")
        return "", "", "", "en"
    except Exception as e:
        print(f"❌ Voice pipeline error: {e}")
        return "", "", "", "en"


# ── Individual Service Calls ─────────────────────────────────────────
# These are available if the Pi needs to call services individually
# (e.g., the web server's /api/ask endpoint).

def ask_charli(question: str, language: str = "en", history: list = None) -> str:
    """
    Send a text question to CHARLI Server and return the answer.
    Replaces the local ask_charli() that called OpenClaw directly.
    """
    url = f"{CHARLI_SERVER_URL}/api/ask"

    try:
        response = requests.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json={"question": question, "language": language},
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "Sorry, I couldn't get a response.")
        else:
            print(f"❌ Ask error: {response.status_code}")
            return "Sorry, I'm having trouble connecting to the server."

    except Exception as e:
        print(f"❌ Ask error: {e}")
        return "Sorry, I can't reach the server right now."


def ask_charli_vision(
    question: str,
    language: str = "en",
    image_base64: str = None,
    image_mime: str = "image/jpeg",
) -> str:
    """
    Send a text + image question to CHARLI Server.
    For when the Pi has a camera and wants to do vision queries.
    """
    url = f"{CHARLI_SERVER_URL}/api/ask/vision"

    try:
        body = {
            "question": question,
            "language": language,
            "imageBase64": image_base64,
            "imageMime": image_mime,
        }
        response = requests.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json=body,
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("answer", "Sorry, I couldn't process the image.")
        else:
            print(f"❌ Vision error: {response.status_code}")
            return "Sorry, I'm having trouble with vision queries."

    except Exception as e:
        print(f"❌ Vision error: {e}")
        return "Sorry, I can't reach the server right now."


def speak_text(text: str, language: str = "en") -> str:
    """
    Get TTS audio from CHARLI Server. Returns path to WAV file.
    Useful when the Pi receives a text command and needs to speak it.
    """
    url = f"{CHARLI_SERVER_URL}/api/tts"

    try:
        response = requests.post(
            url,
            headers={**_headers(), "Content-Type": "application/json"},
            json={"text": text, "language": language},
            timeout=10,
        )

        if response.status_code == 200 and "audio/wav" in response.headers.get("Content-Type", ""):
            fd, output_path = tempfile.mkstemp(suffix=".wav", prefix="charli_tts_")
            os.close(fd)
            with open(output_path, "wb") as f:
                f.write(response.content)
            return output_path
        else:
            print(f"❌ TTS error: {response.status_code}")
            return ""

    except Exception as e:
        print(f"❌ TTS error: {e}")
        return ""


def check_health() -> bool:
    """Check if the CHARLI Server is reachable."""
    try:
        response = requests.get(f"{CHARLI_SERVER_URL}/health", timeout=3)
        return response.status_code == 200
    except Exception:
        return False


# ── Helpers ──────────────────────────────────────────────────────────

def _decode_header(value: str) -> str:
    """URL-decode a header value (server encodes transcription/answer)."""
    if not value:
        return ""
    try:
        from urllib.parse import unquote
        return unquote(value)
    except Exception:
        return value


# ── Standalone Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"CHARLI Server: {CHARLI_SERVER_URL}")
    print(f"API Key: {CHARLI_API_KEY[:8]}..." if CHARLI_API_KEY else "API Key: NOT SET")

    if check_health():
        print("✅ Server is reachable!")
        answer = ask_charli("Hello CHARLI! How are you?")
        print(f"🤖 {answer}")
    else:
        print("❌ Server is not reachable.")
