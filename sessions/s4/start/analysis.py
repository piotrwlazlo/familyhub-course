"""Session 4: before answering, the model fills in a short form about the question.

Try it:  python analysis.py "What's the weather in London?"
"""
import json
import sys
from typing import Literal

from openai import OpenAI
from pydantic import BaseModel, Field

import config

client = OpenAI(base_url=config.MODEL_URL, api_key="not-needed")


class QuestionAnalysis(BaseModel):
    # TODO: four fields, each with Field(description="...")
    #   on_topic      bool
    #   is_crisis     bool
    #   kind          Literal["time", "place", "contact", "description", "other"]
    #   search_query  str
    pass


PROMPT = """You analyse questions sent to the Family Hub information assistant of the council.
Fill in the form about the user's last question. Do not answer the question.

Reply with JSON that matches this schema (read the description of every field):
{schema}"""


def analyse(question: str) -> QuestionAnalysis | None:
    """Ask the model to fill in the form. Returns None if the model did not return a valid form.
    Use client.chat.completions.parse(..., response_format=QuestionAnalysis, temperature=0)
    and a system message PROMPT.format(schema=json.dumps(QuestionAnalysis.model_json_schema()))."""
    # TODO
    return None


if __name__ == "__main__":
    print(analyse(" ".join(sys.argv[1:]) or "What's the weather in London?"))
