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
    """Cut a page into passages of at most max_chars: a new passage at every heading,
    or when the passage would get too long. Blank lines separate the blocks of text."""
    chunks, current = [], ""
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        if current and (block.startswith("#") or len(current) + len(block) > max_chars):
            chunks.append(current)
            current = ""
        while len(block) > max_chars:                # a very long block (a big table): cut it at line ends
            cut = block.rfind("\n", 0, max_chars)
            cut = cut if cut > 200 else max_chars
            chunks.append(block[:cut])
            block = block[cut:].strip()
        current = (current + "\n\n" + block).strip()
    if current:
        chunks.append(current)
    return chunks


def build_index() -> None:
    """Cut every knowledge page into passages and store them in Chroma (on disk, in config.INDEX_DIR)."""
    db = chromadb.PersistentClient(path=str(config.INDEX_DIR))
    if "familyhub" in [c.name for c in db.list_collections()]:
        db.delete_collection("familyhub")
    collection = db.create_collection("familyhub", metadata={"hnsw:space": "cosine"})
    for path in sorted(config.KNOWLEDGE.glob("*.md")):
        page = read_page(path)
        chunks = make_chunks(page["text"])
        collection.add(ids=[f"{page['page']}#{i}" for i in range(len(chunks))],
                       documents=[f"{page['title']}\n{chunk}" for chunk in chunks],   # every passage keeps its page title
                       metadatas=[{"page": page["page"], "title": page["title"], "url": page["url"]}] * len(chunks))
        print(f"{page['page']:60} {len(chunks):3} passages")
    print(f"\nIndex ready: {collection.count()} passages")


# Small words that appear everywhere and do not help the keyword search
STOP_WORDS = set("a an the is are was what when where who how do does i my me can of for to in on at "
                 "and or it its there this that be any with about".split())


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
    """Return the k best passages for the query: meaning search (Chroma) and keyword search (BM25) together."""
    by_meaning = collection.query(query_texts=[query], n_results=30)["ids"][0]
    scores = bm25.get_scores(words(query))
    by_words = [ALL["ids"][i] for i in sorted(range(len(scores)), key=lambda i: -scores[i])[:30]]
    best = fuse(by_meaning, by_words)[:k]
    position = {chunk_id: i for i, chunk_id in enumerate(ALL["ids"])}
    hits, whole_done = [], set()
    for cid in best:
        meta = ALL["metadatas"][position[cid]]
        if meta["page"] in config.WHOLE_PAGES:          # a big table: give the whole page once, not a cut piece
            if meta["page"] not in whole_done:
                whole_done.add(meta["page"])
                hits.append({"id": meta["page"], **read_page(config.KNOWLEDGE / f"{meta['page']}.md"), **meta})
        else:
            hits.append({"id": cid, "text": ALL["documents"][position[cid]], **meta})
    return hits


if __name__ == "__main__":
    if sys.argv[1:] == ["--build"]:
        build_index()
    else:
        for hit in search(" ".join(sys.argv[1:]) or "When is Neuro Ninjas?"):
            print(f"--- {hit['id']}  ({hit['title']})\n{hit['text'][:300]}\n")
