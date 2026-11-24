# Session 4: The assistant checks its answer

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** the council's rules are kept by plain Python code, not only by asking the model nicely. Crisis words always give the 999 reply. Every answer needs a source, no advice, no personal data and no made-up phone numbers.

**You start from** the session 3 version (if yours does not pass its check, ask the instructor for the working version).

**You get**
- `sessions/s4/start/checks.py`: copy to the main folder. Ready: the phone number pattern `PHONE` and `digits()`

**You build**

| Where | What |
|---|---|
| `checks.py`: `CRISIS_WORDS` and `is_crisis(question)` | A list of words that mean someone is in danger now, and a check for them |
| `checks.py`: `unknown_phone_numbers(answer, passages)` | Phone numbers in the answer that are not in any passage |
| `checks.py`: `check_answer(result, passages)` | Returns our fallback reply if a rule is broken, otherwise `None` |
| `bot.py`: the `Answer` form | Two more fields: `contains_advice` and `contains_personal_data` (yes/no, with descriptions) |
| `bot.py`: `answer(question)` | `is_crisis` before anything else; `check_answer` after `write_answer` |

## Steps
1. Write your own list of crisis words. How would a frightened person really write it?
2. Write `is_crisis` and `unknown_phone_numbers`. Try them in Python with your own sentences.
3. Write `check_answer`, add the two fields to the `Answer` form, add both checks to `answer`.
4. Try to break the assistant: ask for medical advice, give it your name and address, tell it to ignore its rules. Write down what gets through.
5. Run the check: `python sessions/s4/check.py`, then the checks of sessions 1, 2 and 3.

## Prompts for the AI assistant
- *"Write a Python function is_crisis(question) that returns True if the lower-case question contains any word or phrase from the list CRISIS_WORDS."*
- *"Write unknown_phone_numbers(answer, passages): find phone numbers in answer with the regex PHONE, and return those whose digits do not appear in the digits of all passage texts joined together. Use the function digits(text)."*

**Done when** `python sessions/s4/check.py` prints `SESSION DONE` (4 rules and 10 tricky questions), and the checks of sessions 1 to 3 still pass.

## Hints
- A crisis word that is too short (like "hit") also blocks normal questions ("Is there a hit song session?"). Keep the phrases specific.
- Rules must not block good answers: the last question in the check is a normal one on purpose.

## Try at the end
- Which rule fired? Add a `print` in `check_answer` and ask the tricky questions again.
