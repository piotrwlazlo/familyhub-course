# Session 3: the search index (Chroma, on disk) and how we cut and search the pages
INDEX_DIR = HERE / "index"
CHUNK_CHARS = 1000     # a passage is at most this many characters
TOP_K = 5              # how many passages the model reads for one answer
# Pages that only make sense as a whole (a big table): when search finds a passage of one, the model gets the whole page
WHOLE_PAGES = ["family-hubs-timetable"]
