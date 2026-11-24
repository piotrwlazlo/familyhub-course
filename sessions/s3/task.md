# Session 3: The assistant finds the right passage

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** the assistant searches all 116 pages, reads only the 5 best passages and shows links to its sources. Search = Chroma (finds passages by meaning) + keyword search (BM25), merged into one list.

**You start from** the session 2 version (`git checkout gold-s2` if yours does not pass its check).

**You get**
- `sessions/s3/start/config_addition.py`: four new settings (`INDEX_DIR`, `CHUNK_CHARS`, `TOP_K`, `WHOLE_PAGES`); paste them into `config.py`
- `sessions/s3/start/search.py`: copy to the main folder. Ready: `read_page`, `words`, `fuse`. You write the rest
- `sessions/s3/start/bot.py`: the new `bot.py` (copy over yours). Ready: the `Answer` form and `build_prompt`. You write the rest

**You build**

| Where | Function | What it does |
|---|---|---|
| `search.py` | `make_chunks(text)` | Cuts a page into passages of at most 1000 characters, a new one at every heading |
| `search.py` | `build_index()` | Puts every passage of every page into Chroma, with its page title and web address |
| `search.py` | `search(query, k)` | 30 best by meaning + 30 best by keywords, merged with `fuse`, the best `k` returned. A passage of the timetable (`WHOLE_PAGES`) becomes the whole timetable page |
| `bot.py` | `write_answer(question, passages)` | The model reads the passages and fills in the `Answer` form |
| `bot.py` | `source_links(passages, used)` | The "Sources" list: links to the pages the model used, each page once |
| `bot.py` | `answer(question)` | analyse → search → write_answer → answer + sources |

## Steps
1. Write `make_chunks`. Cut one page and print the passages: do they make sense on their own?
2. Write `build_index`, then run it once: `python search.py --build` (the first time it downloads a small model, about 80 MB).
3. Write `search`. Try `python search.py "When is Neuro Ninjas?"` and read the passages: is the answer in one of them?
4. Compare: search only by meaning, only by keywords, then both. Which one finds more?
5. Write `write_answer`, `source_links` and the new `answer`. Try `python bot.py "When is Neuro Ninjas?"`
6. Run the check: `python sessions/s3/check.py`, then the checks of sessions 1 and 2.

## Prompts for the AI assistant
- *"Write a Python function make_chunks(text, max_chars) that splits a markdown text at blank lines into blocks and joins blocks into passages of at most max_chars characters. Start a new passage at every block that starts with '#'. If one block is longer than max_chars, cut it at line ends."*
- *"Write build_index() with chromadb.PersistentClient(path=str(config.INDEX_DIR)): delete the collection 'familyhub' if it exists, create it with metadata {'hnsw:space': 'cosine'}, and for each .md file in config.KNOWLEDGE use read_page and make_chunks and add the passages with ids '<page>#<n>', documents '<title>\n<passage>' and metadatas page, title, url."*

**Done when** `python sessions/s3/check.py` prints `SESSION DONE`: the right page is found for at least 90% of the golden questions, and 3 answers come with their source links.

## Hints
- `build_index` is slow: it runs once, not at every question.
- Search finds nothing useful: print the passages. Are they cut in the middle of a sentence? Is the page title in each one?
- Keyword search finds "the", "what", "is" everywhere: that is why `words()` leaves out small words.

## Why the whole timetable?
The timetable is one big table. Cut into pieces, only the first piece has the column names, and the model mixes up days and places. The whole table is about 3,500 tokens: small enough to give in one piece. In our test this took the score from 87% to 90%.

## Try at the end
- *"How do I contact CAFCASS?"* The page spells it "CAFCAS". What does each search method find? Why?
- *"Who is SEND Saturday for?"* Where is the answer, and why is it hard to find?
