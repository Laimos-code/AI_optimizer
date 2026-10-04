import os, json, httpx
from dotenv import load_dotenv
load_dotenv()

GROQ_KEY = os.environ["GROQ_API_KEY"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]

print("=== GROQ ===")
r = httpx.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={"Authorization": f"Bearer {GROQ_KEY}"},
    json={
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": "Say hi in 3 words"}],
        "max_tokens": 20,
    },
    timeout=30.0,
)
print(r.status_code)
print(json.dumps(r.json(), indent=2))

print("\n=== GEMINI ===")
r = httpx.post(
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
    params={"key": GEMINI_KEY},
    json={"contents": [{"parts": [{"text": "Say hi in 3 words"}]}]},
    timeout=30.0,
)
print(r.status_code)
print(json.dumps(r.json(), indent=2))