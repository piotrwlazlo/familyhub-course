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
| 7 | Your own knowledge: download every council page from the website (`fetch_knowledge.py`), every section included |
| 8 | Logs (INFO / WARNING / ERROR), the model's reasoning in its own file, and a health check |
| 9 | Unit tests and a smoke test written by you, and a real bug fixed |
| 10 | Fresh knowledge every night: download, check with the golden questions, swap and roll back |

## Folders

| Path | What |
|---|---|
| `config.py` | Settings: model address, files, later search settings and fixed replies |
| `knowledge/` | The council web pages as text files (116), the timetable export and the pages made from it, hub contacts |
| `sessions/sN/task.md` | The task card for session N: what to build, step by step |
| `sessions/sN/start/` | Starter files for session N |
| `sessions/sN/check.py` | Run it to see if you are done: it prints `SESSION DONE` |
| `sessions/golden_questions.json` | Golden questions with the facts the answers must contain |
| `familyhub_pipe.py`, `deploy_openwebui.sh` | Session 6: the assistant inside Open WebUI (deploy: instructor only) |

## How the team works on the GB10

- Every participant has their own folder in the team folder: `aidevteam/familyhub-<name>`, a `git clone` of this repository. Each person works only in their own folder (see `sessions/HOW_TO_WORK.md`).
- Starting session 7: whoever passes `python sessions/s6/check.py` goes on with their own code; everyone else runs `git stash -u`, `git fetch --tags`, `git checkout -b work gold-s6`.
- New sessions: the instructor adds them to every folder, changing only the session files:
  ```bash
  cd aidevteam
  for d in familyhub-*; do
    git -C "$d" fetch origin --tags && git -C "$d" checkout origin/main -- sessions README.md deploy_openwebui.sh
  done
  ```
- The model: Gemma 4 26B served by vLLM on port 8004 (`config.MODEL_URL`). From session 3 on, each person builds their own search index once: `python search.py --build`
- Open WebUI is shared by the whole team. Only the instructor updates the Family Hub assistant there, from the instructor's own folder, with a version that passes all session checks: `bash deploy_openwebui.sh --instructor`. Participants never run this script: it replaces the assistant for everyone.

## Before session 1

1. Get your own copy of this repository and open the folder in VS Code (see `sessions/HOW_TO_WORK.md`).
2. Create the Python environment: `python3 -m venv .venv && .venv/bin/pip install openai pydantic chromadb rank_bm25 ipykernel`
3. Check `MODEL_URL` and `MODEL` in `config.py`: they point to the AI model on your GB10.

Then open `sessions/s1/task.md` and start.
