#!/usr/bin/env python3
"""
CHARLI Home - Building Block 3: Send a question to CHARLI.

Connects to the OpenClaw gateway on the Mac Mini via Tailscale.
This is the ONLY step in the pipeline that costs tokens — everything
else (wake word, recording, transcription, TTS) runs locally for free.

Now supports conversation context: sends the last 3 turns (6 messages)
so CHARLI can handle follow-up questions like "What about tomorrow?"
after you ask about weather.
"""

import os
from openai import OpenAI

# -- Connect to CHARLI -----------------------------------------------------
charli_host  = os.environ.get("CHARLI_HOST", "http://100.91.206.1:18789")
charli_token = os.environ.get("CHARLI_TOKEN", "")

client = OpenAI(
    base_url=f"{charli_host}/v1",
    api_key=charli_token
)

PI_SYSTEM_PROMPT = """You are responding through the CHARLI Home Raspberry Pi voice assistant.
Keep answers SHORT: 1 to 3 sentences maximum.
No bullet points, no numbered lists, no markdown symbols like * or #.
Speak naturally, like you're talking to someone in the room.
Respond in {lang_name}. Match the language the user spoke."""

# Max conversation turns to send for context (keeps token costs low)
MAX_CONTEXT_TURNS = 3


def ask_charli(question: str, language: str = "en", history: list = None) -> str:
    """
    Sends a question to CHARLI and returns her response.

    Args:
        question: The user's transcribed question
        language: Detected language code ("en", "es", etc.)
        history: Optional list of past messages [{"role": "user"|"charli", "text": "..."}]
                 Only the last MAX_CONTEXT_TURNS turns are sent to save tokens.

    The history parameter lets CHARLI understand follow-ups:
      You: "What's the capital of France?"
      CHARLI: "The capital of France is Paris."
      You: "How big is it?"  ← CHARLI knows "it" = Paris because of history
    """

    lang_name = "English" if language == "en" else "Spanish" if language == "es" else "English"
    print(f"🤔 [{lang_name}] Asking CHARLI...")

    prompt = PI_SYSTEM_PROMPT.replace("{lang_name}", lang_name)

    # Build message list: system prompt + conversation history + new question
    messages = [{"role": "system", "content": prompt}]

    # Add recent conversation history for context
    if history:
        # Take the last N turns (each turn = 1 user + 1 assistant message)
        recent = history[-(MAX_CONTEXT_TURNS * 2):]
        for entry in recent:
            # Map our role names to OpenAI API role names
            role = "user" if entry["role"] == "user" else "assistant"
            messages.append({"role": role, "content": entry["text"]})

    # Add the current question
    messages.append({"role": "user", "content": question})

    try:
        response = client.chat.completions.create(
            model="openclaw:main",
            messages=messages,
            max_tokens=150,
            user="pi-home"
        )

        answer = response.choices[0].message.content
        print(f"🤖 CHARLI says: '{answer}'")
        return answer

    except Exception as e:
        print(f"❌ Error asking CHARLI: {e}")
        return "I'm sorry Sir, I'm having trouble connecting to my brain right now."


if __name__ == "__main__":
    # Test without history
    ask_charli("Hello Charli!")

    # Test with history (simulated follow-up)
    test_history = [
        {"role": "user", "text": "What's the capital of France?"},
        {"role": "charli", "text": "The capital of France is Paris."},
    ]
    ask_charli("How big is it?", history=test_history)
