
# Session 10: nightly data refresh (python refresh.py)
STAGING_DIR = HERE / "staging"     # the new knowledge and index are built here first
BACKUP_DIR = HERE / "backup"       # the previous knowledge and index, for python refresh.py --rollback
TIMETABLE_URL = "https://www.blackpool.gov.uk/custom/api/contenttype/entries/familyHubEvents"   # sessions (JSON)
TIMETABLE_PAGES = ["family-hubs-timetable", "family-hubs-activities"]   # built from the timetable data
KEEP_PAGES = ["hub-contacts"]      # pages we wrote ourselves: copied as they are, never downloaded
MAX_FAILED = 0.10                  # more failed downloads than this share: keep the old knowledge
MIN_ROWS = 10                      # the new timetable must have at least this many sessions
MIN_SEARCH_SCORE = 0.90            # golden questions: share that must find the right page (session 3 target)
