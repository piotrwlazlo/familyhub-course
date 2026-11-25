# Session 8: The assistant tells us what happens

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** today, if the model is down, a resident just gets the polite fallback reply and nobody knows. After this session every question leaves a line in a log file, with a level that says how serious it is: **INFO** (normal), **WARNING** (it worked, but someone should look), **ERROR** (it failed for someone). What the model returned goes to a separate file. A health check says if the assistant is ready.

**You start from** your own session 6 version if `python sessions/s6/check.py` prints SESSION DONE (session 7 is not needed for this session). If not: `git stash -u`, `git fetch --tags`, `git checkout -b work gold-s6` (see `sessions/HOW_TO_WORK.md`).

**Before you start (once, the instructor):** install the new packages into the Python environment the team uses: `pip install loguru fastapi uvicorn httpx`

**You get**
- `sessions/s8/start/logs.py`: copy to the main folder. Ready: the line formats, `is_reasoning`, `not_reasoning`, `new_request_id`
- `sessions/s8/start/app.py`: copy to the main folder. Ready: the assistant as a web service (`/v1/chat/completions`)
- `sessions/s8/start/config_addition.py`: `LOG_DIR` and `LOG_LEVEL`; paste at the end of `config.py`

**You build** (keep these names, the check uses them)

| Where | What |
|---|---|
| `logs.py`: `setup_logging()` | Three outputs: the terminal (coloured), `logs/familyhub.log`, `logs/reasoning.log` |
| `logs.py`: `log_reasoning(step, message)` | One line in `logs/reasoning.log`: the step, the model's reasoning (if any) and the form it filled in |
| `bot.py`: top of the file | `import logs` and `from loguru import logger`; call `logs.setup_logging()` once, after `client = ...` |
| `analysis.py` and `bot.py`: `analyse`, `write_answer` | After the model call: `logs.log_reasoning(...)`. In the `except` part: `logger.exception(...)` |
| `bot.py`: `answer(question, history)` | All of it inside `with logger.contextualize(request_id=logs.new_request_id()):`, and one log line before every `return` (table below) |
| `checks.py`: `check_answer` | `logger.warning(...)` that says which rule blocked the answer |
| `app.py`: `health()` and `model_ok()` | `/health` answers 200 if the model and the search index are ready, otherwise 503 |

**Which level for which event in `answer()`**

| Event | Level | Example message |
|---|---|---|
| Crisis words in the question, or the model marked it as a crisis | WARNING | `crisis reply sent` |
| No question analysis (the model failed) | ERROR | `no question analysis: fallback reply sent` |
| Off-topic question | INFO | `off-topic question` |
| No answer from the model (the model failed) | ERROR | `no answer from the model: fallback reply sent` |
| Answered | INFO | `answered | kind=time | pages=[...] | 4.2 s` |

## Steps
1. Copy the starter files to the main folder: `cp sessions/s8/start/logs.py sessions/s8/start/app.py .` and paste `config_addition.py` at the end of `config.py`.
2. Write `setup_logging`. Add the three lines at the top of `bot.py`. Try it: `python bot.py "When is Babbling Babies?"` You should see no new lines yet, but the folder `logs/` appears.
3. Add the log lines to `answer()` (see the table). Ask again: now you see coloured lines in the terminal, and the same lines in `logs/familyhub.log`.
4. Write `log_reasoning` and call it in `analyse` and `write_answer`. Open `logs/reasoning.log`: what did the model fill in for your question?
5. Add `logger.exception` to both `except` parts, and `logger.warning` to `check_answer`.
6. Write `model_ok` and `health`. Start the service on your own port and ask it: `.venv/bin/uvicorn app:app --port <your port>`, then in a second terminal `curl localhost:<your port>/health`
7. Run the check: `python sessions/s8/check.py`, then the checks of sessions 4 and 6.

## Prompts for the AI assistant
- *"Complete setup_logging in logs.py with loguru: add three outputs with logger.add and append each returned id to our_outputs: sys.stderr with level config.LOG_LEVEL, format TERMINAL_FORMAT, colorize=True, filter=not_reasoning; the file config.LOG_DIR / 'familyhub.log' with level config.LOG_LEVEL, format FILE_FORMAT, filter=not_reasoning, rotation='10 MB', retention='14 days', encoding='utf-8'; the file config.LOG_DIR / 'reasoning.log' with level 'DEBUG', format FILE_FORMAT, filter=is_reasoning, retention='3 days', encoding='utf-8'."*
- *"Complete log_reasoning(step, message): write one line with logger.bind(reasoning=True).debug that contains step, reasoning (or '(the model returned no reasoning)' if it is None) and message.content."*
- *"In this answer() function, put the whole body inside `with logger.contextualize(request_id=logs.new_request_id()):` and add a loguru log line before every return: WARNING for the crisis replies, ERROR when the model failed (form is None or result is None), INFO for off-topic, and INFO for an answered question with form.kind, the pages used and the seconds since the start (time.perf_counter())."*
- *"Write a FastAPI endpoint GET /health: checks = {'model': model_ok(), 'index': search.collection.count() > 0}. If all checks are True return JSONResponse({'status': 'ok', **checks}) with status 200, otherwise log logger.error with the checks and return status 'error' with status code 503."*

**Done when** `python sessions/s8/check.py` prints `SESSION DONE` (10 of 10), and the checks of sessions 4 and 6 still pass.

## Hints
- Error `KeyError: 'request_id'`: `setup_logging` was not run, or a line was written before it. Call `logs.setup_logging()` at the top of `bot.py`.
- Every line appears twice in the terminal: run `setup_logging` only once, and keep the ready part at its top.
- No `logs/reasoning.log`: did you use `logger.bind(reasoning=True)`? Without it the line goes to the main log.
- `logger.exception` writes the error and where it happened (the traceback): that is what `except Exception: return None` was hiding.
- Logs are personal data too: the search query in `reasoning.log` repeats what the person asked. That is why this file is kept only 3 days.
- Port already in use: someone else has that port. Use the one your instructor gave you.

## Try at the end
- Pretend the model is down: in `config.py` set `MODEL_URL = "http://localhost:9/v1"`, ask a question, then read `logs/familyhub.log`. Can you tell from the log what went wrong? Put the old address back.
- Set `LOG_LEVEL = "DEBUG"`: what changes?
- Add `serialize=True` to the `familyhub.log` output and look at one line: this is the JSON format a central log platform wants. Then remove it again.
