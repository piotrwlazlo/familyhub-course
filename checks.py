"""Deterministic validation of questions and generated answers."""
import re

from loguru import logger

import config

# Phrases that trigger the fixed crisis reply
CRISIS_WORDS = ["in danger", "not safe at home", "unsafe at home", "hurt myself", "kill myself", "suicide",
                "hitting me", "hits me", "being abused", "abusing me", "going to hurt"]
# With config.CRISIS_NARROW these go through normal search instead (answer starts with config.ABUSE_LINE)
ABUSE_WORDS = ["abuse", "abusive", "abusing", "violent", "violence", "controlling", "coercive"]

# UK phone numbers, e.g. 01253 476480, 0808 2000 247, 116 123
PHONE = re.compile(r"\b(?:0\d{2,4}[ -]?\d{3,4}[ -]?\d{3,4}|116 ?\d{3})\b")


def is_crisis(question: str) -> bool:
    """True if the question contains one of the crisis words."""
    text = question.lower().replace("’", "'")
    words = CRISIS_WORDS
    if config.CRISIS_NARROW:
        words = [w for w in CRISIS_WORDS if w not in ("being abused", "abusing me")]
    return any(word in text for word in words)


def is_about_abuse(text: str) -> bool:
    """True if the text mentions abuse or violence (used only with config.CRISIS_NARROW)."""
    text = text.lower()
    return any(word in text for word in ABUSE_WORDS)


def digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def unknown_phone_numbers(answer: str, passages: list[dict]) -> list[str]:
    """Return phone numbers in the answer that do not appear in any passage."""
    known = digits(" ".join(p["text"] for p in passages))
    return [number for number in PHONE.findall(answer) if digits(number) not in known]


def check_answer(result, passages: list[dict]) -> str | None:
    """Return the fallback reply if the answer fails validation, otherwise None."""
    if not result.found or not result.answer.strip():
        logger.warning("answer blocked: not found in the passages")
        return config.FALLBACK_REPLY
    if not result.sources and config.MEMBERSHIP_FORM not in result.answer:   # the membership form link needs no sources
        logger.warning("answer blocked: no sources")
        return config.FALLBACK_REPLY
    if result.contains_advice or result.contains_personal_data:
        logger.warning("answer blocked: marked as advice or personal data")
        return config.FALLBACK_REPLY
    unknown = unknown_phone_numbers(result.answer, passages)
    if unknown:
        logger.warning("answer blocked: unknown phone number {}", unknown)
        return config.FALLBACK_REPLY
    return None
