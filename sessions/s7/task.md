# Session 7: Knowledge from the website

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** until now the assistant answered from a `knowledge/` folder we gave you. After this session you make it yourself: one command, `python fetch_knowledge.py`, starts at the Blackpool family hubs page, walks through every page of the family hubs section and the SEND Local Offer, and saves the main text of each page. Then you check that nothing on the way got lost.

**You start from** your own session 6 version if `python sessions/s6/check.py` prints SESSION DONE. If not: `git stash -u`, `git fetch --tags`, `git checkout -b work gold-s6` (see `sessions/HOW_TO_WORK.md`).

**Before you start (once, the instructor):** install trafilatura into the Python environment the team uses: `pip install trafilatura httpx`

**How the download works**

| Step | What happens |
|---|---|
| 1. Crawl | start at `START` (and `EXTRA_PAGES`), read every link on the page, follow the ones inside our sections, each page only once |
| 2. Main text | keep only the text of the page as markdown: no menu, header or footer (trafilatura) |
| 3. Save | one file per page, `# Title`, `URL: ...`, an empty line, the text, always under the same file name |
| 4. Timetable | the sessions come from the council's timetable data, not from the page (ready in `timetable.py`) |
| 5. Swap | everything goes to `knowledge.new/` first; then `knowledge/` becomes `knowledge.previous/` and `knowledge.new/` becomes `knowledge/` |

**You get**
- `sessions/s7/start/fetch_knowledge.py`: copy to the main folder. Ready: the addresses (`START`, `EXTRA_PAGES`, `SECTIONS`), `page_key(url)`, `in_sections(url)`, `page_id(url)`
- `sessions/s7/start/timetable.py`: copy to the main folder. Ready: `save_timetable_pages(folder)`
- `.gitignore` must have two lines: `knowledge.new/` and `knowledge.previous/` (add them if they are not there)

**You build** in `fetch_knowledge.py` (keep these names, the check uses them)

| Function | What it does |
|---|---|
| `main_text(html)` | the main text of a page as markdown with `trafilatura.extract` (tables and links included); `""` if there is none |
| `crawl()` | a queue that starts with `[START] + EXTRA_PAGES`; download each page with `client.get`, skip it on an error; keep `(final url, html)`; add every link of the page for which `in_sections(link)` is True; each page only once (`page_key`), at most `MAX_PAGES` |
| `save_pages(pages, folder)` | for every page except `TIMETABLE_PAGE`: the title from `trafilatura.extract_metadata`, the text from `main_text`, the file `folder / f"{page_id(url)}.md"`; return the number of files |
| `main()` | step 5 of the table, with `timetable.save_timetable_pages(new)` before the swap |

## Steps
1. Copy the starter files: `cp sessions/s7/start/fetch_knowledge.py sessions/s7/start/timetable.py .` and check the two lines in `.gitignore`.
2. Write `main_text`. Try it on one page in a Python shell: `import fetch_knowledge as f; print(f.main_text(f.client.get(f.START).text))`
3. Write `crawl`. Try it: `pages = f.crawl(); print(len(pages))`. About 115 pages, in about one minute.
4. Write `save_pages` and `main`. Run `python fetch_knowledge.py`, then `git status knowledge/` and `git diff --stat knowledge/`: what changed on the council website since 21 November?
5. **Look at your data.** On the website, open "Support available at Blackpool family hubs" (the link is in `knowledge/support-available-at-blackpool-family-hub.md`). It has a section about gambling. Now search your file: `grep -i gambling knowledge/support-available-at-blackpool-family-hub.md`. Is it there? Compare the headings on the page with the headings in your file. Then find out why, and fix `main_text` (see the hints).
6. Download again, build the index: `python fetch_knowledge.py && python search.py --build`, and ask: `python bot.py "Where can I get help with gambling?"`
7. Run the check: `python sessions/s7/check.py`, then the checks of sessions 3 and 6.

## Prompts for the AI assistant
- *"Complete main_text(html) in fetch_knowledge.py: return trafilatura.extract(html, output_format='markdown', include_tables=True, include_links=True), or an empty string if it returns None."*
- *"Complete crawl() in fetch_knowledge.py: a breadth-first crawl. queue = [START] + EXTRA_PAGES, seen = set of page_key values, pages = list. While the queue is not empty and len(pages) < MAX_PAGES: take the first url, skip it if page_key(url) is in seen, else add it; response = client.get(url) and raise_for_status, on httpx.HTTPError print the url and continue; final = str(response.url), also add page_key(final) to seen (skip if it was already there and differs from url); append (final, response.text); for every href in re.findall(r'href=\"([^\"]+)\"', response.text): link = urldefrag(urljoin(final, href.replace('&amp;', '&'))).url, append it to the queue if in_sections(link). Return pages."*
- *"Complete save_pages(pages, folder): for each (url, html): name = page_id(url); skip TIMETABLE_PAGE; text = main_text(html), skip and print if empty; meta = trafilatura.extract_metadata(html); title = meta.title without ' - Blackpool Council' (or name); write f'# {title}\\nURL: {url}\\n\\n{text}' to folder / f'{name}.md' with utf-8. Return the number of files written."*
- *"Here is the HTML around the heading 'Help with money and debt' of a council page, and the text trafilatura returns for it. Why does trafilatura keep only the first section? Change main_text so that it keeps all sections."* (paste both)

**Done when** `python sessions/s7/check.py` prints `SESSION DONE` (9 of 9), and the checks of sessions 3 and 6 still pass.

## Hints
- `crawl()` never ends or finds thousands of pages: you follow links outside our sections. Only `in_sections(link)` decides.
- The same page twice under different names: the council links to some pages with capital letters and `.aspx`, and to others in lower case. `page_key` makes them the same.
- Why fixed file names (`PAGE_IDS`)? Two pages moved to a new address with a new name. The golden questions name the file that holds the answer, so the file name must not change when the address does.
- Step 5: open the page source in the browser (right click, View page source) and search for "Help with money and debt". Look at the `class="..."` of the `<div>` around it. Expandable sections ("accordions") are a common pattern on GOV.UK sites.
- After the fix, `support-available-at-blackpool-family-hub.md` is more than twice as long as before.
- `knowledge.previous/` is your way back: `rm -rf knowledge && mv knowledge.previous knowledge` and build the index again.

## Try at the end
- How many pages are new or gone since 21 November? (`git status knowledge/`)
- Set `MAX_PAGES = 10` and run `python fetch_knowledge.py`: what does the assistant answer now? Set it back and download again.
- Which other pages had expandable sections? (`git diff --stat knowledge/` before and after your fix)
