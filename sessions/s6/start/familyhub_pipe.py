"""
title: Family Hub assistant
description: Answers questions from the Blackpool Family Hub web pages, with sources.
version: 1.0
"""
# Session 6: the Family Hub assistant inside Open WebUI, as a Pipe.
# Paste this file in Open WebUI: Admin Panel > Functions > + (New Function), save, and switch it on.
# The code itself (bot.py, search.py ...) lives in APP_DIR inside the Open WebUI container.
import sys

from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        APP_DIR: str = Field(default="/app/backend/data/familyhub-app",
                             description="Folder with the Family Hub code and knowledge")
        MODEL_URL: str = Field(default="http://host.docker.internal:8004/v1",
                               description="Address of the AI model, as seen from the Open WebUI container")

    def __init__(self):
        self.valves = self.Valves()
        self.bot = None

    def pipes(self) -> list[dict]:
        return [{"id": "family-hub", "name": "Family Hub assistant"}]

    def load_bot(self):
        """Import our code once, with the model address from the valves."""
        if self.bot is None:
            sys.path.insert(0, self.valves.APP_DIR)
            import config
            config.MODEL_URL = self.valves.MODEL_URL     # must be set before bot.py creates its model client
            import bot
            self.bot = bot
        return self.bot

    def pipe(self, body: dict, __task__=None) -> str:
        """Open WebUI calls this for every message.
        1. If __task__ is set (Open WebUI wants a chat title, tags ...), return "Family Hub question".
        2. Take the user and assistant messages from body["messages"] (use as_text for the content).
        3. The last message is the question, the ones before it are the history.
        4. bot = self.load_bot(); reply = bot.answer(question, history)
        5. If there is no history (the first message), put bot.config.HELP_NOTICE above the reply."""
        # TODO
        return ""


def as_text(content) -> str:
    """Open WebUI sends text as a string, or as a list of parts."""
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content or ""
