"""Session 10 check: the refresh keeps good data, refuses bad data and can go back.

Run from your main folder:  python sessions/s10/check.py   (about 2 minutes, no model and no internet needed)
It works in a throw-away copy of your folder with simulated downloads: your own knowledge and index are not touched.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder

from common import APP, finish  # noqa: E402  (also sets up the paths and the fixed date)

import config  # noqa: E402

SKIP = shutil.ignore_patterns("logs", "staging", "backup", "__pycache__", ".git", "tests")
passed, total = 0, 5


def run(folder: Path, scenario: str):
    """Run one scenario; returns (result, new log lines)."""
    log = folder / "logs" / "familyhub.log"
    before = log.stat().st_size if log.exists() else 0
    done = subprocess.run([sys.executable, str(folder / "sessions" / "s10" / "scenarios.py"), scenario],
                          cwd=folder, capture_output=True, text=True, timeout=900)
    result = None
    for line in done.stdout.splitlines():
        if line.startswith("RESULT "):
            result = json.loads(line[7:])
    if result is None:
        error = [line for line in done.stderr.splitlines() if line.strip()][-3:]
        print("       the scenario crashed: " + "\n       ".join(error))
    lines = log.read_text(encoding="utf-8")[before:] if log.exists() else ""
    return result, lines


def fingerprint(folder: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(folder.glob("*")):
        digest.update(path.name.encode() + path.read_bytes())
    return digest.hexdigest()


def report(ok: bool, text: str) -> None:
    global passed
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'} | {text}")


for name in ("refresh.py", "sources.py"):
    if not (APP / name).exists():
        print(f"FAIL | {name} is missing in your main folder (see step 1 of the task card)")
        finish(0, total)
if not hasattr(config, "STAGING_DIR"):
    print("FAIL | config.py has no STAGING_DIR: paste sessions/s10/start/config_addition.py at the end of config.py")
    finish(0, total)

with tempfile.TemporaryDirectory() as temp:
    folder = Path(temp) / "familyhub"
    shutil.copytree(APP, folder, ignore=SKIP, symlinks=True)
    shutil.copytree(APP / "knowledge", folder / "pristine")
    live = folder / "knowledge"
    start = fingerprint(live)
    print("Working in a throw-away copy of your folder. Every scenario simulates one night.\n")

    # 1. The quick rules
    result, _ = run(folder, "rules")
    expected = {"good data": False, "20 failed downloads": True, "timetable with 3 sessions": True,
                "staff data in timetable.json": True}
    if result is None:
        report(False, "check_pages runs")
    else:
        wrong = [case for case, problem in expected.items()
                 if isinstance(result[case], str) or bool(result[case]) != problem]
        for case in wrong:
            print(f"       {case}: check_pages returned {result[case]!r}")
        report(not wrong, "check_pages: good data passes; too many failed downloads, a short timetable "
                          "and staff data are each found")

    # 2. The council website is down
    result, lines = run(folder, "down")
    ok = result is False and fingerprint(live) == start and "| ERROR" in lines
    if result is not False:
        print(f"       refresh() returned {result!r}, expected False")
    report(ok, "website down: refresh() returns False, the live knowledge stays the same, an ERROR is logged")

    # 3. Every page comes back as a maintenance page
    result, lines = run(folder, "junk")
    ok = result is False and fingerprint(live) == start and "| ERROR" in lines and "golden" in lines
    if result is not False:
        print(f"       refresh() returned {result!r}, expected False")
    report(ok, "maintenance pages: the golden questions stop the refresh, the live knowledge stays the same")

    # 4. A normal night: one page changed, one download failed
    result, lines = run(folder, "good")
    changed = (live / "register-a-birth.md").read_text(encoding="utf-8")
    broken = (live / "relationship-support.md").read_bytes() == (folder / "pristine" / "relationship-support.md").read_bytes()
    clean = '"sys"' not in (live / "timetable.json").read_text(encoding="utf-8")
    backup = (folder / "backup" / "knowledge" / "register-a-birth.md").exists() and (folder / "backup" / "index").exists()
    details = {"refresh() returns True": result is True,
               "the changed page is live": "24 November 2026" in changed,
               "the failed page keeps its old copy": broken,
               "a WARNING names the failed page": "| WARNING" in lines and "Relationship-support" in lines,
               "timetable.json has no staff data": clean,
               "the previous knowledge and index are in backup/": backup,
               "the new index is live": (folder / "index").exists() and not (folder / "staging").exists()}
    for text, good in details.items():
        if not good:
            print(f"       not yet: {text}")
    report(all(details.values()), "normal night: the new data goes live, the failed page keeps its old copy")

    # 5. Rollback
    result, lines = run(folder, "rollback")
    ok = result is True and fingerprint(live) == start and "24 November 2026" in (
        folder / "backup" / "knowledge" / "register-a-birth.md").read_text(encoding="utf-8")
    report(ok, "rollback: the knowledge from before the refresh is live again, the newer one waits in backup/")

finish(passed, total)
