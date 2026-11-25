"""Smoke test: a few quick checks against the RUNNING service, right after it is started or deployed.

Run:  python tests/smoke_test.py http://localhost:<port>
"""
import sys

import httpx

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8100"
results = []


def check(name: str, ok: bool) -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {name}")


response = httpx.get(f"{URL}/health", timeout=10)
check("the health check says ok", response.status_code == 200 and response.json().get("status") == "ok")

response = httpx.get(f"{URL}/v1/models", timeout=10)
check("the service offers family-hub-assistant",
      any(model["id"] == "family-hub-assistant" for model in response.json().get("data", [])))

response = httpx.post(f"{URL}/v1/chat/completions", timeout=120, json={
    "messages": [{"role": "user", "content": "What is the phone number for North Family Hub?"}]})
check("a real question gets the right answer",
      response.status_code == 200 and "01253 476480" in response.json()["choices"][0]["message"]["content"])

response = httpx.post(f"{URL}/v1/chat/completions", timeout=10, json={"messages": []})
check("an empty message list gets 400, not a crash", response.status_code == 400)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
