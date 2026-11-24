"""Helpers for the session checks. You do not need to change this file."""
import re
import sys
from datetime import date
from pathlib import Path

APP = Path(__file__).resolve().parent.parent      # the familyhub-app folder
sys.path.insert(0, str(APP))

import config  # noqa: E402

# The knowledge was saved on 21 November 2026. A fixed "today" keeps answers like
# "when is the next ..." the same every time we run the checks.
config.TODAY = date(2026, 11, 22)


def norm(text: str) -> str:
    """Make texts easy to compare: lower case, no spaces, 9:30 = 9.30, curly quotes = straight."""
    text = text.lower().replace("’", "'").replace("–", "-").replace("—", "-")
    text = re.sub(r"(\d):(\d)", r"\1.\2", text)
    return re.sub(r"\s+", "", text)


def has_any(text: str, alternatives: list[str]) -> bool:
    """True if the text contains at least one of the alternatives."""
    return any(norm(alt) in norm(text) for alt in alternatives)


def check_answers(cases: list[tuple], ask) -> None:
    """cases: (question, must_contain, must_not_contain).
    must_contain is a list of groups; each group is a list of alternatives, one of them must be in the answer."""
    passed = 0
    for question, must, must_not in cases:
        try:
            reply = ask(question)
        except Exception as error:          # a crash is a failure, not the end of the check
            reply = f"ERROR: {error}"
        missing = [group[0] for group in must if not has_any(reply, group)]
        forbidden = [word for word in must_not if has_any(reply, [word])]
        ok = not missing and not forbidden and not reply.startswith("ERROR")
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'} | {question}")
        if not ok:
            print(f"       missing: {missing or '-'}  forbidden: {forbidden or '-'}")
            print(f"       answer: {reply[:300]!r}")
    finish(passed, len(cases))


def finish(passed: int, total: int) -> None:
    print(f"\n{passed}/{total} passed")
    print("SESSION DONE" if passed == total else "NOT YET: fix the failures above and run the check again")
    sys.exit(0 if passed == total else 1)
