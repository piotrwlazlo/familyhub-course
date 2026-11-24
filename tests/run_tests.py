"""Session 5: ask all golden questions and write a report.

Run:    python tests/run_tests.py            (all questions, 4 at a time)
        python tests/run_tests.py TI08 OT51  (only these ids)
Result: tests/report.md (score + every failure) and tests/results.json (every answer)

expect = answer      the answer must contain the facts in must_contain
         no_answer   our pages do not have it: the assistant must not invent an answer
         off_topic   the assistant must give our fixed off-topic reply
         safe        nothing from must_not_contain may appear (facts in must_contain optional)
"""
import json
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import config  # noqa: E402

config.TODAY = date(2026, 11, 22)   # the knowledge was saved on 21 November 2026
import bot  # noqa: E402

FIXED_REPLIES = (config.OFF_TOPIC_REPLY, config.FALLBACK_REPLY, config.CRISIS_REPLY)
NOT_FOUND_WORDS = ["not contain", "no information", "not able to find", "could not find", "couldn't find",
                   "not listed", "contact your local family hub", "there is no", "there are no"]


def norm(text: str) -> str:
    """Make texts easy to compare: lower case, no spaces, 9:30 = 9.30, curly quotes = straight."""
    text = text.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", "", re.sub(r"(\d):(\d)", r"\1.\2", text))


def check(item: dict, reply: str) -> dict:
    text = reply.split("\n\n**Sources:**")[0]        # the facts must be in the answer, not in the links
    missing = [group[0] for group in item["must_contain"] if not any(norm(alt) in norm(text) for alt in group)]
    forbidden = [word for word in item["must_not_contain"] if norm(word) in norm(text)]
    fixed = text in FIXED_REPLIES
    if item["expect"] == "answer":
        ok = not fixed and not missing and not forbidden
    elif item["expect"] == "no_answer":
        ok = (fixed or any(norm(w) in norm(text) for w in NOT_FOUND_WORDS)) and not forbidden
    elif item["expect"] == "off_topic":
        ok = text == config.OFF_TOPIC_REPLY
    else:                                             # safe
        ok = not missing and not forbidden
    return {"pass": ok, "missing": missing, "forbidden": forbidden}


def run_one(item: dict) -> dict:
    start = time.time()
    try:
        reply = bot.answer(item["question"])
    except Exception as error:                        # a crash is a failure, not the end of the run
        reply = f"ERROR: {error}"
    result = {**item, "answer": reply, "seconds": round(time.time() - start, 1), **check(item, reply)}
    print(f"{item['id']:6} {'PASS' if result['pass'] else 'FAIL'} {result['seconds']:5}s  {item['question'][:70]}", flush=True)
    return result


def report(results: list[dict]) -> str:
    by_category = defaultdict(list)
    for r in results:
        by_category[r["category"]].append(r)
    total = sum(r["pass"] for r in results)
    lines = ["# Family Hub assistant: test report", "",
             f"**Score: {total}/{len(results)} = {100 * total // len(results)}%** · model {config.MODEL} · "
             f"{time.strftime('%Y-%m-%d %H:%M')}", "", "| Category | Questions | Passed |", "|---|---|---|"]
    for category, rs in by_category.items():
        lines.append(f"| {category} | {len(rs)} | {sum(r['pass'] for r in rs)} |")
    lines += ["", f"Average time per question: {sum(r['seconds'] for r in results) / len(results):.1f} s", "",
              "## Failures", ""]
    for r in results:
        if not r["pass"]:
            lines += [f"### {r['id']}: {r['question']}",
                      f"- expect: {r['expect']} · missing: {r['missing'] or '-'} · forbidden: {r['forbidden'] or '-'}",
                      f"- answer: {r['answer'][:500]}", ""]
    return "\n".join(lines)


def main():
    items = json.loads((HERE / "golden.json").read_text(encoding="utf-8"))
    if sys.argv[1:]:
        items = [item for item in items if item["id"] in sys.argv[1:]]
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(run_one, items))
    (HERE / "results.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    text = report(results)
    (HERE / "report.md").write_text(text, encoding="utf-8")
    print("\n" + text.split("## Failures")[0])


if __name__ == "__main__":
    main()
