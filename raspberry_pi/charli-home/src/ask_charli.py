#!/usr/bin/env python3
"""
CHARLI Home - Building Block 3: Send a question to CHARLI.
"""

import os
from openai import OpenAI

# -- Connect to CHARLI -------------------------------------------------
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

def ask_charli(question: str, language: str = "en") -> str:
    """
    Sends a question to CHARLI and returns her response.
    """

    lang_name = "English" if language == "en" else "Spanish" if language == "es" else "English"
    print(f"🤔 [{lang_name}] Asking CHARLI...")

    prompt = PI_SYSTEM_PROMPT.replace("{lang_name}", lang_name)

    try:
        response = client.chat.completions.create(
            model="openclaw:main",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user",   "content": question}
            ],
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
    ask_charli("Hello Charli!")
