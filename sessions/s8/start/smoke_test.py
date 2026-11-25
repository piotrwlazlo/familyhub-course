"""Session 8: smoke test. A few quick checks against the RUNNING service, right after it is started or deployed.

Run:  python tests/smoke_test.py http://localhost:<your port>
"""
import sys

import httpx

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8100"
results = []


def check(name: str, ok: bool) -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {name}")


# Example: the health check
response = httpx.get(f"{URL}/health", timeout=10)
check("the health check says ok", response.status_code == 200 and response.json().get("status") == "ok")

# TODO 2: GET {URL}/v1/models: the list in response.json()["data"] has a model with id "family-hub-assistant"

# TODO 3: POST {URL}/v1/chat/completions with one real question (timeout=120). The answer text is in
#         response.json()["choices"][0]["message"]["content"]. Check a fact that must be in it.

# TODO 4: POST {URL}/v1/chat/completions with an empty message list: the status code must be 400

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
