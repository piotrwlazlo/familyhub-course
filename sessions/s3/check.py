"""Session 3 check: the assistant answers from our documents and knows today's date.

Run from the familyhub-app folder:  python sessions/s3/check.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder

from common import check_answers  # noqa: E402  (also sets up the paths and the fixed date)

import bot  # noqa: E402

CASES = [
    # question                                                       must contain (one of each group)             must not contain
    ("What is the phone number for North Family Hub?",               [["01253 476480"]],                           []),
    ("What is the address of South Family Hub?",                     [["St Anne's Road"]],                         []),
    ("What time is Babbling Babies at Revoe Children's Centre?",     [["1pm", "1 pm", "13:00"], ["Thursday"]],     []),
    ("When is the next cost of living advice drop-in?",              [["25 Nov", "25th Nov", "November 25"], ["South"]], []),
    ("How long do I have to register a birth?",                      [["42 days"]],                                []),
    ("How long is the Triple P for baby course?",                    [["nine", "9"]],                              []),
]

if __name__ == "__main__":
    check_answers(CASES, bot.answer)
