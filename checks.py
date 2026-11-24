"""Deterministic validation of questions and generated answers."""
import re

import config

# Phrases that trigger the fixed crisis reply
CRISIS_WORDS = ["in danger", "not safe at home", "unsafe at home", "hurt myself", "kill myself", "suicide",
                "hitting me", "hits me", "being abused", "abusing me", "going to hurt"]

# UK phone numbers, e.g. 01253 476480, 0808 2000 247, 116 123
PHONE = re.compile(r"\b(?:0\d{2,4}[ -]?\d{3,4}[ -]?\d{3,4}|116 ?\d{3})\b")


def is_crisis(question: str) -> bool:
    """True if the question contains one of the crisis words."""
    text = question.lower().replace("’", "'")
    return any(word in text for word in CRISIS_WORDS)


def digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def unknown_phone_numbers(answer: str, passages: list[dict]) -> list[str]:
    """Return phone numbers in the answer that do not appear in any passage."""
    known = digits(" ".join(p["text"] for p in passages))
    return [number for number in PHONE.findall(answer) if digits(number) not in known]


def check_answer(result, passages: list[dict]) -> str | None:
    """Return the fallback reply if the answer fails validation, otherwise None."""
    if not result.found or not result.answer.strip():
        return config.FALLBACK_REPLY          # not found in the passages
    if not result.sources:
        return config.FALLBACK_REPLY          # no sources
    if result.contains_advice or result.contains_personal_data:
        return config.FALLBACK_REPLY          # flagged as advice or personal data
    if unknown_phone_numbers(result.answer, passages):
        return config.FALLBACK_REPLY          # unverified phone number
    return None
