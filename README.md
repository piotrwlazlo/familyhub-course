# Family Hub assistant: course labs

In these labs you build the Family Hub assistant step by step: a chat assistant that answers questions from the council's Family Hub web pages, shows its sources and keeps to clear safety rules. It runs on a local AI model and is used through Open WebUI.

| Session | You build |
|---|---|
| 1 | The assistant reads the knowledge files and knows today's date |
| 2 | The model fills in a short form about the question (structured output) |
| 3 | Search by meaning (Chroma) and by keywords, answers with source links |
| 4 | Rules that check every answer before anyone sees it |
| 5 | Golden questions and a test run with a score |
| 6 | The assistant inside Open WebUI, with conversation history |

## Folders

| Path | What |
|---|---|
| `config.py` | Settings: model address, files, later search settings and fixed replies |
| `knowledge/` | The council web pages as text files (116), the timetable export and the pages made from it, hub contacts |
| `sessions/sN/task.md` | The task card for session N: what to build, step by step |
| `sessions/sN/start/` | Starter files for session N |
| `sessions/sN/check.py` | Run it to see if you are done: it prints `SESSION DONE` |
| `sessions/golden_questions.json` | Golden questions with the facts the answers must contain |
| `deploy_openwebui.sh` | Session 6: copies your code into the Open WebUI container |

## Before session 1

1. Get your own copy of this repository and open the folder in VS Code (see `sessions/HOW_TO_WORK.md`).
2. Create the Python environment: `python3 -m venv .venv && .venv/bin/pip install openai pydantic chromadb rank_bm25 ipykernel`
3. Check `MODEL_URL` and `MODEL` in `config.py`: they point to the AI model on your GB10.

Then open `sessions/s1/task.md` and start.
