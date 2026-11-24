"""Session 8 check: the Pipe answers follow-up questions in a conversation, like Open WebUI will use it.

Run from the familyhub-app folder:  python sessions/s8/check.py
(This runs the Pipe here, outside Open WebUI. Then paste familyhub_pipe.py into Open WebUI and try it there.)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder

from common import APP, finish, has_any  # noqa: E402  (also sets up the paths and the fixed date)

import config  # noqa: E402
from familyhub_pipe import Pipe  # noqa: E402

pipe = Pipe()
pipe.valves.APP_DIR = str(APP)
pipe.valves.MODEL_URL = config.MODEL_URL

# Each conversation: (question, phrases the answer must contain: one of each group)
CONVERSATIONS = [
    [("When is Babbling Babies at North Family Hub?", [["Thursday"]]),
     ("And at South Family Hub?",                      [["Friday"], ["10am", "10 am", "10.00"]])],
    [("What is the phone number for North Family Hub?", [["01253 476480"]]),
     ("And what is their address?",                     [["Dingle Avenue"]])],
    [("How long do I have to register a birth?",       [["42 days"]]),
     ("How much does a birth certificate cost?",       [["12.50"]])],
]

passed = total = 0
for conversation in CONVERSATIONS:
    messages = []
    for turn, (question, must) in enumerate(conversation):
        messages.append({"role": "user", "content": question})
        reply = pipe.pipe({"messages": messages})
        messages.append({"role": "assistant", "content": reply})
        missing = [group[0] for group in must if not has_any(reply, group)]
        notice_ok = (turn == 0) == reply.startswith(config.HELP_NOTICE)   # the notice only above the first answer
        ok = not missing and notice_ok
        passed += ok
        total += 1
        print(f"{'PASS' if ok else 'FAIL'} | {question}")
        if not ok:
            print(f"       missing: {missing or '-'}  notice in the right place: {notice_ok}\n       answer: {reply[:300]!r}")
    print()

title_ok = pipe.pipe({"messages": [{"role": "user", "content": "Create a title"}]}, __task__="title_generation") == "Family Hub question"
print(f"{'PASS' if title_ok else 'FAIL'} | Open WebUI tasks (chat title) get a short fixed reply")
finish(passed + title_ok, total + 1)
