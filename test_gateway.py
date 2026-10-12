import json, httpx

AIO_KEY = "paste_your_aio_key_here"

r = httpx.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"X-API-Key": "aiobn-msnwQ8_-d0_IrOBRJQGov36Vp4yKdqyiu81yGeYs"},
    json={
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": "Say hi in 3 words"}],
        "max_tokens": 200,
        "metadata": {"feature": "smoke-test"},
    },
    timeout=60.0,
)
print(r.status_code)
print(json.dumps(r.json(), indent=2))