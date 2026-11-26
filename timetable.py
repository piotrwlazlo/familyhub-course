"""The family hub timetable and the hub contacts page. Ready to use: you do not need to change this file.

save_timetable_pages(folder)   downloads the council's timetable data and writes into folder:
                               timetable.json (without staff data), family-hubs-timetable.md,
                               family-hubs-activities.md and hub-contacts.md
"""
import json
import re
from collections import defaultdict
from datetime import date

import httpx

import config

TIMETABLE_URL = "https://www.blackpool.gov.uk/custom/api/contenttype/entries/familyHubEvents"
HUBS_PAGE = ("https://www.blackpool.gov.uk/Residents/Education-and-schools/Early-years-and-childcare/"
             "Family-Hubs-and-Start-for-Life/Family-Hubs/Family-Hubs-timetable.aspx")
USER_AGENT = "Mozilla/5.0 (compatible; FamilyHubAssistant/1.0)"

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
    response = httpx.get(TIMETABLE_URL, headers={"User-Agent": USER_AGENT}, timeout=60,
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
            f"URL: {HUBS_PAGE}\n\n"
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
            f"URL: {HUBS_PAGE}\n\n"
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


# Our own page: the hub addresses and phone numbers in one small file (easy to find for the search)
HUB_CONTACTS_PAGE = """# Family hub contacts: addresses and phone numbers
URL: https://www.blackpool.gov.uk/Residents/Education-and-schools/Early-years-and-childcare/Family-Hubs-and-Start-for-Life/Family-Hubs/Family-Hubs-timetable.aspx

Addresses and telephone numbers of the Blackpool family hubs.

| Centre | Address | Telephone number |
|---|---|---|
| Central Family Hub [formerly Talbot and Brunswick] | Gorton Street, Blackpool FY1 3JW | 01253 951190 |
| North Family Hub [formerly Grange Park] | 31 Dingle Avenue, Blackpool FY3 7NX | 01253 476480 |
| South Family Hub [within Palatine Leisure Centre] | 207 St Anne's Road, Blackpool FY4 2AP | 01253 476550 |
| Revoe Children's Centre [exterior of Revoe Learning Academy] | Wyre Grove, Blackpool, FY1 5HP | 01253 798016 |

Other venues used for family hub activities: Blackpool and The Fylde College (Bispham), Ashfield Road, FY2 0HB; Stanley Park Visitor Centre, Stanley Park Close, FY3 9TR; Watson Road Park, Watson Road, FY4 4DA.
"""




def save_timetable_pages(folder) -> None:
    """Download the timetable and write the timetable pages and hub-contacts.md into folder."""
    save_timetable(download_timetable(), folder)
    (folder / "hub-contacts.md").write_text(HUB_CONTACTS_PAGE, encoding="utf-8")
