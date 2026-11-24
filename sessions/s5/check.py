"""Session 5 check: the team's own golden questions are in, and the whole test runs with a good score.

Run from the familyhub-app folder:  python sessions/s5/check.py   (takes 2 to 3 minutes)
"""
import json
import subprocess
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent.parent
TARGET = 80          # the gold version of session 4 scores about 86% on our questions

golden = json.loads((APP / "tests" / "golden.json").read_text(encoding="utf-8"))
own = [q for q in golden if q["category"] == "team"]
print(f"Golden questions: {len(golden)}, written by the team (category 'team'): {len(own)}")
if len(own) < 10:
    print("NOT YET: add at least 10 questions of your own to tests/golden.json (category 'team', ids T01, T02, ...)")
    sys.exit(1)

subprocess.run([sys.executable, str(APP / "tests" / "run_tests.py")], cwd=APP, check=True)
first = (APP / "tests" / "report.md").read_text(encoding="utf-8").split("\n")[2]      # "**Score: 77/89 = 86%** ..."
score = int(first.split("=")[1].split("%")[0])
print(f"Score {score}% (target at least {TARGET}%)")
print("SESSION DONE" if score >= TARGET else "NOT YET: read the failures in tests/report.md")
sys.exit(0 if score >= TARGET else 1)
