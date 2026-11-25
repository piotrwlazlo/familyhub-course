# Session 6: The assistant lives in Open WebUI

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** staff use the assistant in the chat window they already know. It remembers the conversation, so follow-up questions like *"And where is it?"* work.

**You start from** the session 5 version (if yours does not pass its check, ask the instructor for the working version).

**You get**
- `sessions/s6/start/familyhub_pipe.py`: copy to the main folder. Ready: the settings (`Valves`), `pipes`, `load_bot`, `as_text`
- `sessions/s6/start/config_addition.py`: the notice shown above the first answer; paste into `config.py`
- `deploy_openwebui.sh`: INSTRUCTOR ONLY. It copies the team's version into the shared Open WebUI container. You do not run it: it would replace the assistant for everyone

**You build**

| Where | What |
|---|---|
| `analysis.py`: `analyse(question, history)` | Also sends the last 6 messages, so the model can turn *"And where is it?"* into a full question |
| `bot.py`: `write_answer(question, passages, history)` and `answer(question, history)` | Pass the history on to the model |
| `familyhub_pipe.py`: `pipe(body)` | Takes the conversation from Open WebUI, calls `bot.answer`, adds the notice to the first answer |

## Steps
1. Add `history` to `analyse`, `write_answer` and `answer` (default `None`, so all older checks still work).
2. Try a follow-up in Python: `bot.answer("And at South Family Hub?", [{"role": "user", "content": "When is Babbling Babies at North Family Hub?"}, {"role": "assistant", "content": "Thursday 10am to 11am."}])`
3. Write `pipe`. Run the check: `python sessions/s6/check.py`
4. The instructor puts the team's version into Open WebUI (`bash deploy_openwebui.sh --instructor`, from the instructor's folder). You do not run this script yourself.
5. In Open WebUI: Admin Panel > Functions > **+**, paste all of `familyhub_pipe.py`, save, switch it on. Pick **Family Hub assistant** as the model in a new chat.
6. Have three conversations with follow-ups. Then ask colleagues to try it and write down what they think.

## Prompts for the AI assistant
- *"Complete pipe(self, body, __task__=None) for an Open WebUI Pipe: if __task__ is set return 'Family Hub question'. Build a list of {'role', 'content'} from body['messages'] with role user or assistant, using as_text for the content. The last one is the question, the rest is the history. Call self.load_bot().answer(question, history). If the history is empty, put bot.config.HELP_NOTICE and a blank line before the reply."*

**Done when** `python sessions/s6/check.py` prints `SESSION DONE` (3 conversations with follow-ups) and the assistant answers in Open WebUI.

## Hints
- Inside the container, the model is not at `localhost`: the Pipe uses `host.docker.internal` (see `Valves`).
- You changed the code? Test it in your own folder (the check, or your own service on your own port). The instructor decides when the team's version in Open WebUI is updated.
- Run `python tests/run_tests.py` one more time: the score must not drop.
