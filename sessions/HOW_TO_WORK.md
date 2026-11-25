# How to work: VS Code on the GB10

Everyone works in their own folder on the GB10, in VS Code (connected to the GB10 the same way as in the earlier labs). Nobody works in someone else's folder, and nobody changes anything that is shared by the team.

## Your own folder
The instructor made one folder per person in the team folder `aidevteam`: `familyhub-<your name>`. It is a `git clone` of the course repository, with your own changes in it.
- In VS Code: File > Open Folder > `aidevteam/familyhub-<your name>`
- Run everything in the VS Code terminal, from that folder, with the Python environment you used in sessions 1 to 6.

## New sessions
The instructor adds the files of each new session (`sessions/sN/`) to every folder. This changes only the `sessions/` folder: your own code stays as it is.

## Every session
- Write the code in the `.py` files (`bot.py`, `search.py` ...). The task card says which file and which function.
- Run everything from your folder, for example `python bot.py "When is Babbling Babies?"` and `python sessions/s7/check.py`
- When you start a service for yourself, use your own port (ask the instructor which one): `uvicorn app:app --port <your port>`
- Want to try things step by step? Make a notebook `scratch.ipynb` (Jupyter extension) and use:
  ```python
  import importlib, bot
  importlib.reload(bot)      # run this after every change to bot.py, or the notebook keeps the old code
  bot.answer("When is Babbling Babies?")
  ```

## Starting session 7 (and later sessions)
1. Run the check of the last session, for example `python sessions/s6/check.py`
2. It prints `SESSION DONE`: go on with your own code.
3. It does not: put your changes aside and take the working version of session 6:
   ```bash
   git stash -u
   git fetch --tags
   git checkout -b work gold-s6
   ```
   Your old changes are not lost: `git stash list` shows them.
4. For sessions 8 and 9: if the check of the session before does not pass, ask the instructor for the working version.

## Never in your own folder
- `bash deploy_openwebui.sh`: it replaces the Family Hub assistant in Open WebUI for the whole team. Only the instructor deploys, from the instructor's folder, with a version that passes all checks.
- Changes to shared things: the Open WebUI container, the model containers, other people's folders.
