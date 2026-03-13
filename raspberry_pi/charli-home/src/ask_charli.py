#!/usr/bin/env python3
"""
CHARLI Home - Building Block 3: Send a question to CHARLI's brain.

This is the network link between the Pi (ears/mouth) and the Mac Mini (brain).
The Pi records and transcribes your voice locally, then sends the TEXT
to OpenClaw on the Mac Mini, which runs the actual LLM to generate a response.

*** THIS IS THE ONLY STEP THAT COSTS TOKENS ***
Everything else (wake word, recording, transcription, TTS) is 100% local and free.

How it works:
  1. Takes the transcribed question ("What's the weather?")
  2. Optionally includes conversation history for follow-up questions
  3. Sends it to OpenClaw via the OpenAI-compatible API
  4. Returns CHARLI's response ("It's 72 degrees and sunny.")

The OpenAI Python client works with ANY OpenAI-compatible API server,
not just OpenAI's servers. OpenClaw exposes the same API format, so we
just point the client at our Mac Mini's URL instead of api.openai.com.
It's like using fetch() to call a REST API — same pattern you know from Node.
"""

import os
from openai import OpenAI  # pip package: openai (works with OpenClaw too)

# ── Connect to the Brain (Mac Mini) ──────────────────────────────────

# The Mac Mini's OpenClaw URL, accessible via Tailscale private network.
# os.environ.get() is like: process.env.CHARLI_HOST || "http://100.91.206.1:18789"
charli_host  = os.environ.get("CHARLI_HOST", "http://100.91.206.1:18789")

# Auth token from the Mac Mini's ~/.openclaw/openclaw.json file.
# This proves to OpenClaw that we're authorized to make requests.
charli_token = os.environ.get("CHARLI_TOKEN", "")

# Create the OpenAI client pointed at our Mac Mini instead of OpenAI's servers.
# base_url + "/v1" gives us: http://100.91.206.1:18789/v1
# which is where OpenClaw serves its OpenAI-compatible API.
# In Node.js/fetch terms, this is like:
#   const api = new OpenAI({ baseURL: 'http://100.91.206.1:18789/v1' })
client = OpenAI(
    base_url=f"{charli_host}/v1",
    api_key=charli_token
)

# ── System Prompt ─────────────────────────────────────────────────────
# This is the "personality" instruction sent with every request.
# It tells the LLM HOW to respond — short, natural, voice-friendly.
# {lang_name} gets replaced with "English" or "Spanish" at runtime.
PI_SYSTEM_PROMPT = """You are responding through the CHARLI Home Raspberry Pi voice assistant.
Keep answers SHORT: 1 to 3 sentences maximum.
No bullet points, no numbered lists, no markdown symbols like * or #.
Speak naturally, like you're talking to someone in the room.
Respond in {lang_name}. Match the language the user spoke."""

# ── Conversation Context ──────────────────────────────────────────────
# How many past conversation "turns" to include for context.
# A "turn" = 1 user message + 1 CHARLI response = 2 messages.
# 3 turns = 6 messages max sent to the LLM.
# More turns = better follow-up understanding, but more tokens (more cost).
MAX_CONTEXT_TURNS = 3


def ask_charli(question: str, language: str = "en", history: list = None) -> str:
    """
    Sends a question to CHARLI and returns her response.

    Args:
        question: The user's transcribed question (from Whisper)
        language: Detected language code ("en", "es", etc.)
        history:  Optional conversation history for context.
                  A list of dicts: [{"role": "user"|"charli", "text": "..."}]
                  Only the last MAX_CONTEXT_TURNS turns are sent to save tokens.

    Why conversation history matters:
      Without it:
        You: "What's the capital of France?"    → "Paris"
        You: "How big is it?"                   → "How big is what?" (confused!)

      With it (last 3 turns included):
        You: "What's the capital of France?"    → "Paris"
        You: "How big is it?"                   → "Paris has about 2.1 million people"
        CHARLI knows "it" = Paris because she can see the previous messages.

    Returns:
        CHARLI's response as a string. On error, returns a friendly error message.
    """

    # Map language code to human-readable name for the system prompt
    lang_name = "English" if language == "en" else "Spanish" if language == "es" else "English"
    print(f"🤔 [{lang_name}] Asking CHARLI...")

    # Fill in the language name in the system prompt template
    prompt = PI_SYSTEM_PROMPT.replace("{lang_name}", lang_name)

    # ── Build the Messages Array ──────────────────────────────────
    # The OpenAI API expects a list of messages in this format:
    #   [
    #     {"role": "system",    "content": "You are a helpful assistant..."},
    #     {"role": "user",      "content": "What's the capital of France?"},
    #     {"role": "assistant", "content": "The capital of France is Paris."},
    #     {"role": "user",      "content": "How big is it?"},  ← NEW question
    #   ]
    #
    # "system" = personality/instructions (always first)
    # "user"   = what the human said
    # "assistant" = what CHARLI said previously
    messages = [{"role": "system", "content": prompt}]

    # ── Add Conversation History (if available) ───────────────────
    if history:
        # Slice the last N turns from history.
        # Each turn is 2 messages, so MAX_CONTEXT_TURNS * 2 = 6 messages max.
        # Python's list[-6:] takes the last 6 items, like JS array.slice(-6).
        recent = history[-(MAX_CONTEXT_TURNS * 2):]

        for entry in recent:
            # Our internal format uses "user" and "charli" as role names,
            # but the OpenAI API expects "user" and "assistant".
            # So we map "charli" → "assistant" here.
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["text"]})

    # Add the current (new) question at the end
    messages.append({"role": "user", "content": question})

    # ── Send to OpenClaw ──────────────────────────────────────────
    try:
        # client.chat.completions.create() sends an HTTP POST request
        # to the Mac Mini's OpenClaw API. It's a blocking call — that's
        # why charli_home.py runs it in run_in_executor().
        #
        # In Node.js/fetch terms:
        #   const response = await fetch(`${CHARLI_HOST}/v1/chat/completions`, {
        #     method: 'POST',
        #     headers: { 'Authorization': `Bearer ${token}` },
        #     body: JSON.stringify({ model: 'openclaw:main', messages, max_tokens: 150 })
        #   });
        response = client.chat.completions.create(
            model="openclaw:main",   # Which model to use on OpenClaw
            messages=messages,        # The conversation (system + history + new question)
            max_tokens=150,           # Cap response length (keeps answers short + saves tokens)
            user="pi-home"            # Identifies this request as coming from the Pi
        )

        # Extract the text from the API response.
        # The response structure is: response.choices[0].message.content
        # Like: const answer = response.data.choices[0].message.content
        answer = response.choices[0].message.content
        print(f"🤖 CHARLI says: '{answer}'")
        return answer

    except Exception as e:
        print(f"❌ Error asking CHARLI: {e}")
        return "I'm sorry Sir, I'm having trouble connecting to my brain right now."


# ── Standalone Test ───────────────────────────────────────────────────
# Test this building block directly:
#   python3 src/ask_charli.py
# Requires CHARLI_HOST and CHARLI_TOKEN env vars to be set.
if __name__ == "__main__":
    # Test 1: Simple question (no history)
    ask_charli("Hello Charli!")

    # Test 2: Follow-up with history (simulates a conversation)
    test_history = [
        {"role": "user", "text": "What's the capital of France?"},
        {"role": "charli", "text": "The capital of France is Paris."},
    ]
    ask_charli("How big is it?", history=test_history)
