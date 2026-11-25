"""Answer pipeline: question analysis, retrieval, answer generation and validation.

Usage: python bot.py "What is the phone number for North Family Hub?"
"""
import json
import sys
import time
from datetime import date

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, Field

import config
import logs
from analysis import analyse
from checks import check_answer, is_crisis
from search import search

client = OpenAI(base_url=config.MODEL_URL, api_key="not-needed")
logs.setup_logging()

RULES = """You are the Family Hub information assistant of Blackpool Council.
Today is {today}.

Rules:
- Answer ONLY with information from the PASSAGES below. Do not use anything else you know.
- If the passages do not contain the answer, set found to false.
- Do not give medical, legal, financial or parenting advice. Only say what the passages say.
- Never ask for personal data.
- For activities, use today's date: only mention sessions that have not ended yet, and give exact dates when asked "when".
- When you give the time of a session, also give the day and the place.
- The message may ask about several things. Answer every part, each in its own short paragraph or bullet.
- If the passages answer only some parts, answer those and say briefly which part you could not find information about.
- Answer in British English, briefly and professionally.

Reply with JSON that matches this schema:
{schema}

PASSAGES:
{passages}"""


class Answer(BaseModel):
    answer: str = Field(description="Short answer in British English, based ONLY on the passages.")
    found: bool = Field(description="True if the passages answer at least one part of the question.")
    sources: list[int] = Field(description="Numbers of the passages used for the answer, for example [1, 3].")
    contains_advice: bool = Field(description="True if the answer gives medical, legal, financial or parenting "
                                              "advice that is not written in the passages.")
    contains_personal_data: bool = Field(description="True if the answer contains personal data of a private "
                                                     "person (public phone numbers and emails of services are fine).")


def today() -> date:
    return config.TODAY or date.today()


def build_prompt(passages: list[dict], day: date, questions: list[str] | None = None) -> str:
    """Build the system prompt: rules, current date, answer schema, numbered passages and the questions to answer."""
    numbered = "\n\n".join(f"[{i}] {p['text']}" for i, p in enumerate(passages, start=1))
    prompt = RULES.format(today=f"{day:%A %d %B %Y}", schema=json.dumps(Answer.model_json_schema()), passages=numbered)
    if questions and len(questions) > 1:
        prompt += "\n\nQUESTIONS TO ANSWER:\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, start=1))
    return prompt


def write_answer(question: str, passages: list[dict], history: list[dict] | None = None,
                 questions: list[str] | None = None) -> Answer | None:
    """Generate a structured answer from the passages and recent conversation. Returns None on failure."""
    messages = ([{"role": "system", "content": build_prompt(passages, today(), questions)}]
                + (history or [])[-6:] + [{"role": "user", "content": question}])
    try:
        response = client.chat.completions.parse(model=config.MODEL, messages=messages,
                                                 response_format=Answer, temperature=0)
        logs.log_reasoning("answer", response.choices[0].message)
        return response.choices[0].message.parsed
    except Exception:
        logger.exception("writing the answer failed: the model did not answer")
        return None


def gather(queries: list[str]) -> list[dict]:
    """Search every query and merge the hits round-robin, without duplicates, up to the limit in config.MAX_PASSAGES."""
    results = [search(query) for query in queries]
    passages, seen = [], set()
    for rank in range(max((len(hits) for hits in results), default=0)):
        for hits in results:
            if rank < len(hits) and (hits[rank]["page"], hits[rank]["text"]) not in seen:
                seen.add((hits[rank]["page"], hits[rank]["text"]))
                passages.append(hits[rank])
    return passages[:config.MAX_PASSAGES[len(queries)]]


def source_links(passages: list[dict], used: list[int]) -> str:
    """Format a deduplicated list of source links for the passages referenced by the answer."""
    links = {}
    for number in used:
        if 1 <= number <= len(passages):
            page = passages[number - 1]
            links[page["url"]] = f"- [{page['title']}]({page['url']})"
    return "\n\n**Sources:**\n" + "\n".join(links.values()) if links else ""


def answer(question: str, history: list[dict] | None = None) -> str:
    """Return the reply for a question.

    history: previous messages as [{"role": "user" | "assistant", "content": str}, ...]
    """
    with logger.contextualize(request_id=logs.new_request_id()):
        started = time.perf_counter()
        if is_crisis(question):                 # keyword check runs before any model call
            logger.warning("crisis words in the question: crisis reply sent")
            return config.CRISIS_REPLY
        form = analyse(question, history)
        if form is None:
            logger.error("no question analysis: fallback reply sent")
            return config.FALLBACK_REPLY
        if form.is_crisis:
            logger.warning("the model marked the question as a crisis: crisis reply sent")
            return config.CRISIS_REPLY
        if not form.on_topic:
            logger.info("off-topic question: off-topic reply sent")
            return config.OFF_TOPIC_REPLY
        queries = form.search_queries[:3] or [question]
        passages = gather(queries)
        result = write_answer(question, passages, history, queries)
        if result is None:
            logger.error("no answer from the model: fallback reply sent")
            return config.FALLBACK_REPLY
        problem = check_answer(result, passages)
        if problem:
            return problem                      # check_answer has logged which rule
        logger.info("answered | kind={} | pages={} | {:.1f} s", form.kind,
                    [passages[n - 1]["page"] for n in result.sources if 1 <= n <= len(passages)],
                    time.perf_counter() - started)
        return result.answer + source_links(passages, result.sources)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the phone number for North Family Hub?"
    print(answer(question))
