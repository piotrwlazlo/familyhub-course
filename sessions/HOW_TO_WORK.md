# How to work: VS Code on the GB10

Everyone works with their own Linux account and their own folder on the GB10, in VS Code (connected to the GB10 the same way as in the earlier labs).

## Your own folder (once, before session 1)
Everyone has their own copy. Nobody works in a shared folder, so nobody can break someone else's code.
1. In the VS Code terminal (Terminal > New Terminal) run:  `bash /srv/familyhub-course/get_my_copy.sh`
   It takes a few seconds and makes `~/familyhub`. Nothing to install: the Python environment is shared and ready.
2. In VS Code: File > Open Folder > `~/familyhub`
3. Pick the Python interpreter: `Ctrl+Shift+P` > *Python: Select Interpreter* > `.venv/bin/python`

(`/srv/familyhub-course` is made once by one person with sudo rights: `sudo bash install_shared.sh` from the course package.)

## Every session
- Write the code in the `.py` files (`bot.py`, `search.py` ...). The task card says which file and which function.
- Run everything in the VS Code terminal, from your folder, for example `python bot.py "When is Babbling Babies?"` and `python sessions/s1/check.py`
- Want to try things step by step? Make a notebook `scratch.ipynb` (Jupyter extension), pick the `.venv` kernel and use:
  ```python
  import importlib, bot
  importlib.reload(bot)      # run this after every change to bot.py, or the notebook keeps the old code
  bot.answer("When is Babbling Babies?")
  ```
- Your version does not pass the check of the last session? Take the golden state before you start the new session:
  `git checkout gold-s2 -- .` (use the number of the last session). This replaces the code files with the working version.
