"""
title: Family Hub assistant
description: Answers questions from the Blackpool Family Hub web pages, with sources.
version: 1.0
"""
# Open WebUI Pipe for the Family Hub assistant.
# Install: Admin Panel > Functions > + (New Function), paste this file, save and enable.
# The application code is loaded from APP_DIR inside the Open WebUI container (see deploy_openwebui.sh).
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
        """Import the application once, using the model URL from the valves."""
        if self.bot is None:
            sys.path.insert(0, self.valves.APP_DIR)
            import config
            config.MODEL_URL = self.valves.MODEL_URL     # must be set before importing bot
            import bot
            self.bot = bot
        return self.bot

    def pipe(self, body: dict, __task__=None) -> str:
        if __task__:                                     # background task (title, tags)
            return "Family Hub question"
        messages = [{"role": m["role"], "content": as_text(m.get("content"))}
                    for m in body.get("messages", []) if m.get("role") in ("user", "assistant")]
        question, history = messages[-1]["content"], messages[:-1]
        bot = self.load_bot()
        reply = bot.answer(question, history)
        if not history:
            reply = bot.config.HELP_NOTICE + "\n\n" + reply
        return reply


def as_text(content) -> str:
    """Normalise message content (string or list of parts) to plain text."""
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content or ""
