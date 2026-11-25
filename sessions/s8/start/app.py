"""Session 8: the Family Hub assistant as a small web service (OpenAI-compatible API), with a health check.

Start:       .venv/bin/uvicorn app:app --port <your port>      (your instructor gives you a port, e.g. 8101)
Try it:      curl localhost:<your port>/health
The model the assistant uses: config.MODEL_URL, or the environment variables FAMILYHUB_MODEL_URL and FAMILYHUB_MODEL.
"""
import json
import os
import time

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel

import config

config.MODEL_URL = os.environ.get("FAMILYHUB_MODEL_URL", config.MODEL_URL)   # must be set before importing bot
config.MODEL = os.environ.get("FAMILYHUB_MODEL", config.MODEL)
import bot  # noqa: E402
import search  # noqa: E402

APP_MODEL_NAME = "family-hub-assistant"      # model id exposed to clients
app = FastAPI()


class ChatRequest(BaseModel):
    model: str = APP_MODEL_NAME
    messages: list[dict]
    stream: bool = False


def as_text(content) -> str:
    """Normalise message content (string or list of parts) to plain text."""
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content or ""


@app.get("/health")
def health():
    """Is the assistant ready? Answers 200 with {"status": "ok", "model": true, "index": true},
    or 503 with "status": "error" and the part that failed (false)."""
    # TODO: checks = {"model": model_ok(), "index": <the search index has passages: search.collection.count() > 0>}
    #       if a check failed: logger.error(...) with the checks
    #       return JSONResponse({...}, status_code=200 or 503)
    return JSONResponse({"status": "not built yet"}, status_code=503)


def model_ok() -> bool:
    """True if the model server answers. Ask it for its list of models (no answer is generated):
    bot.client.with_options(timeout=3, max_retries=0).models.list(). Any error means False."""
    # TODO
    return False


@app.get("/v1/models")
def models():
    return {"object": "list", "data": [{"id": APP_MODEL_NAME, "object": "model", "created": 0, "owned_by": "familyhub"}]}


@app.post("/v1/chat/completions")
def chat(request: ChatRequest):
    messages = [{"role": m["role"], "content": as_text(m.get("content"))}
                for m in request.messages if m.get("role") in ("user", "assistant")]
    question, history = messages[-1]["content"], messages[:-1]
    if question.lstrip().startswith("### Task:"):          # Open WebUI background task (title, tags)
        text = "Family Hub question"
    else:
        text = bot.answer(question, history)
        if not history:
            text = config.HELP_NOTICE + "\n\n" + text
    if request.stream:
        return StreamingResponse(stream(text), media_type="text/event-stream")
    return {"id": "familyhub", "object": "chat.completion", "created": int(time.time()), "model": APP_MODEL_NAME,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}]}


def stream(text: str):
    """Emit the complete answer as a single SSE chunk followed by the end marker."""
    for delta, finish in (({"role": "assistant", "content": text}, None), ({}, "stop")):
        chunk = {"id": "familyhub", "object": "chat.completion.chunk", "created": int(time.time()),
                 "model": APP_MODEL_NAME, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"
