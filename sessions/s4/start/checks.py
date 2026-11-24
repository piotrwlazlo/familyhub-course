"""Session 4: our own rules check every answer before anyone sees it.

The model is asked to follow the rules, but these checks are plain Python: they always work the same way.
"""
import re

import config

# Words that mean someone may be in danger right now. Then we always give our fixed crisis reply.
CRISIS_WORDS = ["in danger"]   # TODO: add more (think of how people really write it)

# UK phone numbers like 01253 476480, 0808 2000 247, 0300 456 4000, 116 123
PHONE = re.compile(r"\b(?:0\d{2,4}[ -]?\d{3,4}[ -]?\d{3,4}|116 ?\d{3})\b")


def is_crisis(question: str) -> bool:
    """True if the question contains one of the crisis words (compare in lower case)."""
    # TODO
    return False


def digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def unknown_phone_numbers(answer: str, passages: list[dict]) -> list[str]:
    """Phone numbers in the answer (PHONE.findall) that do not appear in any passage.
    Compare digits only, so "01253 476 480" and "01253476480" are the same number."""
    # TODO
    return []


def check_answer(result, passages: list[dict]) -> str | None:
    """Return config.FALLBACK_REPLY if the answer breaks a rule, or None if the answer is fine.
    Rules: the answer was found and is not empty; it has sources; the model did not mark it as advice
    or personal data; it has no unknown phone numbers."""
    # TODO
    return None
