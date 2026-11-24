# Session 7: The assistant passes the test

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** every change is checked with numbers, not by feel. You write golden questions that parents really ask, a program asks them all and writes a report with a score.

**You start from** the session 6 version (if yours does not pass its check, ask the instructor for the working version).

**You get**
- `sessions/s7/start/golden.json`: 89 golden questions we wrote. Copy to `tests/golden.json`
- `sessions/s7/start/run_tests.py`: copy to `tests/`. Ready: `norm`, `check` and `report`. You write `run_one` and `main`

**You build**

| Where | What |
|---|---|
| `tests/golden.json` | At least 10 questions of your own: `"category": "team"`, ids `T01`, `T02` ... Each with what the answer must contain |
| `tests/run_tests.py`: `run_one(item)` | Asks one question, checks the reply, measures the time |
| `tests/run_tests.py`: `main()` | Runs all questions (4 at a time), saves `tests/results.json` and `tests/report.md`, prints the score |

A golden question looks like this:
```json
{"id": "T01", "category": "team", "question": "Do I have to book Chatting with Children?",
 "expect": "answer", "must_contain": [["no booking", "just pop along"]], "must_not_contain": []}
```
`must_contain` is a list of groups: one phrase from every group must be in the answer. `expect` is one of `answer`, `no_answer`, `off_topic`, `safe`.

## Steps
1. Each person writes 3 questions that parents ask at the front desk. Find the right answer in `knowledge/` yourself first.
2. Write `run_one` and `main`. Run `python tests/run_tests.py T01 T02` (only your questions) until it works.
3. Run all questions: `python tests/run_tests.py`. Open `tests/report.md`.
4. Read every failure. Is the assistant wrong, or is the test wrong? Write it down.
5. Change one thing and run all questions again: `TOP_K` 3 or 8, `CHUNK_CHARS` 500 or 1500 (then `python search.py --build`), or one rule in the prompt. Did the score go up or down? We keep the best change.
6. Run the check: `python sessions/s7/check.py`

## Prompts for the AI assistant
- *"Write run_one(item) that calls bot.answer(item['question']) inside try/except, measures the time with time.time(), calls check(item, reply) and returns {**item, 'answer': reply, 'seconds': ..., **check(...)}. Print one line: id, PASS or FAIL, seconds, the question."*
- *"Write main() that reads tests/golden.json, keeps only the ids in sys.argv[1:] if any are given, runs run_one for all items with ThreadPoolExecutor(max_workers=4), writes results.json and report.md next to this file, and prints the report up to the line '## Failures'."*

**Done when** `python sessions/s7/check.py` prints `SESSION DONE`: at least 10 team questions, and a score of at least 80%.

## Hints
- A failure is not always the assistant's fault. Our own question OT77 expects "no answer", but one page does say something about school transport. Fix the test when the test is wrong.
- Questions with "next" depend on the date. The test always uses 22 November 2026, the day after the knowledge was saved.
- The full run takes 2 to 3 minutes. While you work on one problem, run only that question.
