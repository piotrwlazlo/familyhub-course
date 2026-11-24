"""Settings for the Family Hub assistant. Change values here, not in the code."""
from pathlib import Path

# --- The AI model (Gemma 4 26B, served by vLLM on the GB10) ---
MODEL_URL = "http://localhost:8004/v1"
MODEL = "gemma-4-26b"

# --- Our knowledge ---
HERE = Path(__file__).parent
KNOWLEDGE = HERE / "knowledge"

# Session 3: the search index (Chroma, on disk) and how we cut and search the pages
INDEX_DIR = HERE / "index"
CHUNK_CHARS = 1000     # a passage is at most this many characters
TOP_K = 5              # how many passages the model reads for one answer
# Pages that only make sense as a whole (a big table): when search finds a passage of one, the model gets the whole page
WHOLE_PAGES = ["family-hubs-timetable"]

# Session 1: the small set of files that fits into one prompt
SMALL_KNOWLEDGE = [
    "hub-contacts.md",
    "family-hubs-timetable.md",
    "family-hubs-activities.md",
    "blackpool-family-hubs.md",
    "family-hubs-and-start-for-life.md",
    "support-available-at-blackpool-family-hub.md",
    "programmes-for-parents.md",
    "parent-and-carer-panels.md",
    "relationship-support.md",
    "supporting-your-child.md",
    "register-a-birth.md",
]

# --- Today's date ---
# None = the real date. Tests set a fixed date, so "when is the next ..." always has the same answer.
TODAY = None

# --- Fixed replies (ours, never written by the model) ---
HUBS_PAGE = ("https://www.blackpool.gov.uk/Residents/Education-and-schools/Early-years-and-childcare/"
             "Family-Hubs-and-Start-for-Life/Family-Hubs/Family-Hubs-timetable.aspx")
OFF_TOPIC_REPLY = ("Sorry, I can only help with information from the Blackpool Family Hub web pages, for example "
                   "family hub activities, support for families, parenting programmes, SEND and registering a birth.")
CRISIS_REPLY = ("If you or someone else is in danger right now, call 999. "
                "You can call the National Domestic Abuse Helpline free, day or night, on 0808 2000 247, "
                "and Samaritans on 116 123.")
FALLBACK_REPLY = ("Sorry, I can't answer that here. Please contact your local family hub "
                  f"([phone numbers and addresses]({HUBS_PAGE})).")
