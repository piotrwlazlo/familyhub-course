"""Nightly data refresh: download the council pages again, check them, build a new index and swap it in.

Run:    python refresh.py              (a few minutes: it downloads every page, the model is not needed)
        python refresh.py --rollback   (go back to the knowledge and index from before the last refresh)

The new data is built in staging/. The live knowledge/ and index/ change only when every check passes.
The previous version stays in backup/. After a refresh, restart the service to use the new data.
"""
import shutil
import sys

from loguru import logger

import config
import logs
import search
import sources


def download_all(staging) -> list[str]:
    """Download every page of the knowledge again into staging/knowledge. Returns the URLs that failed.

    Timetable pages are built from the timetable data, our own pages are copied, and a page that fails to
    download keeps its old copy.
    """
    new = staging / "knowledge"
    new.mkdir(parents=True)
    failed = []
    for path in sorted(config.KNOWLEDGE.glob("*.md")):
        page = search.read_page(path)          # page["page"], page["title"], page["url"]
        # TODO 1: skip the pages in config.TIMETABLE_PAGES; copy the pages in config.KEEP_PAGES;
        #         download all others with sources.download_text and write the file (see the task card).
        #         If a download fails: logger.warning(...), add the URL to failed, copy the old file.

    # Ready: the timetable (built from the council's timetable data)
    try:
        events = sources.download_timetable()
        sources.save_timetable(events, new)
    except Exception as error:
        logger.warning("timetable download failed, old copy kept | {}", error)
        failed.append(config.TIMETABLE_URL)
        for name in config.TIMETABLE_PAGES:
            shutil.copy(config.KNOWLEDGE / f"{name}.md", new / f"{name}.md")
        shutil.copy(config.KNOWLEDGE / "timetable.json", new / "timetable.json")
    return failed


def check_pages(staging, failed: list[str]) -> list[str]:
    """The quick rules for the new data. Returns the problems found (an empty list: all good)."""
    new = staging / "knowledge"
    problems = []
    # TODO 2: three rules, each adds one sentence to problems:
    #   - more than config.MAX_FAILED of the pages failed to download
    #   - family-hubs-timetable.md has fewer than config.MIN_ROWS sessions (sources.count_sessions)
    #   - timetable.json contains the text "sys" in quotes (staff data)
    return problems


def swap(staging) -> None:
    """Put the new knowledge and index live; keep the current ones in backup/."""
    # TODO 3: empty config.BACKUP_DIR; move knowledge/ and index/ into it; move staging/knowledge and
    #         staging/index to config.KNOWLEDGE and config.INDEX_DIR; delete staging.


def rollback() -> bool:
    """Swap the live knowledge and index with the ones in backup/. Running it twice brings the new ones back."""
    # TODO 4
    return False


def refresh() -> bool:
    """Download, check, build, test with the golden questions, swap. True if the new data is live."""
    staging = config.STAGING_DIR
    shutil.rmtree(staging, ignore_errors=True)
    logger.info("refresh started")
    # TODO 5: download_all, check_pages (problems: logger.error and return False),
    #         sources.build_index and sources.search_score on staging/knowledge and staging/index
    #         (score below config.MIN_SEARCH_SCORE: logger.error that names the golden questions, return False),
    #         swap, logger.info with the score, return True.
    return False


if __name__ == "__main__":
    logs.setup_logging()
    ok = rollback() if sys.argv[1:] == ["--rollback"] else refresh()
    sys.exit(0 if ok else 1)
