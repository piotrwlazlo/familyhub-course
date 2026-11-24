# Session 4: The assistant understands the question

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** before answering, the model fills in a short form about the question. Our code reads the form and decides: off topic and crisis questions get our fixed replies, the rest goes on to the answer.

**You start from** the session 3 version (if yours does not pass its check, ask the instructor for the working version).

**You get**
- `config.py`: now also has our fixed replies `OFF_TOPIC_REPLY`, `CRISIS_REPLY`, `FALLBACK_REPLY` (copy the new part from `sessions/s4/start/config_addition.py` to the end of your `config.py`)
- `sessions/s4/start/analysis.py`: copy it to the main folder: `cp sessions/s4/start/analysis.py .`

**You build**

| Where | What |
|---|---|
| `analysis.py`: class `QuestionAnalysis` | The form, with four fields: `on_topic` (yes/no), `is_crisis` (yes/no), `kind` (one of time, place, contact, description, other), `search_query` (the question rewritten as a full question) |
| `analysis.py`: `analyse(question)` | Asks the model to fill in the form; returns the form, or `None` if the model's reply was not a valid form |
| `bot.py`: `answer(question)` | Rename your old `answer` to `ask_model`. The new `answer` calls `analyse` first and returns a fixed reply for: no form, crisis, off topic. Otherwise it returns `ask_model(question)` |

## Steps
1. Write the class `QuestionAnalysis` with Pydantic. Give every field a `description`: the model reads them.
2. Write `analyse`. Try it: `python analysis.py "What's the weather in London?"` Look at the form.
3. Try 5 questions of your own. Is every field what you expect?
4. Change `answer` in `bot.py`. Try an off topic question with `python bot.py ...`
5. Run the check: `python sessions/s4/check.py`, then the old one: `python sessions/s3/check.py`

## Prompts for the AI assistant
- *"Write a Pydantic model QuestionAnalysis with the fields on_topic (bool), is_crisis (bool), kind (Literal of time, place, contact, description, other) and search_query (str). Give each field a Field(description=...) that explains it for a family hub assistant."*
- *"Write a function analyse(question) that calls client.chat.completions.parse with model=config.MODEL, temperature=0, response_format=QuestionAnalysis and a system message PROMPT.format(schema=json.dumps(QuestionAnalysis.model_json_schema())). Return response.choices[0].message.parsed, or None if anything fails."*

**Done when** `python sessions/s4/check.py` prints `SESSION DONE` (12 of 12) and the session 3 check still passes.

## Hints
- The model gets a field wrong again and again: does it see the field descriptions? The schema must be in the prompt, not only in `response_format`.
- `kind` is wrong: describe it with the question words (when, where, phone ...), and say that spelling mistakes are common.
- Do not add more fields than these four. More fields = more mistakes.

## Try at the end (the bridge to session 5)
- Look at `search_query` for *"wen is the clever money drop in"*. It is a clean question now, but we still cannot search all 116 pages. That is next.
