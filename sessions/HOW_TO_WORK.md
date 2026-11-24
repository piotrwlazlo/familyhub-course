# How to work: VS Code on the GB10

Everyone works with their own Linux account and their own copy of the code on the GB10, in VS Code (connected to the GB10 the same way as in the earlier labs). Nobody works in a shared folder, so nobody can break someone else's code.

## Your own folder (once, before session 3)
1. Get your own copy of this repository in your home folder, for example `~/familyhub` (your instructor tells you how).
2. Put the `knowledge` folder from your instructor into `~/familyhub`.
3. In VS Code: File > Open Folder > `~/familyhub`
4. Open the terminal (Terminal > New Terminal) and create the Python environment:
   `python3 -m venv .venv && .venv/bin/pip install openai pydantic chromadb rank_bm25 ipykernel`
5. Pick the Python interpreter: `Ctrl+Shift+P` > *Python: Select Interpreter* > `.venv/bin/python`

## Every session
- Write the code in the `.py` files (`bot.py`, `search.py` ...). The task card says which file and which function.
- Run everything in the VS Code terminal, from your folder, for example `python bot.py "When is Babbling Babies?"` and `python sessions/s3/check.py`
- Want to try things step by step? Make a notebook `scratch.ipynb` (Jupyter extension), pick the `.venv` kernel and use:
  ```python
  import importlib, bot
  importlib.reload(bot)      # run this after every change to bot.py, or the notebook keeps the old code
  bot.answer("When is Babbling Babies?")
  ```
- Your version does not pass the check of the last session? Ask your instructor for the working version before you start the new session, so you start from code that works.
