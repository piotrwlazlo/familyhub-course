"""Session 9: where the knowledge comes from. Ready to use: you do not need to change this file.

download_text(url)          the main text of one council web page, as markdown
download_timetable()        the family hub sessions from the council's timetable data (JSON)
save_timetable(events, folder)   timetable.json without staff data, and the two timetable pages
count_sessions(text)        how many sessions the timetable page lists
build_index(knowledge, index)    build a search index from a knowledge folder (like python search.py --build)
search_score(knowledge, index)   share of golden questions whose right page is found (like the session 3 check)
"""
import contextlib
import importlib
import io
import json
import re
from collections import defaultdict
from datetime import date

import httpx
import trafilatura

import config
import search

USER_AGENT = "Mozilla/5.0 (compatible; FamilyHubAssistant/1.0)"
GOLDEN = config.HERE / "sessions" / "golden_questions.json"


def download_text(url: str) -> str:
    """Download a page and keep only its main text (no menus, header or footer)."""
    response = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)
    response.raise_for_status()
    text = trafilatura.extract(response.text, output_format="markdown", include_tables=True, include_links=True)
    if not text:
        raise ValueError("no main text on the page")
    return text


@contextlib.contextmanager
def use_data(knowledge, index):
    """Point the search at another knowledge folder and index for a moment."""
    saved = config.KNOWLEDGE, config.INDEX_DIR
    config.KNOWLEDGE, config.INDEX_DIR = knowledge, index
    try:
        yield
    finally:
        config.KNOWLEDGE, config.INDEX_DIR = saved


def build_index(knowledge, index) -> None:
    with use_data(knowledge, index), contextlib.redirect_stdout(io.StringIO()):
        search.build_index()


def search_score(knowledge, index) -> float:
    questions = json.loads(GOLDEN.read_text(encoding="utf-8"))
    questions = [q for q in questions if q["expected_pages"] and q["expect"] == "answer"]
    with use_data(knowledge, index):
        importlib.reload(search)
        hits = sum(bool(set(q["expected_pages"]) & {hit["page"] for hit in search.search(q["question"])})
                   for q in questions)
    importlib.reload(search)          # back to the live index
    return hits / len(questions)


# ---------------------------------------------------------------- the timetable

# The timetable on the council page is filled by JavaScript from this JSON list (one item per session)
HUBS_URL = config.HUBS_PAGE
# Hub contacts come from the council page (the JSON has different phone numbers for South and Revoe)
HUB_CONTACTS = """| Centre | Address | Telephone number |
|---|---|---|
| Central Family Hub \\[formerly Talbot and Brunswick\\] | Gorton Street, Blackpool FY1 3JW | 01253 951190 |
| North Family Hub \\[formerly Grange Park\\] | 31 Dingle Avenue, Blackpool FY3 7NX | 01253 476480 |
| South Family Hub \\[within Palatine Leisure Centre\\] | 207 St Anne's Road, Blackpool FY4 2AP | 01253 476550 |
| Revoe Children's Centre \\[exterior of Revoe Learning Academy\\] | Wyre Grove, Blackpool, FY1 5HP | 01253 798016 |"""
HUB_VENUES = {"Central Family Hub", "North Family Hub", "South Family Hub", "Revoe Children's Centre"}


def download_timetable() -> list[dict]:
    """All sessions of the council's timetable data, as they come (with the staff data in "sys")."""
    response = httpx.get(config.TIMETABLE_URL, headers={"User-Agent": USER_AGENT}, timeout=60,
                         follow_redirects=True)
    response.raise_for_status()
    events = response.json()
    if not isinstance(events, list):
        raise ValueError("the timetable data is not a list of sessions")
    return events


def without_staff_data(value):
    """The same data without every "sys" part (it holds the names of the staff who edited the entry)."""
    if isinstance(value, dict):
        return {key: without_staff_data(item) for key, item in value.items() if key != "sys"}
    if isinstance(value, list):
        return [without_staff_data(item) for item in value]
    return value


def clean(text) -> str:
    text = re.sub(r"\bwith with\b", "with", " ".join((text or "").split()))
    return text.replace("|", "/")


def nice_date(day: date) -> str:
    return f"{day:%a} {day.day} {day:%b %Y}"           # Tue 24 Nov 2026


