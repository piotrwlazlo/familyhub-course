"""Session 9: a quick quality check of your unit tests. Do they catch broken code?

Run from your main folder:  python sessions/s9/hunt.py

The hunt makes 6 broken versions of our functions, one at a time (each with one small, realistic mistake),
and runs your tests (tests/test_units.py) against each one in a temporary copy. Your own files are not changed.
A broken version is CAUGHT when at least one of your tests fails. It SURVIVES when all your tests still pass:
then write a test for the rule it breaks.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

APP = Path(__file__).resolve().parent.parent.parent      # your main folder
TESTS = "tests/test_units.py"

# (what is broken, file, the correct code, the broken code)
BROKEN = [
    ("make_chunks: the last passage of a page is lost", "search.py",
     "    if current:\n        chunks.append(current)\n    return chunks", "    return chunks"),
    ("fuse: the worst result comes first", "search.py",
     "return sorted(score, key=score.get, reverse=True)", "return sorted(score, key=score.get)"),
    ("is_crisis: capital letters are not found ('I AM IN DANGER')", "checks.py",
     "text = question.lower()", "text = question"),
    ("unknown_phone_numbers: a real number written with spaces is reported as unknown", "checks.py",
     "if digits(number) not in known]", "if number not in known]"),
    ("check_answer: an answer without sources gets through", "checks.py",
     "    if not result.sources:", "    if False:"),
    ("check_answer: an answer with personal data gets through", "checks.py",
     "if result.contains_advice or result.contains_personal_data:", "if result.contains_advice:"),
]


def run_tests(folder: Path) -> bool:
    """True if all tests pass in this folder."""
    done = subprocess.run([sys.executable, "-m", "pytest", TESTS, "-q", "-x", "-p", "no:cacheprovider"],
                          cwd=folder, capture_output=True, text=True, timeout=300)
    return done.returncode == 0


def copy_app(target: Path) -> None:
    """Copy only the code and the tests: the temporary copy has no knowledge, index or logs."""
    for path in APP.glob("*.py"):
        shutil.copy(path, target)
    (target / "tests").mkdir()
    shutil.copy(APP / TESTS, target / TESTS)


def hunt() -> tuple[int, int, list[str]]:
    if not (APP / TESTS).exists():
        print(f"No {TESTS} yet: copy sessions/s9/start/test_units.py to tests/ first.")
        sys.exit(1)
    print("Your tests on the real code ...", end=" ", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        copy_app(Path(tmp))
        if not run_tests(Path(tmp)):
            print("FAIL\nFirst make all your tests pass on the real code:  python -m pytest tests/test_units.py")
            sys.exit(1)
    print("all pass\n")

    caught, alive = 0, []
    for what, file, correct, broken in BROKEN:
        with tempfile.TemporaryDirectory() as tmp:
            copy_app(Path(tmp))
            code = (Path(tmp) / file).read_text(encoding="utf-8")
            if correct not in code:
                print(f"SKIP     | {what}\n           ({file} is not the working version: get it from your instructor)")
                alive.append(what)
                continue
            (Path(tmp) / file).write_text(code.replace(correct, broken, 1), encoding="utf-8")
            if run_tests(Path(tmp)):
                print(f"SURVIVES | {what}")
                alive.append(what)
            else:
                print(f"CAUGHT   | {what}")
                caught += 1
    print(f"\nCaught {caught} of {len(BROKEN)} broken versions.")
    if alive:
        print("For each one that survives: write a test that passes on the real code and fails on that mistake.")
    return caught, len(BROKEN), alive


if __name__ == "__main__":
    caught, total, _ = hunt()
    sys.exit(0 if caught == total else 1)
