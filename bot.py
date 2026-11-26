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
from checks import check_answer, is_about_abuse, is_crisis
from search import search

client = OpenAI(base_url=config.MODEL_URL, api_key="not-needed")
logs.setup_logging()

RULES = """You are the Family Hub information assistant of Blackpool Council.
Today is {today}.

Rules:
- Answer ONLY with the FAMILY HUB INFORMATION below. Do not use anything else you know.
- If nothing in the FAMILY HUB INFORMATION helps the person, set found to false.
- When someone asks for help, list every service that fits them, with who it is for and how to contact it. For 'me/I' questions assume an adult unless they say otherwise.
- Do not give medical, legal, financial or parenting advice. Only say what the Family Hub information says.
- Never ask for personal data.
- For activities, use today's date: only mention sessions that have not ended yet, and give exact dates when asked "when".
- When you give the time of a session, also give the day and the place.
- For today/day questions use only rows whose day is that weekday and whose dates include that date; list ALL such rows for the asked hub.
- Never list more than 10 sessions. If the question asks for the whole timetable or would match more than
  10 sessions, do not list them, even if the user asks for everything or says not to summarise. Instead, in a
  few lines, name the venues and the main kinds of activities, ask the user to narrow the question by family
  hub, day or child's age, and give the link to the full timetable: {timetable}
  Then set found to true and give the timetable passage in sources.
- The message may ask about several things. Answer every part, each in its own short paragraph or bullet.
- If the Family Hub information answers only some parts, answer those and say briefly which part you could not find information about.
- Answer in British English, briefly and professionally.
- Speak directly to the person. Never mention "passages", "context", "documents", "the text", "the information provided" or anything similar, and never write numbers like [1] in the answer. The person cannot see this material; links to the pages are added under your answer automatically. If you need to refer to it, say "the Family Hub pages", for example "I found this information on the Family Hub pages" or "I couldn't find that on the Family Hub pages".

Reply with JSON that matches this schema:
{schema}

FAMILY HUB INFORMATION (the numbers in brackets are only for the sources field):
{passages}"""


class Answer(BaseModel):
    answer: str = Field(description="Answer in British English, spoken directly to the person and based ONLY on the "
                                    "Family Hub information. When the person asks for help or support, list EVERY "
                                    "service in the Family Hub information that fits the person: name, who it is for, "
                                    "and phone number or website. Never reply with a general sentence that names no "
                                    "service. Leave out guidance written for schools or professionals. "
                                    "Leave out services whose age range clearly does not fit the person (for 'me/I' "
                                    "questions assume an adult unless they say otherwise), for example a service for "
                                    "11 to 18 year olds. For questions about today or a given day use only timetable rows whose day is "
                                    "that weekday and whose dates include that date; list ALL such rows for the hub "
                                    "asked about. Never mention passages, context or numbers like [1].")
    found: bool = Field(description="True when the Family Hub information contains at least one service, helpline or "
                                    "partial answer that helps the person, also when it answers only one part of the "
                                    "question. Also true for a short timetable overview that asks the user to narrow "
                                    "the question. False only when nothing relevant is there.")
    sources: list[int] = Field(description="Numbers of the extracts used for the answer, for example [1, 3]. "
                                          "Numbers go only here, never in answer.")
    contains_advice: bool = Field(description="True if the answer gives medical, legal, financial or parenting "
                                              "advice that is not written in the Family Hub information.")
    contains_personal_data: bool = Field(description="True if the answer contains personal data of a private "
                                                     "person (public phone numbers and emails of services are fine).")


def today() -> date:
    return config.TODAY or date.today()


def sessions_on(day: date) -> str:
    """List the timetable sessions running on the given day (weekday and date range), all hubs."""
    rows = json.loads((config.KNOWLEDGE / "timetable.json").read_text(encoding="utf-8"))
    lines = []
    for row in rows:
        start, end = date.fromisoformat(row["startDate"][:10]), date.fromisoformat(row["endDate"][:10])
        if f"{day:%A}" in (row["day"] or []) and start <= day <= end:
            lines.append(f"- {row['title']} | {row['entry']['venue']} | {row['familyHub']}")
    return f"Sessions running today ({day:%A %d %B %Y}):\n" + ("\n".join(sorted(lines)) or "- none")


def build_prompt(passages: list[dict], day: date, questions: list[str] | None = None) -> str:
    """Build the system prompt: rules, current date, answer schema, numbered passages and the questions to answer.

    The timetable page starts with the list of today's sessions, worked out from the timetable data.
    """
    texts = [f"{sessions_on(day)}\n\n{p['text']}" if p["id"] in config.WHOLE_PAGES else p["text"] for p in passages]
    numbered = "\n\n".join(f"[{i}] {text}" for i, text in enumerate(texts, start=1))
    prompt = RULES.format(today=f"{day:%A %d %B %Y}", timetable=config.HUBS_PAGE,
                          schema=json.dumps(Answer.model_json_schema()), passages=numbered)
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
    """Format a deduplicated list of source links for the passages referenced by the answer.

    Several pages can share one URL; the link keeps the title of the page the URL belongs to,
    otherwise the title of the first passage with that URL.
    """
    links = {}
    for number in used:
        if 1 <= number <= len(passages):
            page = passages[number - 1]
            owns_url = page["page"] in page["url"].lower()
            if page["url"] not in links or owns_url:
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
        abuse = config.CRISIS_NARROW and is_about_abuse(question + " " + " ".join(queries))
        passages = gather(queries)
        result = write_answer(question, passages, history, queries)
        if result is None:
            logger.error("no answer from the model: fallback reply sent")
            return config.CRISIS_REPLY if abuse else config.FALLBACK_REPLY
        problem = check_answer(result, passages)
        if problem:
            return config.CRISIS_REPLY if abuse else problem   # check_answer has logged which rule
        logger.info("answered | kind={} | pages={} | {:.1f} s", form.kind,
                    [passages[n - 1]["page"] for n in result.sources if 1 <= n <= len(passages)],
                    time.perf_counter() - started)
        reply = result.answer + source_links(passages, result.sources)
        return config.ABUSE_LINE + "\n\n" + reply if abuse else reply


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the phone number for North Family Hub?"
    print(answer(question))
