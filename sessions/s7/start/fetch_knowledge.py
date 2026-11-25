"""Download our knowledge from the council website, from zero.

Run from your main folder:  python fetch_knowledge.py   (about one minute)

Starts at the Blackpool family hubs page, follows every link inside the family hubs section and the
SEND Local Offer, and saves the main text of each page as markdown in knowledge/ (one file per page:
'# Title', 'URL: ...', an empty line, the text). The timetable pages come from timetable.py.
The previous knowledge/ is kept as knowledge.previous/. Afterwards: python search.py --build
"""
import re
import shutil
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
import trafilatura

import config
import timetable

START = ("https://www.blackpool.gov.uk/residents/education-and-schools/early-years-and-childcare/"
         "family-hubs-and-best-start-for-life/family-hubs/blackpool-family-hubs")
EXTRA_PAGES = [
    "https://www.blackpool.gov.uk/residents/education-and-schools/early-years-and-childcare/"
    "family-hubs-and-best-start-for-life/family-hubs-and-best-start-in-life",
    "https://www.blackpool.gov.uk/Residents/Life-events/Register-a-birth/Register-a-birth.aspx",
    "https://www.blackpool.gov.uk/Residents/Education-and-schools/Local-offer/Local-offer-home.aspx",
]
# Path prefixes (lower case) the crawler follows
SECTIONS = [
    "/residents/education-and-schools/early-years-and-childcare/family-hubs-and-best-start-for-life/family-hubs/",
    "/residents/education-and-schools/early-years-and-childcare/family-hubs-and-start-for-life/family-hubs/",
    "/residents/education-and-schools/local-offer/",
]
SKIP_EXTENSIONS = (".css", ".js", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".png", ".zip")
MAX_PAGES = 400
# Stable file names for pages whose address does not match their name (the golden questions use these names)
PAGE_IDS = {
    "family-hubs-and-best-start-in-life": "family-hubs-and-start-for-life",
    "parent-voice-and-volunteering": "parent-and-carer-panels",
    "local-offer/professionals/graduated-approach/physical-and-medical/sensory-processing-difficulties":
        "sensory-processing-difficulties-109",
}
TIMETABLE_PAGE = "family-hubs-timetable"
USER_AGENT = "Mozilla/5.0 (compatible; FamilyHubAssistant/1.0)"

client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30, follow_redirects=True)


# ---------------------------------------------------------------- ready: small helpers

def page_key(url: str) -> str:
    """The same page whatever the letter case or the .aspx ending."""
    parts = urlparse(url)
    return (parts.netloc.lower() + parts.path.lower().rstrip("/")).removesuffix(".aspx")


def in_sections(url: str) -> bool:
    parts = urlparse(url)
    path = parts.path.lower()
    return (parts.netloc.lower() == "www.blackpool.gov.uk" and any(path.startswith(s) for s in SECTIONS)
            and "/site/" not in path and not path.endswith(SKIP_EXTENSIONS))


def page_id(url: str) -> str:
    key = page_key(url)
    for ending, name in PAGE_IDS.items():
        if key.endswith(ending):
            return name
    return key.rsplit("/", 1)[-1]



# ---------------------------------------------------------------- you build

def main_text(html: str) -> str:
    """The main text of a page as markdown, without menus, header and footer ("" if there is none)."""
    raise NotImplementedError


def crawl() -> list[tuple[str, str]]:
    """Visit START and EXTRA_PAGES, then every linked page for which in_sections(link) is True.

    Each page only once (compare page_key). Follow redirects: keep the final address of each page.
    A page that fails to download is skipped with a printed line. At most MAX_PAGES pages.
    Returns a list of (final url, html).
    """
    raise NotImplementedError


def save_pages(pages: list[tuple[str, str]], folder) -> int:
    """Write one file per page to folder / f"{page_id(url)}.md" and return how many were saved.

    Skip the page TIMETABLE_PAGE (timetable.py builds it). File: f"# {title}\nURL: {url}\n\n{text}"
    The title comes from trafilatura.extract_metadata(html).title, without " - Blackpool Council".
    """
    raise NotImplementedError


def main():
    """Download into knowledge.new/, add the timetable pages, then swap:
    knowledge/ becomes knowledge.previous/ and knowledge.new/ becomes knowledge/."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
