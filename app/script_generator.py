"""
LLM wrapper that turns each text chunk + trend template
into a short‑form video script.
"""
import os
from openai import OpenAI
from typing import List
from tqdm import tqdm

# 1.  Create a client that talks to Groq instead of OpenAI
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

# 2.  Pick a Groq‑hosted model you have access to
MODEL = "llama-3.3-70b-versatile"

def _one_prompt(chunk: str, trend) -> str:
    messages = [
        {"role": "system", "content": trend["system_prompt"]},
        {
            "role": "user",
            "content": (
                "Rewrite the following study notes into an engaging short‑form video script for Instagram Reels using the style directives provided. Return WORD FOR WORD the script to be said, and nothing else.\n\n"
                f"STYLE DIRECTIVES:\n{trend['style_directives']}\n\n"
                f"STUDY NOTES:\n{chunk}"
            ),
        },
    ]
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    return resp.choices[0].message.content.strip()

def generate_scripts(chunks: List[str], trend) -> List[str]:
    """Generate a script per chunk, preserving order."""
    return [_one_prompt(c, trend) for c in tqdm(chunks, desc="LLM scripting")]
