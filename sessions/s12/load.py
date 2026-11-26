"""Send questions straight to the model so the dashboards have something to show.

Run from your main folder:  python sessions/s12/load.py                 (2 people asking, 10 questions)
                            python sessions/s12/load.py --users 4 --questions 20
The questions are the golden questions from sessions/golden_questions.json (no personal data).
"""
import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import APP  # noqa: E402

import config  # noqa: E402


def ask(question: str) -> tuple[float, int]:
    """One question to the model. Returns (seconds, tokens written)."""
    start = time.time()
    reply = httpx.post(f"{config.MODEL_URL}/chat/completions", timeout=300, json={
        "model": config.MODEL,
        "messages": [{"role": "system", "content": "You help families in Blackpool. Answer in 3 to 5 sentences."},
                     {"role": "user", "content": question}],
        "max_tokens": 300,
    })
    reply.raise_for_status()
    return time.time() - start, reply.json()["usage"]["completion_tokens"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--users", type=int, default=2, help="how many people ask at the same time (1-8)")
    parser.add_argument("--questions", type=int, default=10, help="how many questions in total (1-40)")
    args = parser.parse_args()
    users, count = max(1, min(args.users, 8)), max(1, min(args.questions, 40))

    questions = [item["question"] for item in json.loads((APP / "sessions" / "golden_questions.json").read_text())]
    chosen = random.sample(questions, min(count, len(questions)))
    print(f"{count} questions, {users} at the same time, to {config.MODEL} ... watch Grafana now")

    start = time.time()
    with ThreadPoolExecutor(max_workers=users) as pool:
        results = list(pool.map(ask, chosen))
    took = time.time() - start
    tokens = sum(written for _, written in results)
    slowest = max(seconds for seconds, _ in results)
    print(f"done in {took:.0f} s | {tokens} tokens written | {tokens / took:.0f} tokens/s for the whole group"
          f" | slowest answer {slowest:.1f} s")


if __name__ == "__main__":
    main()
