# Session 1: The assistant reads our documents

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** a first working assistant. It reads a small set of Family Hub files, knows today's date and answers questions from them.

**You get**
- `knowledge/`: the council web pages as text files (`.md`), the timetable export (`timetable.json`) and the files made from it
- `config.py`: ready, with the model address and the list `SMALL_KNOWLEDGE`
- `sessions/s1/start/bot.py`: the file you complete. Copy it to the main folder first: `cp sessions/s1/start/bot.py .`

**You build in `bot.py`** (keep these names, the check uses them)

| Function | What it does |
|---|---|
| `load_knowledge(names)` | Reads each file in `names` from `config.KNOWLEDGE` and returns a list like `[{"name": ..., "text": ...}]` |
| `build_prompt(docs, day)` | Puts our rules, today's date and all document texts into one instruction text for the model |
| `answer(question)` | Sends the instruction text and the question to the model and returns its reply |

## Steps
0. In the VS Code terminal, in your main folder (the one with `config.py`), copy the starter file: `cp sessions/s1/start/bot.py .` From now on open and run `bot.py` in the main folder, not the one in `sessions/s1/start`.
1. Open two or three files in `knowledge/` and read them. What is inside? What would a parent ask?
2. Write `load_knowledge`. Test it: `python -c "import bot; print(len(bot.DOCS))"` should print 11.
3. Write `build_prompt`. Print the result for one file and read it: is the date there? Are the rules there?
4. Write `answer`. Try it: `python bot.py "What is the phone number for North Family Hub?"`
5. Run the check: `python sessions/s1/check.py`

## Prompts for the AI assistant (paste into Open WebUI, then read what you get)
- *"Write a Python function load_knowledge(names) that reads each file name from the folder config.KNOWLEDGE (a pathlib Path) as UTF-8 text and returns a list of dictionaries with the keys name and text."*
- *"Write a Python function build_prompt(docs, day) that fills the string RULES using .format(today=..., documents=...). today is the date written like 'Sunday 22 November 2026'. documents joins all docs as '=== name ===' followed by the text, separated by blank lines."*
- *"Write a Python function answer(question) that calls an OpenAI-compatible chat model with client.chat.completions.create, model=config.MODEL, temperature=0, a system message from build_prompt(DOCS, today()) and the question as the user message. Return the text of the reply."*

**Done when** `python sessions/s1/check.py` prints `SESSION DONE` (6 of 6).

## Hints
- Error `No module named 'config'`: Python is not running in your main folder, or you are running `sessions/s1/start/bot.py` instead of the copy in the main folder. In the terminal: `cd` to the folder with `config.py`, then run the command again.
- Error `FileNotFoundError`: run Python from your main folder (the one with `config.py`).
- Strange characters: read files with `encoding="utf-8"`.
- The answer mentions a session that is already over: is the date in the prompt?

## Try at the end (the bridge to the next sessions)
- Ask *"What will the weather be like tomorrow?"* What happens?
- Change `SMALL_KNOWLEDGE` to all 116 files: `[p.name for p in config.KNOWLEDGE.glob("*.md")]`. What happens, and why?
