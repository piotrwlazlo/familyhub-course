"""Settings for the Family Hub assistant. Change values here, not in the code."""
from pathlib import Path

# --- The AI model (Gemma 4 26B, served by vLLM on the GB10) ---
MODEL_URL = "http://localhost:8004/v1"
MODEL = "gemma-4-26b"

# --- Our knowledge ---
HERE = Path(__file__).parent
KNOWLEDGE = HERE / "knowledge"

# Session 3: the small set of files that fits into one prompt
SMALL_KNOWLEDGE = [
    "hub-contacts.md",
    "family-hubs-timetable.md",
    "family-hubs-activities.md",
    "family-hubs-and-start-for-life.md",
    "programmes-for-parents.md",
    "parent-and-carer-panels.md",
    "relationship-support.md",
    "supporting-your-child.md",
    "register-a-birth.md",
]

# --- Today's date ---
# None = the real date. Tests set a fixed date, so "when is the next ..." always has the same answer.
TODAY = None
