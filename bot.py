"""Family Hub assistant: a question goes in, an answer comes out.

Try it:  python bot.py "What is the phone number for North Family Hub?"
"""
import json
import sys
from datetime import date

from openai import OpenAI
from pydantic import BaseModel, Field

import config
from analysis import analyse
from search import search

client = OpenAI(base_url=config.MODEL_URL, api_key="not-needed")

RULES = """You are the Family Hub information assistant of Blackpool Council.
Today is {today}.

Rules:
- Answer ONLY with information from the PASSAGES below. Do not use anything else you know.
- If the passages do not contain the answer, set found to false.
- Do not give medical, legal, financial or parenting advice. Only say what the passages say.
- Never ask for personal data.
- For activities, use today's date: only mention sessions that have not ended yet, and give exact dates when asked "when".
- When you give the time of a session, also give the day and the place.
- Answer in British English, briefly and professionally.

Reply with JSON that matches this schema:
{schema}

PASSAGES:
{passages}"""


class Answer(BaseModel):
    answer: str = Field(description="Short answer in British English, based ONLY on the passages.")
    found: bool = Field(description="True if the passages contain the answer to the question.")
    sources: list[int] = Field(description="Numbers of the passages used for the answer, for example [1, 3].")


def today() -> date:
    return config.TODAY or date.today()


def build_prompt(passages: list[dict], day: date) -> str:
    """Our rules, today's date, the answer form and the numbered passages."""
    numbered = "\n\n".join(f"[{i}] {p['text']}" for i, p in enumerate(passages, start=1))
    return RULES.format(today=f"{day:%A %d %B %Y}", schema=json.dumps(Answer.model_json_schema()), passages=numbered)


def write_answer(question: str, passages: list[dict]) -> Answer | None:
    """The model reads the passages and fills in the Answer form."""
    messages = [{"role": "system", "content": build_prompt(passages, today())},
                {"role": "user", "content": question}]
    try:
        response = client.chat.completions.parse(model=config.MODEL, messages=messages,
                                                 response_format=Answer, temperature=0)
        return response.choices[0].message.parsed
    except Exception:
        return None


def source_links(passages: list[dict], used: list[int]) -> str:
    """Links to the pages of the passages the model used, each page once."""
    links = {}
    for number in used:
        if 1 <= number <= len(passages):
            page = passages[number - 1]
            links[page["url"]] = f"- [{page['title']}]({page['url']})"
    return "\n\n**Sources:**\n" + "\n".join(links.values()) if links else ""


def answer(question: str) -> str:
    """Understand the question, find passages, write the answer, add the sources."""
    form = analyse(question)
    if form is None:
        return config.FALLBACK_REPLY
    if form.is_crisis:
        return config.CRISIS_REPLY
    if not form.on_topic:
        return config.OFF_TOPIC_REPLY
    passages = search(form.search_query)
    result = write_answer(question, passages)
    if result is None or not result.found or not result.answer.strip():
        return config.FALLBACK_REPLY
    return result.answer + source_links(passages, result.sources)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the phone number for North Family Hub?"
    print(answer(question))
