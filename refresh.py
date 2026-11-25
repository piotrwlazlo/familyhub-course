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
        page = search.read_page(path)
        if page["page"] in config.TIMETABLE_PAGES:
            continue
        if page["page"] in config.KEEP_PAGES:
            shutil.copy(path, new / path.name)
            continue
        try:
            text = sources.download_text(page["url"])
            (new / path.name).write_text(f"# {page['title']}\nURL: {page['url']}\n\n{text}", encoding="utf-8")
        except Exception as error:
            logger.warning("download failed, old copy kept | {} | {}", page["url"], error)
            failed.append(page["url"])
            shutil.copy(path, new / path.name)

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
    pages = len(list(new.glob("*.md")))
    if len(failed) > config.MAX_FAILED * pages:
        problems.append(f"{len(failed)} of {pages} downloads failed")
    rows = sources.count_sessions((new / "family-hubs-timetable.md").read_text(encoding="utf-8"))
    if rows < config.MIN_ROWS:
        problems.append(f"the timetable has only {rows} sessions")
    if '"sys"' in (new / "timetable.json").read_text(encoding="utf-8"):
        problems.append("timetable.json still holds staff data (sys)")
    return problems


def swap(staging) -> None:
    """Put the new knowledge and index live; keep the current ones in backup/."""
    shutil.rmtree(config.BACKUP_DIR, ignore_errors=True)
    config.BACKUP_DIR.mkdir()
    config.KNOWLEDGE.rename(config.BACKUP_DIR / "knowledge")
    if config.INDEX_DIR.exists():
        config.INDEX_DIR.rename(config.BACKUP_DIR / "index")
    (staging / "knowledge").rename(config.KNOWLEDGE)
    (staging / "index").rename(config.INDEX_DIR)
    shutil.rmtree(staging)


def rollback() -> bool:
    """Swap the live knowledge and index with the ones in backup/. Running it twice brings the new ones back."""
    if not (config.BACKUP_DIR / "knowledge").exists():
        logger.error("rollback not possible: there is no backup/knowledge")
        return False
    for name, live in (("knowledge", config.KNOWLEDGE), ("index", config.INDEX_DIR)):
        old = config.BACKUP_DIR / name
        newer = config.BACKUP_DIR / f"{name}-newer"
        if not old.exists():
            continue
        if live.exists():
            live.rename(newer)
        old.rename(live)
        if newer.exists():
            newer.rename(old)
    logger.warning("rollback done: the previous knowledge and index are live | restart the service")
    return True


def refresh() -> bool:
    """Download, check, build, test with the golden questions, swap. True if the new data is live."""
    staging = config.STAGING_DIR
    shutil.rmtree(staging, ignore_errors=True)
    logger.info("refresh started")

    failed = download_all(staging)
    problems = check_pages(staging, failed)
    if problems:
        logger.error("refresh stopped, the old knowledge stays live | {}", "; ".join(problems))
        return False

    sources.build_index(staging / "knowledge", staging / "index")
    score = sources.search_score(staging / "knowledge", staging / "index")
    if score < config.MIN_SEARCH_SCORE:
        logger.error("refresh stopped by the golden questions, the old knowledge stays live | "
                     "search score {:.0%}, needed {:.0%}", score, config.MIN_SEARCH_SCORE)
        return False

    swap(staging)
    logger.info("refresh done | {} failed downloads | search score {:.0%} | restart the service to use the new data",
                len(failed), score)
    return True


if __name__ == "__main__":
    logs.setup_logging()
    ok = rollback() if sys.argv[1:] == ["--rollback"] else refresh()
    sys.exit(0 if ok else 1)
