# Session 10: Fresh knowledge every night

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** today the assistant knows the council pages as they were on 21 November 2026. The timetable ends on 23 December, so after Christmas it knows no sessions at all. After this session one command, `python refresh.py`, downloads every page and the timetable again, checks the new data and puts it live only when it is good. In production this command runs every night.

**How a safe refresh works**

| Step | What happens | If it goes wrong |
|---|---|---|
| 1. Download | every page again, into `staging/knowledge` (never straight into `knowledge/`) | a page that fails keeps its old copy, with a WARNING |
| 2. Quick rules | enough pages downloaded, the timetable has sessions, no staff data | stop: ERROR, the old knowledge stays live |
| 3. Build | a new search index in `staging/index` | |
| 4. Golden questions | the session 3 search test on the new index: does each question still find its page? | stop: ERROR, the old knowledge stays live |
| 5. Swap | `staging/` goes live, the old `knowledge/` and `index/` move to `backup/` | `python refresh.py --rollback` brings them back |

**You start from** the session 9 version (if yours does not pass its check, ask the instructor for the working version).

**Before you start (once, the instructor):** install trafilatura into the Python environment the team uses: `pip install trafilatura`

**You get**
- `sessions/s10/start/sources.py`: copy to the main folder. Ready: `download_text(url)`, `download_timetable()`, `save_timetable(events, folder)`, `count_sessions(text)`, `build_index(knowledge, index)`, `search_score(knowledge, index)`
- `sessions/s10/start/refresh.py`: copy to the main folder. Ready: the timetable part, the start of `refresh()` and the command line
- `sessions/s10/start/config_addition.py`: paste at the end of `config.py`
- add two lines to `.gitignore`: `staging/` and `backup/`

**You build** in `refresh.py` (keep these names, the check uses them)

| Function | What it does |
|---|---|
| `download_all(staging)` | for every page in `knowledge/`: skip `config.TIMETABLE_PAGES`; copy `config.KEEP_PAGES`; for all others `sources.download_text(page["url"])` and write `# <title>`, `URL: <url>`, an empty line and the text to `staging/knowledge/<same file name>`. On an error: `logger.warning` with the URL, add the URL to `failed`, copy the old file |
| `check_pages(staging, failed)` | three rules, each problem is one sentence in the list it returns: more than `config.MAX_FAILED` of the pages failed; fewer than `config.MIN_ROWS` sessions in `family-hubs-timetable.md`; `"sys"` in `timetable.json` |
| `swap(staging)` | empty `backup/`, move `knowledge/` and `index/` into it, move `staging/knowledge` and `staging/index` to their place, delete `staging/` |
| `rollback()` | swap the live `knowledge/` and `index/` with the ones in `backup/`; `logger.warning`; return `True` (`False` with `logger.error` if there is no backup) |
| `refresh()` | the five steps of the table above, with a log line for each result; return `True` only when the new data is live |

## Steps
1. Copy the starter files: `cp sessions/s10/start/sources.py sessions/s10/start/refresh.py .`, paste `config_addition.py` at the end of `config.py`, add the two lines to `.gitignore`.
2. Write `check_pages`. Run the check: `python sessions/s10/check.py`. The first line should say PASS.
3. Write `download_all` and `refresh` up to the quick rules. Run the check again: "website down" should pass.
4. Add the build, the golden questions and `swap` to `refresh`. Run the check: "maintenance pages" and "normal night" should pass.
5. Write `rollback`. Run the check: `SESSION DONE`.
6. **The real thing:** `python refresh.py`. It downloads about 115 pages (a few minutes). Read the log lines: how many downloads failed, what search score did the new data get? Then see what changed on the council website since 21 November: `git diff --stat knowledge/`, and for one page `git diff knowledge/<page>.md`
7. Ask about the new data, for example `python bot.py "What is on at North Family Hub next week?"`. A running service (session 8) still answers from the old data until you restart it.
8. Go back to the course data, because the checks of the other sessions expect the knowledge from 21 November: `python refresh.py --rollback`, then `git status` should show no changes in `knowledge/`.

## Every night in production
One line in the crontab of the service account (`crontab -e`) runs the refresh at 2 am, and a restart of the service after a good refresh:
```
0 2 * * * cd /opt/familyhub && .venv/bin/python refresh.py && systemctl restart familyhub
```
Do not add it on the course GB10. Who runs it on the council's server, and who reads the ERROR lines in the morning, is a question for council IT (see the deck).

## Prompts for the AI assistant
- *"Complete check_pages(staging, failed) in refresh.py. new = staging / 'knowledge'. Add one sentence to problems for each rule: if len(failed) is more than config.MAX_FAILED times the number of .md files in new; if sources.count_sessions of the text of new / 'family-hubs-timetable.md' is below config.MIN_ROWS; if the text of new / 'timetable.json' contains '\"sys\"'. Return problems."*
- *"Complete the loop in download_all: if page['page'] is in config.TIMETABLE_PAGES continue; if it is in config.KEEP_PAGES copy path to new / path.name with shutil.copy and continue; otherwise try text = sources.download_text(page['url']) and write f\"# {page['title']}\\nURL: {page['url']}\\n\\n{text}\" to new / path.name; except Exception as error: logger.warning with the url and the error, failed.append(page['url']), copy the old file."*
- *"Complete swap(staging) with shutil.rmtree(config.BACKUP_DIR, ignore_errors=True), mkdir, Path.rename: config.KNOWLEDGE to BACKUP_DIR / 'knowledge', config.INDEX_DIR to BACKUP_DIR / 'index', staging / 'knowledge' to config.KNOWLEDGE, staging / 'index' to config.INDEX_DIR, then shutil.rmtree(staging)."*
- *"Write rollback(): for knowledge and index, swap the live folder with the one in config.BACKUP_DIR using a temporary name BACKUP_DIR / (name + '-newer'). If there is no BACKUP_DIR / 'knowledge', log an error and return False."*

**Done when** `python sessions/s10/check.py` prints `SESSION DONE` (5 of 5) and step 8 left your `knowledge/` unchanged. The check works in a throw-away copy with simulated downloads, so it needs no internet and does not touch your folder.

## Hints
- Why `staging/` and not straight into `knowledge/`? If the download stops half way, the assistant would answer from half old, half new pages. A swap is two quick renames.
- Why the golden questions and not only the rules? A website in maintenance returns pages that look fine (long text, status 200) but say nothing. Only a quality test sees that the right pages are no longer found.
- Why the search test and not the full answer test of session 5? Answers about dates change when the timetable changes, so their expected text would fail. The page that holds the answer stays the same.
- `PermissionError` or `FileExistsError` in `swap`: a `staging/` or `backup/` from an earlier run is still there. `refresh()` deletes `staging/` at the start; `swap` must empty `backup/` first.
- The service answers with old data after a refresh: it loaded the index when it started. Restart it.
- `timetable.json` from the council holds the names of the staff who edited each entry (`sys`). `save_timetable` removes them; the rule in `check_pages` makes sure they never reach `knowledge/`.

## Try at the end
- Run `python refresh.py` twice. The second time, what is in `backup/`?
- Set `MIN_SEARCH_SCORE = 0.99` in `config.py` and run the refresh: what does the log say? Set it back.
- Which ERROR line would you want to see in a morning e-mail, and which WARNING lines can wait?