def sessions_from(events: list[dict], today: date) -> list[dict]:
    """One row per session that has not ended, sorted by activity, start date and venue."""
    sessions = []
    for item in events:
        entry, info = item.get("entry") or {}, item.get("moreInformation") or {}
        start = date.fromisoformat(item["startDate"][:10])
        end = date.fromisoformat(item["endDate"][:10])
        if end < today:
            continue
        if start == end:      # one-off session: the weekday comes from the date (day[] is wrong in a few rows)
            days, dates = f"{start:%A}", nice_date(start)
        else:                 # repeating session: day[] says on which weekdays
            days = ", ".join(item.get("day") or [])
            dates = f"every {days}, {start.day} {start:%b} – {nice_date(end)[4:]}"
        time = clean(item.get("familyHub"))
        sessions.append({
            "title": clean(item["title"]),
            "venue": clean(entry.get("venue")),
            "address": ", ".join(p for p in (clean(entry.get("address")), clean(entry.get("postCode"))) if p),
            "days": days,
            "time": time if "to" in time else f"starts {time}",
            "dates": dates,
            "start": start,
            "term_time_only": "Yes" if "Yes" in (item.get("termTimeOnly") or []) else "No",
            "booking": clean(item.get("booking")) or "–",
            "description": (info.get("longText") or "").strip(),
        })
    sessions.sort(key=lambda s: (s["title"].lower(), s["start"], s["venue"]))
    return sessions


def as_of_line(today: date) -> str:
    return f"Timetable valid as of {today:%d %B %Y}. Sessions that have already ended are not listed."


def timetable_page(sessions: list[dict], today: date) -> str:
    other = sorted({(s["venue"], s["address"]) for s in sessions if s["venue"] not in HUB_VENUES})
    rows = "\n".join(f"| {s['title']} | {s['venue']} | {s['days']} | {s['time']} | {s['dates']} | "
                     f"{s['term_time_only']} | {s['booking']} |" for s in sessions)
    other_text = ("Other venues: " + "; ".join(f"{v} ({a})" for v, a in other) + ".\n\n") if other else ""
    return ("# Family hub locations and timetable\n"
            f"URL: {HUBS_URL}\n\n"
            f"## Family hub locations\n\n{HUB_CONTACTS}\n\n{other_text}"
            "## Activities timetable\n\n"
            "We have put together a timetable of activities, sessions and events for families across our "
            "three Blackpool family hubs and other shared spaces. This timetable covers the north, central "
            "and south areas of Blackpool.\n"
            f"{as_of_line(today)} For a description of each activity see the page "
            "\"Family hub activities and what they offer\".\n\n"
            "| Activity | Venue | Day | Time | Dates | Term time only | Booking |\n"
            "|---|---|---|---|---|---|---|\n"
            f"{rows}\n")


def activities_page(sessions: list[dict], today: date) -> str:
    by_title = defaultdict(list)
    for s in sessions:
        by_title[s["title"]].append(s)
    parts = []
    for title, group in by_title.items():
        description = next((s["description"] for s in group if s["description"]), "")
        about = description or "No description is available. Please contact the family hub for details."
        slots = defaultdict(list)                    # one "where and when" line per venue + time
        for s in group:
            slots[(s["venue"], s["time"])].append(s)
        lines = []
        for (venue, time), slot in slots.items():
            if len(slot) == 1:
                when = slot[0]["dates"]
            else:
                when = f"{slot[0]['days']}: " + ", ".join(f"{x['start'].day} {x['start']:%b}" for x in slot)
            extra = " (term time only)" if slot[0]["term_time_only"] == "Yes" else ""
            booking = f", booking: {slot[0]['booking']}" if slot[0]["booking"] != "–" else ""
            lines.append(f"- {venue}, {time}, {when}{extra}{booking}")
        parts.append(f"## {title}\n\n{about}\n\nWhere and when:\n" + "\n".join(lines))
    return ("# Family hub activities and what they offer\n"
            f"URL: {HUBS_URL}\n\n"
            "Free activities, groups and drop-ins at Blackpool family hubs. "
            f"{as_of_line(today)} Addresses and phone numbers of the hubs are on the page "
            "\"Family hub locations and timetable\".\n\n" + "\n\n".join(parts) + "\n")


def save_timetable(events: list[dict], folder) -> None:
    """Write timetable.json (without staff data) and the two timetable pages into folder."""
    today = config.TODAY or date.today()
    events = without_staff_data(events)
    (folder / "timetable.json").write_text(json.dumps(events, indent=1, ensure_ascii=False), encoding="utf-8")
    sessions = sessions_from(events, today)
    (folder / "family-hubs-timetable.md").write_text(timetable_page(sessions, today), encoding="utf-8")
    (folder / "family-hubs-activities.md").write_text(activities_page(sessions, today), encoding="utf-8")


def count_sessions(text: str) -> int:
    """The number of sessions in the table of family-hubs-timetable.md."""
    table = text.split("| Activity | Venue |", 1)[-1] if "| Activity | Venue |" in text else ""
    return sum(1 for line in table.splitlines() if line.startswith("| "))
