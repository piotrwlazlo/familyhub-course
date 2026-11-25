"""Session 8: unit tests. Each test checks one small piece of our code, without the model, in a split second.

Run from your main folder:  python -m pytest tests/test_units.py
A test is a function whose name starts with test_. Inside it: call our code, then assert what must be true.
"""
from checks import is_crisis


# An example: one rule, one test. The name says what must be true.
def test_crisis_words_are_found():
    assert is_crisis("I am in danger at home right now")


# Write your own tests below (see the task card for what to test).
