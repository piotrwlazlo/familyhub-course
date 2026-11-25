"""Runs one refresh scenario in a throw-away copy of your folder. Used by check.py: you do not run it yourself.

The downloads are simulated, so the check needs no internet and gives the same result every time.
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

import httpx

APP = Path.cwd()
sys.path.insert(0, str(APP))
import config  # noqa: E402

config.TODAY = date(2026, 11, 22)          # the knowledge was saved on 21 November 2026
import logs  # noqa: E402
import refresh  # noqa: E402
import search  # noqa: E402
import sources  # noqa: E402

PRISTINE = APP / "pristine"                # the knowledge as it was before the check
MARK = "Updated by the council on 24 November 2026."
CHANGED, BROKEN = "register-a-birth", "relationship-support"
JUNK = ("Sorry, this page is temporarily unavailable. We are carrying out planned maintenance on our website. "
        "Please try again later. If your enquiry is urgent, please contact us. ") * 3
PAGES = {search.read_page(path)["url"]: path for path in PRISTINE.glob("*.md")}


def body(path) -> str:
    return path.read_text(encoding="utf-8").split("\n\n", 1)[1]


def fake_text(scenario):
    def download_text(url):
        page = PAGES[url].stem
        if scenario == "down" or (scenario == "good" and page == BROKEN):
            raise httpx.ConnectError("connection refused")
        if scenario == "junk":
            return JUNK
        return body(PAGES[url]) + (f"\n\n{MARK}" if page == CHANGED else "")
    return download_text


def fake_timetable(scenario):
    def download_timetable():
        if scenario == "down":
            raise httpx.ConnectError("connection refused")
        return json.loads((PRISTINE / "timetable.json").read_text(encoding="utf-8"))
    return download_timetable


def use_fakes(scenario):
    for module in (sources, refresh):      # works with "import sources" and with "from sources import ..."
        if hasattr(module, "download_text"):
            module.download_text = fake_text(scenario)
        if hasattr(module, "download_timetable"):
            module.download_timetable = fake_timetable(scenario)


def rules() -> dict:
    """check_pages on four made-up staging folders."""
    results = {}
    cases = {"good data": ([], 91, "[]"),
             "20 failed downloads": ([f"https://example.org/{i}" for i in range(20)], 91, "[]"),
             "timetable with 3 sessions": ([], 3, "[]"),
             "staff data in timetable.json": ([], 91, '[{"title": "x", "sys": {"owner": "x"}}]')}
    timetable = (PRISTINE / "family-hubs-timetable.md").read_text(encoding="utf-8")
    head, rows = timetable.split("| Activity |", 1)
    rows = rows.split("\n")
    for name, (failed, keep_rows, timetable_json) in cases.items():
        staging = APP / "rules-test"
        shutil.rmtree(staging, ignore_errors=True)
        shutil.copytree(PRISTINE, staging / "knowledge")
        (staging / "knowledge" / "family-hubs-timetable.md").write_text(
            head + "| Activity |" + "\n".join(rows[:keep_rows + 2]), encoding="utf-8")
        (staging / "knowledge" / "timetable.json").write_text(timetable_json, encoding="utf-8")
        try:
            problems = refresh.check_pages(staging, failed)
        except Exception as error:
            problems = f"crash: {type(error).__name__}: {error}"
        results[name] = problems
        shutil.rmtree(staging)
    return results


if __name__ == "__main__":
    scenario = sys.argv[1]
    logs.setup_logging()
    if scenario == "rules":
        print("RESULT " + json.dumps(rules()))
    elif scenario == "rollback":
        print("RESULT " + json.dumps(refresh.rollback()))
    else:
        use_fakes(scenario)
        print("RESULT " + json.dumps(refresh.refresh()))
