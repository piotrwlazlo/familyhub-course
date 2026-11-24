"""Family Hub assistant: a question goes in, an answer comes out.

Try it:  python bot.py "What is the phone number for North Family Hub?"
"""
import sys
from datetime import date

from openai import OpenAI

import config

client = OpenAI(base_url=config.MODEL_URL, api_key="not-needed")

RULES = """You are the Family Hub information assistant of the council.
Today is {today}.

Rules:
- Answer ONLY with information from the DOCUMENTS below. Do not use anything else you know.
- If the documents do not contain the answer, say so and suggest contacting the local family hub.
- Do not give medical, legal, financial or parenting advice. Only say what the documents say.
- Never ask for personal data.
- For activities, use today's date: only mention sessions that have not ended yet, and give exact dates when asked "when".
- Answer in British English, briefly and professionally.

DOCUMENTS:
{documents}"""


def today() -> date:
    return config.TODAY or date.today()


def load_knowledge(names: list[str]) -> list[dict]:
    """Read the given files from the knowledge folder.
    Return a list like [{"name": "hub-contacts.md", "text": "..."}, ...]"""
    # TODO
    return []


def build_prompt(docs: list[dict], day: date) -> str:
    """Return RULES filled in with today's date (like "Sunday 22 November 2026")
    and all documents, each one starting with a line "=== <name> ===". """
    # TODO
    return ""


DOCS = load_knowledge(config.SMALL_KNOWLEDGE)


def answer(question: str) -> str:
    """Ask the model one question, with all our documents in the system message. Return the reply text."""
    # TODO
    return ""


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the phone number for North Family Hub?"
    print(answer(question))
