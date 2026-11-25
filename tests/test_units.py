"""Unit tests: small pieces of the code, without the model.

Run:  python -m pytest tests/test_units.py
"""
from types import SimpleNamespace

import config
from app import as_text
from checks import check_answer, is_crisis, unknown_phone_numbers
from search import fuse, make_chunks, words

PASSAGES = [{"text": "Call North Family Hub on 01253 476480."}]


def good_answer(**changes):
    """An answer form that passes every rule; change one field to break one rule."""
    fields = dict(answer="Call 01253 476480.", found=True, sources=[1],
                  contains_advice=False, contains_personal_data=False)
    fields.update(changes)
    return SimpleNamespace(**fields)


# make_chunks
def test_heading_starts_a_new_passage():
    chunks = make_chunks("# One\n\nText one.\n\n# Two\n\nText two.")
    assert len(chunks) == 2
    assert chunks[1].startswith("# Two")


def test_no_passage_is_longer_than_the_limit():
    text = "\n".join(["A line of text that goes on."] * 100)
    assert all(len(chunk) <= 1000 for chunk in make_chunks(text, max_chars=1000))


def test_the_last_passage_is_kept():
    chunks = make_chunks("# One\n\nText one.\n\n# Two\n\nThe very end.")
    assert "The very end." in chunks[-1]


# fuse
def test_fuse_puts_the_best_first():
    assert fuse(["a", "b", "c"], ["a", "c", "b"])[0] == "a"


def test_fuse_uses_both_lists():
    assert fuse(["a", "b"], ["c", "b"])[0] == "b"


# words
def test_words_drops_stop_words_and_capitals():
    assert words("When is the Babbling Babies session?") == ["babbling", "babies", "session"]


# is_crisis
def test_crisis_in_capital_letters():
    assert is_crisis("I AM IN DANGER")


def test_normal_question_is_no_crisis():
    assert not is_crisis("When is Babbling Babies?")


# unknown_phone_numbers
def test_made_up_number_is_found():
    assert unknown_phone_numbers("Call 01253 999999.", PASSAGES) == ["01253 999999"]


def test_real_number_with_spaces_is_known():
    assert unknown_phone_numbers("Call 01253 476 480.", PASSAGES) == []


# check_answer
def test_good_answer_passes():
    assert check_answer(good_answer(), PASSAGES) is None


def test_answer_without_sources_is_blocked():
    assert check_answer(good_answer(sources=[]), PASSAGES) == config.FALLBACK_REPLY


def test_answer_with_personal_data_is_blocked():
    assert check_answer(good_answer(contains_personal_data=True), PASSAGES) == config.FALLBACK_REPLY


def test_answer_with_advice_is_blocked():
    assert check_answer(good_answer(contains_advice=True), PASSAGES) == config.FALLBACK_REPLY


# as_text
def test_as_text_joins_parts():
    assert as_text([{"type": "text", "text": "Hello"}, {"type": "text", "text": "there"}]) == "Hello there"


def test_as_text_plain_string():
    assert as_text("Hello") == "Hello"


# the web service
def test_empty_message_list_gives_400():
    from fastapi.testclient import TestClient
    import app
    response = TestClient(app.app).post("/v1/chat/completions", json={"messages": []})
    assert response.status_code == 400
