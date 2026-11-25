"""Session 7 check: fetch_knowledge.py downloads the whole knowledge from the council website, every section of every page.

Run from your main folder, after `python fetch_knowledge.py` and `python search.py --build`:
    python sessions/s7/check.py   (about 1 minute, the model is needed for the last two checks)
"""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder

from common import APP, finish, has_any  # noqa: E402  (also sets up the paths and the fixed date)

import config  # noqa: E402

HERE = Path(__file__).parent
SEARCH_TARGET = 0.95
# Phrases from the later, folded sections of pages built from expandable sections
FOLDED = {
    "support-available-at-blackpool-family-hub.md": ["gambling", "Housing help"],
    "parent-and-carer-panels.md": ["Sip and Share"],
    "supporting-your-child.md": ["HENRY", "Oral care"],
}
results = []


def result(ok: bool, text: str, detail: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {text}")
    if not ok and detail:
        print(f"       {detail}")


try:
    import fetch_knowledge
except Exception as error:
    print(f"FAIL | fetch_knowledge.py cannot be imported: {error}\n"
          "       Copy sessions/s7/start/fetch_knowledge.py and sessions/s7/start/timetable.py to your main folder.")
    finish(0, 1)

# 1-2. main_text on a saved council page (no internet needed)
html = (HERE / "support_page.html").read_text(encoding="utf-8")
try:
    text = fetch_knowledge.main_text(html)
except Exception as error:
    text = ""
    print(f"       main_text failed: {error!r}")
result("Advice and helplines" in text and "Mind" in text,
       "main_text finds the main text of a council page", "the first section of the page is missing")
missing = [p for p in ["Help with money and debt", "gambling", "Housing help"] if p.lower() not in text.lower()]
result(not missing, "main_text keeps every section of a page with expandable sections",
       f"missing in the text: {missing}. Compare the headings on the page with the headings in your text.")

# 3. knowledge/: the same files as the course knowledge, with the right header
expected = (HERE / "expected_files.txt").read_text(encoding="utf-8").split()
have = {p.name for p in config.KNOWLEDGE.glob("*")} if config.KNOWLEDGE.exists() else set()
lost = sorted(set(expected) - have)
result(not lost and not (APP / "knowledge.new").exists(),
       f"knowledge/ has all {len(expected)} files (run python fetch_knowledge.py first)",
       f"missing: {lost[:8]}{' ...' if len(lost) > 8 else ''}")
bad = [p.name for p in config.KNOWLEDGE.glob("*.md")
       if not p.read_text(encoding="utf-8").startswith("# ") or "\nURL: https://" not in p.read_text(encoding="utf-8")[:400]]
result(not bad, "every page starts with '# Title' and 'URL: ...'", f"wrong header: {bad[:8]}")

# 4. the folded sections reached knowledge/
gaps = [f"{name}: {phrase}" for name, phrases in FOLDED.items() for phrase in phrases
        if not (config.KNOWLEDGE / name).exists()
        or phrase.lower() not in (config.KNOWLEDGE / name).read_text(encoding="utf-8").lower()]
result(not gaps, "the downloaded pages have their folded sections", f"missing: {gaps}")

# 5. timetable pages
table = config.KNOWLEDGE / "family-hubs-timetable.md"
rows = table.read_text(encoding="utf-8").count("\n| ") if table.exists() else 0
result(rows > 20, "the timetable page lists the family hub sessions", f"only {rows} table rows")

# 6. search on the new knowledge (needs: python search.py --build)
index_time = max((p.stat().st_mtime for p in config.INDEX_DIR.rglob("*")), default=0) if config.INDEX_DIR.exists() else 0
knowledge_time = max((p.stat().st_mtime for p in config.KNOWLEDGE.glob("*.md")), default=0)
if index_time < knowledge_time:
    result(False, "search finds the right pages", "the index is older than knowledge/: run python search.py --build")
else:
    from search import search  # noqa: E402
    questions = json.loads((HERE.parent / "golden_questions.json").read_text(encoding="utf-8"))
    questions = [q for q in questions if q["expected_pages"] and q["expect"] == "answer"]
    hits = sum(bool(set(q["expected_pages"]) & {hit["page"] for hit in search(q["question"])}) for q in questions)
    result(hits / len(questions) >= SEARCH_TARGET,
           f"search finds the right page for {hits}/{len(questions)} golden questions (target {SEARCH_TARGET:.0%})")

    # 7-8. the assistant answers from the new sections
    import bot  # noqa: E402
    for question, must in [("Where can I get help with gambling?", ["Empowerment", "Lancashire Women"]),
                           ("Where can I get free advice about debt?", ["National Debt"])]:
        try:
            reply = bot.answer(question)
        except Exception as error:
            reply = f"ERROR: {error}"
        result(has_any(reply, must), f"the assistant answers: {question}", f"answer: {reply[:300]!r}")

finish(sum(results), 9)
