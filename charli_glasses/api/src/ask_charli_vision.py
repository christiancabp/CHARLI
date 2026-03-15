#!/usr/bin/env python3
"""
CHARLI Glasses - Vision-capable Ask CHARLI.

An extended version of the desk hub's ask_charli.py that supports sending
images alongside text questions. This powers the "what am I looking at?"
experience when using CHARLI through the Meta Ray-Ban glasses.

How it works:
  1. Takes a text question + optional image (base64-encoded)
  2. Builds an OpenAI-compatible message with text + image content
  3. Sends to OpenClaw on Mac Mini (which routes to a vision-capable model)
  4. Returns CHARLI's response as text

The OpenAI vision API format uses a "content" array instead of a plain string:
  {"role": "user", "content": [
      {"type": "text", "text": "What am I looking at?"},
      {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
  ]}

This is the same format used by GPT-4V, Claude, and other vision models.
OpenClaw routes to the appropriate vision-capable model automatically.
"""

import os
import base64
from openai import OpenAI

# ── Connect to the Brain (Mac Mini) ──────────────────────────────────
charli_host = os.environ.get("CHARLI_HOST", "http://100.91.206.1:18789")
charli_token = os.environ.get("CHARLI_TOKEN", "")

client = OpenAI(
    base_url=f"{charli_host}/v1",
    api_key=charli_token
)

# ── System Prompts ───────────────────────────────────────────────────
# Two prompts: one for text-only questions, one for vision queries.
# Vision queries get a longer max_tokens since describing images needs more words.

GLASSES_SYSTEM_PROMPT = """You are CHARLI, responding through smart glasses worn by your user.
Keep answers SHORT: 1 to 3 sentences maximum.
No bullet points, no numbered lists, no markdown symbols like * or #.
Speak naturally, like a personal assistant talking in someone's ear.
Be concise — the user is on the move and needs quick, clear answers.
Respond in {lang_name}."""

VISION_SYSTEM_PROMPT = """You are CHARLI, responding through smart glasses with a camera.
The user is asking about something they can see through their glasses camera.
Describe what you see clearly and concisely — 1 to 3 sentences.
No bullet points, no numbered lists, no markdown symbols.
Speak naturally, like a personal assistant identifying things for someone.
If you recognize landmarks, buildings, signs, text, or people, mention them.
Respond in {lang_name}."""

# How many past turns to include for context
MAX_CONTEXT_TURNS = 3

# ── Vision Query Detection ───────────────────────────────────────────
# Keywords that suggest the user wants CHARLI to look at something.
# If the question contains any of these AND an image is provided,
# we use the vision system prompt instead of the regular one.
VISION_KEYWORDS = [
    "looking at", "see", "read this", "read that", "what is this",
    "what is that", "what's this", "what's that", "who is",
    "translate", "identify", "describe", "show me", "tell me about this",
    "what does this say", "what do you see", "can you see",
]


def is_vision_query(question: str) -> bool:
    """Check if the question is asking about something visual."""
    q = question.lower()
    return any(keyword in q for keyword in VISION_KEYWORDS)


def ask_charli(
    question: str,
    language: str = "en",
    history: list = None,
    image_base64: str = None,
    image_mime: str = "image/jpeg",
) -> str:
    """
    Send a question (with optional image) to CHARLI and return the response.

    Args:
        question:     The user's question text
        language:     Language code ("en", "es", etc.)
        history:      Optional conversation history for follow-ups
        image_base64: Optional base64-encoded image from the glasses camera.
                      When provided, CHARLI can "see" what the user sees.
        image_mime:   MIME type of the image (default: "image/jpeg")

    Returns:
        CHARLI's text response.

    Examples:
        # Text-only (same as desk hub)
        ask_charli("What's the weather?")

        # Vision query — "what am I looking at?"
        ask_charli("What am I looking at?", image_base64="<base64 jpeg>")
    """
    lang_name = "English" if language == "en" else "Spanish" if language == "es" else "English"

    # Pick the right system prompt based on whether this is a vision query
    has_image = image_base64 is not None
    use_vision = has_image and is_vision_query(question)

    if use_vision:
        prompt_template = VISION_SYSTEM_PROMPT
        max_tokens = 250  # Vision descriptions need more room
        print(f"👁️ [{lang_name}] Vision query — asking CHARLI to look...")
    else:
        prompt_template = GLASSES_SYSTEM_PROMPT
        max_tokens = 150
        print(f"🤔 [{lang_name}] Asking CHARLI...")

    prompt = prompt_template.replace("{lang_name}", lang_name)

    # ── Build Messages ───────────────────────────────────────────
    messages = [{"role": "system", "content": prompt}]

    # Add conversation history (same pattern as desk hub)
    if history:
        recent = history[-(MAX_CONTEXT_TURNS * 2):]
        for entry in recent:
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["text"]})

    # ── Build the User Message ───────────────────────────────────
    # If we have an image, use the multi-part content format.
    # Otherwise, use a plain text string (compatible with all models).
    if has_image:
        # Multi-part content: text + image
        # The image is sent as a data URL: "data:image/jpeg;base64,<data>"
        user_content = [
            {"type": "text", "text": question},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_mime};base64,{image_base64}"
                }
            }
        ]
        messages.append({"role": "user", "content": user_content})
    else:
        # Plain text (same as desk hub)
        messages.append({"role": "user", "content": question})

    # ── Send to OpenClaw ─────────────────────────────────────────
    try:
        response = client.chat.completions.create(
            model="openclaw:main",
            messages=messages,
            max_tokens=max_tokens,
            user="glasses"  # Identifies requests from the glasses
        )

        answer = response.choices[0].message.content
        print(f"🤖 CHARLI says: '{answer}'")
        return answer

    except Exception as e:
        print(f"❌ Error asking CHARLI: {e}")
        return "I'm sorry, I'm having trouble connecting to my brain right now."


def encode_image_file(image_path: str) -> tuple:
    """
    Helper: Read an image file and return (base64_string, mime_type).

    Useful for testing — the iOS app will send base64 directly.
    """
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    return image_data, mime_type


# ── Standalone Test ──────────────────────────────────────────────────
if __name__ == "__main__":
    # Test 1: Text-only (same as desk hub)
    ask_charli("Hello Charli! How are you?")

    # Test 2: Vision query without image (falls back to text)
    ask_charli("What am I looking at?")

    # Test 3: Vision query with image (if a test image exists)
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        img_b64, mime = encode_image_file(test_image)
        ask_charli("What am I looking at?", image_base64=img_b64, image_mime=mime)
    else:
        print(f"ℹ️ No test image at {test_image} — skipping vision test")
