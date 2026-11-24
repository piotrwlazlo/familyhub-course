"""Hybrid retrieval over the knowledge base: Chroma (semantic) + BM25 (keyword).

Build the index:  python search.py --build
Search:           python search.py "When is Neuro Ninjas?"
"""
import re
import sys

import chromadb
from rank_bm25 import BM25Okapi

import config


def read_page(path) -> dict:
    """Parse a knowledge file ('# Title' and 'URL: ...' header) into page id, title, url and text."""
    text = path.read_text(encoding="utf-8")
    title = text.split("\n", 1)[0].lstrip("# ").strip()
    url = re.search(r"^URL: (\S+)", text, re.M)
    return {"page": path.stem, "title": title, "url": url.group(1) if url else "", "text": text}


def make_chunks(text: str, max_chars: int = config.CHUNK_CHARS) -> list[str]:
    """Split a markdown page into passages of at most max_chars.

    A new passage starts at each heading or when the size limit is reached; oversized blocks are split at line ends.
    """
    chunks, current = [], ""
    for block in re.split(r"\n\s*\n", text):
        block = block.strip()
        if not block:
            continue
        if current and (block.startswith("#") or len(current) + len(block) > max_chars):
            chunks.append(current)
            current = ""
        while len(block) > max_chars:
            cut = block.rfind("\n", 0, max_chars)
            cut = cut if cut > 200 else max_chars
            chunks.append(block[:cut])
            block = block[cut:].strip()
        current = (current + "\n\n" + block).strip()
    if current:
        chunks.append(current)
    return chunks


def build_index() -> None:
    """(Re)build the persistent Chroma collection from all knowledge files."""
    db = chromadb.PersistentClient(path=str(config.INDEX_DIR))
    if "familyhub" in [c.name for c in db.list_collections()]:
        db.delete_collection("familyhub")
    collection = db.create_collection("familyhub", metadata={"hnsw:space": "cosine"})
    for path in sorted(config.KNOWLEDGE.glob("*.md")):
        page = read_page(path)
        chunks = make_chunks(page["text"])
        collection.add(ids=[f"{page['page']}#{i}" for i in range(len(chunks))],
                       documents=[f"{page['title']}\n{chunk}" for chunk in chunks],   # prefix the page title
                       metadatas=[{"page": page["page"], "title": page["title"], "url": page["url"]}] * len(chunks))
        print(f"{page['page']:60} {len(chunks):3} passages")
    print(f"\nIndex ready: {collection.count()} passages")


# Stop words excluded from keyword scoring
STOP_WORDS = set("a an the is are was what when where who how do does i my me can of for to in on at "
                 "and or it its there this that be any with about".split())


def words(text: str) -> list[str]:
    """Tokenise text for BM25: lower case, alphanumeric, stop words removed."""
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS]


# Load the collection once and build the BM25 index over the same passages
collection = chromadb.PersistentClient(path=str(config.INDEX_DIR)).get_or_create_collection("familyhub")
ALL = collection.get()
bm25 = BM25Okapi([words(doc) for doc in ALL["documents"]]) if ALL["ids"] else None


def fuse(*ranked_lists: list[str]) -> list[str]:
    """Merge ranked id lists with reciprocal rank fusion."""
    score = {}
    for ranked in ranked_lists:
        for rank, chunk_id in enumerate(ranked):
            score[chunk_id] = score.get(chunk_id, 0) + 1 / (60 + rank)
    return sorted(score, key=score.get, reverse=True)


def search(query: str, k: int = config.TOP_K) -> list[dict]:
    """Return the top k passages for the query using hybrid retrieval.

    Passages from pages listed in config.WHOLE_PAGES are replaced by the full page (once).
    """
    by_meaning = collection.query(query_texts=[query], n_results=30)["ids"][0]
    scores = bm25.get_scores(words(query))
    by_words = [ALL["ids"][i] for i in sorted(range(len(scores)), key=lambda i: -scores[i])[:30]]
    best = fuse(by_meaning, by_words)[:k]
    position = {chunk_id: i for i, chunk_id in enumerate(ALL["ids"])}
    hits, whole_done = [], set()
    for cid in best:
        meta = ALL["metadatas"][position[cid]]
        if meta["page"] in config.WHOLE_PAGES:
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
