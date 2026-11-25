# Family Hub assistant: course repository

The team builds the Family Hub assistant step by step, in sessions 1 to 8. Every session has a task card, starter files and a check. The tags `gold-s1` ... `gold-s8` are the working version after each session.

## Folders

| Path | What |
|---|---|
| `knowledge/` | The council web pages as text (116 `.md` files), `timetable.json`, `hub-contacts.md` |
| `config.py` | All settings: model address, files, search settings, fixed replies |
| `bot.py` | The assistant: question in, answer out |
| `analysis.py` | Session 2: the form about the question (structured output) |
| `search.py` | Session 3: passages in Chroma + keyword search (BM25) |
| `checks.py` | Session 4: our rules check every answer |
| `tests/` | Session 5: golden questions and the test run with its report |
| `familyhub_pipe.py`, `deploy_openwebui.sh` | Session 6: the assistant inside Open WebUI |
| `logs.py` | Session 7: logging setup: terminal, logs/familyhub.log, logs/reasoning.log |
| `tests/test_units.py`, `tests/smoke_test.py` | Session 8: unit tests (pytest, no model) and a smoke test for the running service |
| `app.py`, `run_app.sh` | For the instructor: the finished assistant as a server on port 8100 (`bash run_app.sh`), for Open WebUI as a connection |
| `sessions/sN/` | `task.md` (task card), `start/` (starter files), `check.py` (done when it says SESSION DONE) |
| `sessions/golden_questions.json` | Our 91 golden questions (used by the session 3 check) |

## Start (once, on the GB10)

The course package `familyhub-course.tar.gz` holds this repository and two scripts:

1. One person with sudo rights (for example the GB10 admin), once:
   `tar xzf familyhub-course.tar.gz && cd familyhub-course && sudo bash install_shared.sh`
   This makes `/srv/familyhub-course`: the code package and one Python environment, read-only for everyone.
2. Every participant, as themselves, once (seconds): `bash /srv/familyhub-course/get_my_copy.sh`
   This makes `~/familyhub`, their own copy on their own branch, starting at `gold-s1`. See `sessions/HOW_TO_WORK.md`.

The model: Gemma 4 26B served by vLLM on port 8004 (`config.MODEL_URL`).
From session 3 on, each person builds their own search index once: `python search.py --build`
Session 6 (`deploy_openwebui.sh`) needs rights to run `docker`: one person with those rights deploys the team's version.

## Using the golden state

```bash
git tag                          # gold-s1 ... gold-s8
git checkout gold-s3             # the whole working version after session 3
git checkout gold-s3 -- search.py   # only one file from it
python sessions/s3/check.py      # every session has its own check
```
Each session starts from the golden state of the session before, so everyone starts from code that works.

## Results of the golden state (GB10-1, Gemma 4 26B, 24 November 2026)

| Check | Result |
|---|---|
| Session 1 | 6/6 |
| Session 2 | 12/12 |
| Session 3 | search finds the right page for 74/77 golden questions (96%), 3/3 answers |
| Session 4 | 4 rules + 10/10 tricky questions |
| Session 5 | 90 to 91% on 99 golden questions (the first version of the assistant: 81%) |
| Session 6 | 7/7, and tested inside the Open WebUI container |
| Session 7 | 10/10 |
| Session 8 | 17 unit tests, 6/6 broken versions caught, smoke test 4/4, empty message list gives 400 |
