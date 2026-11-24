"""Session 3: find the right passages in all our documents.

Build the index once:   python search.py --build
Try a search:           python search.py "When is Neuro Ninjas?"
"""
import re
import sys

import chromadb
from rank_bm25 import BM25Okapi

import config


def read_page(path) -> dict:
    """A knowledge file starts with '# Title' and 'URL: ...'. Return title, url and text."""
    text = path.read_text(encoding="utf-8")
    title = text.split("\n", 1)[0].lstrip("# ").strip()
    url = re.search(r"^URL: (\S+)", text, re.M)
    return {"page": path.stem, "title": title, "url": url.group(1) if url else "", "text": text}


def make_chunks(text: str, max_chars: int = config.CHUNK_CHARS) -> list[str]:
    """Cut a page into passages of at most max_chars: a new passage at every heading (a block starting
    with "#"), or when the passage would get too long. Blank lines separate the blocks of text.
    A single block longer than max_chars (a big table) is cut at line ends."""
    # TODO
    return []


def build_index() -> None:
    """Cut every knowledge page into passages and store them in Chroma (on disk, in config.INDEX_DIR).
    Collection name "familyhub", metadata={"hnsw:space": "cosine"}. Delete the old collection first.
    For every passage: id "<page>#<number>", document "<title>
<passage>", metadata page, title, url."""
    # TODO
    pass


def words(text: str) -> list[str]:
    """The words of a text for the keyword search: lower case, without the small words."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]


# Open the index once, and build the keyword search (BM25) from the same passages
collection = chromadb.PersistentClient(path=str(config.INDEX_DIR)).get_or_create_collection("familyhub")
ALL = collection.get()
bm25 = BM25Okapi([words(doc) for doc in ALL["documents"]]) if ALL["ids"] else None


def fuse(*ranked_lists: list[str]) -> list[str]:
    """Reciprocal rank fusion: merge several ranked lists of ids into one. Given, no need to change."""
    score = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked):
            score[chunk_id] = score.get(chunk_id, 0) + 1 / (60 + rank)
    return sorted(score, key=score.get, reverse=True)


def search(query: str, k: int = config.TOP_K) -> list[dict]:
    """Return the k best passages for the query: meaning search (Chroma) and keyword search (BM25) together.
    1. collection.query(query_texts=[query], n_results=30) gives 30 ids by meaning
    2. bm25.get_scores(words(query)) gives a score for every passage: take the ids of the 30 best
    3. fuse(by_meaning, by_words)[:k] merges both lists
    4. return a list of dicts: id, text, page, title, url
    5. a passage from a page in config.WHOLE_PAGES (the timetable): give the whole page instead, once
       (read_page(config.KNOWLEDGE / f"{page}.md") gives its text)"""
    # TODO
    return []


if __name__ == "__main__":
    if sys.argv[1:] == ["--build"]:
        build_index()
    else:
        for hit in search(" ".join(sys.argv[1:]) or "When is Neuro Ninjas?"):
            print(f"--- {hit['id']}  ({hit['title']})\n{hit['text'][:300]}\n")
