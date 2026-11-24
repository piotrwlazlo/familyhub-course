"""Family Hub assistant: a question goes in, an answer comes out.

Try it:  python bot.py "What is the phone number for North Family Hub?"
"""
import sys
from datetime import date

from openai import OpenAI

import config
from analysis import analyse

client = OpenAI(base_url=config.MODEL_URL, api_key="not-needed")

RULES = """You are the Family Hub information assistant of Blackpool Council.
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
    """Read the given files from the knowledge folder."""
    docs = []
    for name in names:
        text = (config.KNOWLEDGE / name).read_text(encoding="utf-8")
        docs.append({"name": name, "text": text})
    return docs


def build_prompt(docs: list[dict], day: date) -> str:
    """The instructions for the model: our rules, today's date and the documents."""
    documents = "\n\n".join(f"=== {doc['name']} ===\n{doc['text']}" for doc in docs)
    return RULES.format(today=f"{day:%A %d %B %Y}", documents=documents)


DOCS = load_knowledge(config.SMALL_KNOWLEDGE)


def ask_model(question: str) -> str:
    """Ask the model one question, with all our documents in the prompt."""
    messages = [
        {"role": "system", "content": build_prompt(DOCS, today())},
        {"role": "user", "content": question},
    ]
    response = client.chat.completions.create(model=config.MODEL, messages=messages, temperature=0)
    return response.choices[0].message.content


def answer(question: str) -> str:
    """Session 2: first understand the question, then decide what to do."""
    form = analyse(question)
    if form is None:
        return config.FALLBACK_REPLY
    if form.is_crisis:
        return config.CRISIS_REPLY
    if not form.on_topic:
        return config.OFF_TOPIC_REPLY
    return ask_model(question)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the phone number for North Family Hub?"
    print(answer(question))
