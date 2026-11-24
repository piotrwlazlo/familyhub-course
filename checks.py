"""Session 4: our own rules check every answer before anyone sees it.

The model is asked to follow the rules, but these checks are plain Python: they always work the same way.
"""
import re

import config

# Words that mean someone may be in danger right now. Then we always give our fixed crisis reply.
CRISIS_WORDS = ["in danger", "not safe at home", "unsafe at home", "hurt myself", "kill myself", "suicide",
                "hitting me", "hits me", "being abused", "abusing me", "going to hurt"]

# UK phone numbers like 01253 476480, 0808 2000 247, 0300 456 4000, 116 123
PHONE = re.compile(r"\b(?:0\d{2,4}[ -]?\d{3,4}[ -]?\d{3,4}|116 ?\d{3})\b")


def is_crisis(question: str) -> bool:
    """True if the question contains one of the crisis words."""
    text = question.lower().replace("’", "'")
    return any(word in text for word in CRISIS_WORDS)


def digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def unknown_phone_numbers(answer: str, passages: list[dict]) -> list[str]:
    """Phone numbers in the answer that do not appear in any passage (the model may have made them up)."""
    known = digits(" ".join(p["text"] for p in passages))
    return [number for number in PHONE.findall(answer) if digits(number) not in known]


def check_answer(result, passages: list[dict]) -> str | None:
    """Return our fallback reply if the answer breaks a rule, or None if the answer is fine."""
    if not result.found or not result.answer.strip():
        return config.FALLBACK_REPLY          # the passages do not have the answer
    if not result.sources:
        return config.FALLBACK_REPLY          # an answer must say where it comes from
    if result.contains_advice or result.contains_personal_data:
        return config.FALLBACK_REPLY          # the model itself says the answer breaks a rule
    if unknown_phone_numbers(result.answer, passages):
        return config.FALLBACK_REPLY          # a phone number that is not on our pages
    return None
