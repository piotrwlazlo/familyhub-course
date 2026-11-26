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
         "family-hubs-and-best-start-for-life/")
EXTRA_PAGES = [
    "https://www.blackpool.gov.uk/residents/education-and-schools/early-years-and-childcare/"
    "family-hubs-and-best-start-for-life/family-hubs-and-best-start-in-life",
    "https://www.blackpool.gov.uk/Residents/Life-events/Register-a-birth/Register-a-birth.aspx",
    "https://www.blackpool.gov.uk/Residents/Education-and-schools/Local-offer/Local-offer-home.aspx",
]
# Path prefixes (lower case) the crawler follows
SECTIONS = [
    "/residents/education-and-schools/early-years-and-childcare/family-hubs-and-best-start-for-life/",
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



# ---------------------------------------------------------------- pages

def main_text(html: str) -> str:
    """The main text of a page as markdown, without menus, header and footer.

    The council pages use GOV.UK accordions (expandable sections). trafilatura treats every section after
    the first one as page furniture and drops it, so the accordion classes are removed first.
    """
    html = re.sub(r'class="govuk-(accordion|tabs|details)[^"]*"', "", html)
    return trafilatura.extract(html, output_format="markdown", include_tables=True, include_links=True) or ""


def crawl() -> list[tuple[str, str]]:
    """Visit the start pages and every linked page inside SECTIONS. Returns (final url, html) per page."""
    queue, seen, pages = [START] + EXTRA_PAGES, set(), []
    while queue and len(pages) < MAX_PAGES:
        url = queue.pop(0)
        if page_key(url) in seen:
            continue
        seen.add(page_key(url))
        try:
            response = client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as error:
            print(f"skipped {url}: {error}")
            continue
        final = str(response.url)
        if page_key(final) != page_key(url):
            if page_key(final) in seen:
                continue
            seen.add(page_key(final))
        pages.append((final, response.text))
        for href in re.findall(r'href="([^"]+)"', response.text):
            link = urldefrag(urljoin(final, href.replace("&amp;", "&"))).url
            if in_sections(link):
                queue.append(link)
    return pages


def save_pages(pages: list[tuple[str, str]], folder) -> int:
    saved = set()
    for url, html in pages:
        name = page_id(url)
        if name == TIMETABLE_PAGE:            # built from the timetable data instead
            continue
        if name in saved:
            name = f"{name}-{len(saved)}"
        text = main_text(html)
        if not text:
            print(f"no main text: {url}")
            continue
        meta = trafilatura.extract_metadata(html)
        title = (meta.title if meta and meta.title else name).split(" - Blackpool Council")[0].strip()
        (folder / f"{name}.md").write_text(f"# {title}\nURL: {url}\n\n{text}", encoding="utf-8")
        saved.add(name)
    return len(saved)


def main():
    """Download into knowledge.new/, add the timetable pages, then swap:
    knowledge/ becomes knowledge.previous/ and knowledge.new/ becomes knowledge/."""
    new = config.HERE / "knowledge.new"
    shutil.rmtree(new, ignore_errors=True)
    new.mkdir()
    count = save_pages(crawl(), new)
    timetable.save_timetable_pages(new)
    previous = config.HERE / "knowledge.previous"
    if config.KNOWLEDGE.exists():
        shutil.rmtree(previous, ignore_errors=True)
        config.KNOWLEDGE.rename(previous)
    new.rename(config.KNOWLEDGE)
    print(f"{count} pages and the timetable saved to {config.KNOWLEDGE}")
    print("Next: python search.py --build")


if __name__ == "__main__":
    main()
