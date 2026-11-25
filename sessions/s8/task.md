# Session 8: Tests before every release

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** the assistant gets the tests a production service needs. **Unit tests** check small pieces of our own code without the model, in a split second, on every change. A **smoke test** checks the running service in a few seconds, right after it is started or deployed. On the way you find and fix a real bug in the web service.

**You start from** the session 7 version (if yours does not pass its check, ask the instructor for the working version). The hunt needs the working versions of `search.py`, `checks.py` and `app.py`.

**Before you start (once, the instructor):** install pytest into the Python environment the team uses: `pip install pytest`

**You get**
- `sessions/s8/start/test_units.py`: copy to `tests/`. It has one example test.
- `sessions/s8/start/smoke_test.py`: copy to `tests/`. It has the first of four checks.
- `sessions/s8/hunt.py`: a quick quality check of your unit tests (ready, you only run it)

**How a test looks**
```python
from checks import is_crisis

def test_crisis_words_are_found():                     # the name starts with test_ and says what must be true
    assert is_crisis("I am in danger at home right now")   # assert: this must be True, or the test fails
```
Run all tests: `python -m pytest tests/test_units.py` (green dots = pass, `F` = fail).

**You build**
- `tests/test_units.py`: at least 8 unit tests. What the functions must do:

| Function (file) | Rules to test |
|---|---|
| `make_chunks(text, max_chars)` (`search.py`) | a heading (`# ...`) starts a new passage; no passage is longer than `max_chars`; the last passage of the text is kept |
| `fuse(list1, list2)` (`search.py`) | an id that is high in both lists comes first; both lists count, not only the first |
| `words(text)` (`search.py`) | lower case words, without stop words like *the*, *is*, *when* |
| `is_crisis(question)` (`checks.py`) | finds crisis words, also in CAPITAL letters; a normal question is no crisis |
| `unknown_phone_numbers(answer, passages)` (`checks.py`) | a made-up number is reported; a real number is not, also when written with different spaces |
| `check_answer(result, passages)` (`checks.py`) | a good answer passes (`None`); no sources, advice or personal data gives `config.FALLBACK_REPLY` |
| `as_text(content)` (`app.py`) | a plain text stays the same; a message sent in parts (`[{"type": "text", "text": "Hello"}, ...]`) becomes one text |

- `app.py`: `chat()` answers 400 for an empty message list (today it crashes)
- `tests/smoke_test.py`: four checks against the running service: health, model list, one real question, empty message list

## Steps
1. Copy the starter files: `cp sessions/s8/start/test_units.py sessions/s8/start/smoke_test.py tests/` and run the unit tests: `python -m pytest tests/test_units.py` (1 passed).
2. Write unit tests for `is_crisis`, `unknown_phone_numbers` and `check_answer`: these are our safety rules. For `check_answer` you need an answer form: `bot.Answer(answer="Call 01253 476480.", found=True, sources=[1], contains_advice=False, contains_personal_data=False)`. Change one field per test. Run pytest after each new test.
3. Write unit tests for `make_chunks` and `fuse`. Write the small texts and lists yourself, e.g. `fuse(["a", "b"], ["c", "b"])`.
4. Quick quality check: `python sessions/s8/hunt.py`. If a line says **SURVIVES**, add a test for that rule.
5. **Find a real bug:** add this test. It fails today, because the service crashes on an empty message list. Then fix `chat()` in `app.py` so it answers with status 400 instead, and run pytest again.
   ```python
   from fastapi.testclient import TestClient
   import app

   def test_empty_message_list_gives_400():
       response = TestClient(app.app).post("/v1/chat/completions", json={"messages": []})
       assert response.status_code == 400
   ```
6. **Smoke test:** complete the three TODO checks in `tests/smoke_test.py`. Start your service (`.venv/bin/uvicorn app:app --port <your port>`) and in a second terminal run `python tests/smoke_test.py http://localhost:<your port>`. Stop the service, run the smoke test again: what do you see?
7. Run the check: `python sessions/s8/check.py` (it starts the service by itself), then the check of session 7.

## Prompts for the AI assistant
- *"Write pytest tests for this Python function. One test per rule, each test name says the rule, for example test_heading_starts_a_new_passage. Use small inputs that I can read. Rules: <paste the rules from the table>. Function: <paste the function>."*
- *"This broken version of the function survives my tests: <paste the line from the hunt>. Which test would pass on the correct code and fail on this mistake?"*
- *"Complete this smoke test with httpx: GET URL/v1/models must list a model with id 'family-hub-assistant'; POST URL/v1/chat/completions with one user message must answer with status 200 and contain '01253 476480' in choices[0].message.content; POST with an empty messages list must give status 400. Use the function check(name, ok) for each."*
- *"In this FastAPI function chat(), if the list messages is empty, return JSONResponse with an error message and status_code 400 before messages[-1] is used."*

**Done when** `python sessions/s8/check.py` prints `SESSION DONE`: at least 8 unit tests, 6 of 6 broken versions caught, the empty message list gets 400, and your smoke test passes against the running service.

## Hints
- `ModuleNotFoundError: No module named 'checks'`: run pytest from your main folder, with `python -m pytest ...` (not just `pytest`).
- A test fails on the real code? Read the message under the red `F`: pytest shows the values on both sides of the `assert`. Maybe your expectation is wrong, maybe you found a bug: ask.
- The hunt says SKIP: that file is not the working version. Ask your instructor for it.
- Smoke test: `ConnectError` means the service is not running on that port.
- Good tests are small: one rule, one test, a clear name. When it fails, the name tells you what broke.
- Unit tests never call the model: they must be fast and give the same result every time.

## Try at the end
- Break something on purpose in your own `checks.py` (for example remove `.lower()`), run pytest, see which test goes red, then undo it with `git checkout checks.py`.
- Time it: how long do the unit tests take, the smoke test, and `python tests/run_tests.py`? That is why unit tests run on every change, the smoke test after every deploy, and the golden questions before a release.
