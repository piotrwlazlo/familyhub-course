"""Session 5 check: search finds the right page, and answers come with source links.

Run from the familyhub-app folder (build the index first):  python sessions/s5/check.py
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder

from common import check_answers, has_any  # noqa: E402,F401  (also sets up the paths and the fixed date)

import bot  # noqa: E402
from search import search  # noqa: E402

TARGET = 0.90     # at least 90% of the golden questions must find a passage from the right page

# Part 1: search only (no model, fast). Golden questions that name the page with the answer.
questions = json.loads((Path(__file__).parent.parent / "golden_questions.json").read_text(encoding="utf-8"))
questions = [q for q in questions if q["expected_pages"] and q["expect"] == "answer"]
hits = 0
for q in questions:
    pages = [hit["page"] for hit in search(q["question"])]
    found = bool(set(q["expected_pages"]) & set(pages))
    hits += found
    if not found:
        print(f"MISS | {q['question']}\n       expected {q['expected_pages']}, found {sorted(set(pages))}")
rate = hits / len(questions)
print(f"\nSearch: right page in the top passages for {hits}/{len(questions)} questions = {rate:.0%} (target {TARGET:.0%})\n")

# Part 2: three questions the old version could not answer; each answer needs its fact and a source link
CASES = [
    ("When is Neuro Ninjas and what ages is it for?", [["Thursday"], ["4.30"], ["Sources"]], []),
    ("What is the Samaritans phone number?",          [["116 123"], ["Sources"]], []),
    ("What is the domestic abuse helpline number?",   [["0808 2000 247"], ["Sources"]], []),
]
if rate < TARGET:
    print("NOT YET: search finds too few right pages. Look at the misses above.")
    sys.exit(1)
check_answers(CASES, bot.answer)
