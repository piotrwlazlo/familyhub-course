"""Session 8 check: the assistant writes useful logs, keeps the model's reasoning apart and has a health check.

Run from your main folder:  python sessions/s8/check.py   (about 1 minute)
The check writes its own logs to logs/check/, so your logs/familyhub.log stays as it is.
"""
import shutil
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder

from common import APP, finish  # noqa: E402  (also sets up the paths and the fixed date)

import config  # noqa: E402

config.LOG_DIR = APP / "logs" / "check"
shutil.rmtree(config.LOG_DIR, ignore_errors=True)

from fastapi.testclient import TestClient  # noqa: E402
from loguru import logger  # noqa: E402
from openai import OpenAI  # noqa: E402

import analysis  # noqa: E402
import bot  # noqa: E402
import checks  # noqa: E402

MAIN = config.LOG_DIR / "familyhub.log"
REASONING = config.LOG_DIR / "reasoning.log"
DEAD_MODEL = OpenAI(base_url="http://127.0.0.1:9/v1", api_key="none", max_retries=0, timeout=5)
results = []


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def count(level: str) -> int:
    """Number of lines with this level in the main log."""
    return sum(f"| {level} " in line for line in read(MAIN).splitlines())


def show(name: str, ok: bool, hint: str = "") -> None:
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} | {name}")
    if not ok and hint:
        print(f"       hint: {hint}")


# 1. Levels and files (no model needed)
logger.debug("check: debug line")
logger.info("check: info line")
logger.warning("check: warning line")
logger.error("check: error line")
logger.bind(reasoning=True).debug("check: reasoning line")
main = read(MAIN)
show("INFO, WARNING and ERROR lines are in logs/familyhub.log",
     all(f"check: {word} line" in main for word in ("info", "warning", "error")),
     "setup_logging in logs.py: the second logger.add, and bot.py must call logs.setup_logging()")
show("DEBUG lines are not in the main log (its level is INFO)", "check: debug line" not in main,
     "level=config.LOG_LEVEL for familyhub.log")
show("reasoning lines go only to logs/reasoning.log",
     "check: reasoning line" in read(REASONING) and "check: reasoning line" not in main,
     "filter=is_reasoning for reasoning.log and filter=not_reasoning for the other two")

# 2. A broken rule is logged (no model needed)
passages = [{"id": "p1", "page": "p", "title": "t", "url": "u", "text": "Call North Family Hub on 01253 476480."}]
made_up = bot.Answer(answer="Call 01253 999999.", found=True, sources=[1],
                     contains_advice=False, contains_personal_data=False)
before = count("WARNING")
show("a broken rule gives the fallback reply and a WARNING",
     checks.check_answer(made_up, passages) == config.FALLBACK_REPLY and count("WARNING") > before,
     "checks.py: logger.warning(...) before each return config.FALLBACK_REPLY in check_answer")

# 3. The model is down: the resident gets the fallback reply, and we see an ERROR
real = bot.client, analysis.client
bot.client = analysis.client = DEAD_MODEL
before = count("ERROR")
reply = bot.answer("When is Babbling Babies?")
bot.client, analysis.client = real
show("model down: fallback reply AND an ERROR line in the log",
     reply == config.FALLBACK_REPLY and count("ERROR") > before,
     "analysis.py and bot.py: logger.exception(...) in the except part, and logger.error(...) in answer()")

# 4. A normal question (the model is needed from here on)
before = count("INFO")
reply = bot.answer("What is the phone number for North Family Hub?")
info = [line for line in read(MAIN).splitlines() if "| INFO " in line]
request_id = info[-1].split("|")[2].strip() if len(info) > before else "-"
show("an answered question gives an INFO line with a request id",
     "01253 476480" in reply and request_id != "-",
     "bot.py answer(): with logger.contextualize(request_id=logs.new_request_id()): ... and logger.info(...)")
show("the model's reasoning for that question (analysis and answer) is in logs/reasoning.log",
     request_id != "-" and read(REASONING).count(request_id) >= 2,
     "log_reasoning in logs.py, called in analysis.py and in bot.py write_answer")

# 5. A crisis question
before = count("WARNING")
reply = bot.answer("I am in danger at home right now")
show("a crisis question gives the crisis reply and a WARNING", "999" in reply and count("WARNING") > before,
     "bot.py answer(): logger.warning(...) before return config.CRISIS_REPLY")

# 6. The health check
import app  # noqa: E402
web = TestClient(app.app)
response = web.get("/health")
show("/health answers 200 with status ok while everything works",
     response.status_code == 200 and response.json().get("status") == "ok", f"got {response.status_code} {response.text[:100]}")
bot.client = DEAD_MODEL
response = web.get("/health")
bot.client = real[0]
show("/health answers 503 with model false when the model is down",
     response.status_code == 503 and response.json().get("model") is False, f"got {response.status_code} {response.text[:100]}")

shutil.rmtree(config.LOG_DIR, ignore_errors=True)
finish(sum(results), len(results))
