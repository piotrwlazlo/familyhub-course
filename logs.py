"""Logging: coloured lines in the terminal, the main log file and a separate file for the model's reasoning.

Use it anywhere:  from loguru import logger
                  logger.info("..."), logger.warning("..."), logger.error("..."), logger.exception("...")
"""
import sys
import uuid

from loguru import logger

import config

TERMINAL_FORMAT = ("<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                   "<cyan>{extra[request_id]}</cyan> | <level>{message}</level>")
FILE_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[request_id]} | {message}"

our_outputs = []      # the outputs added by setup_logging


def is_reasoning(record) -> bool:
    """True for lines written with logger.bind(reasoning=True)."""
    return "reasoning" in record["extra"]


def not_reasoning(record) -> bool:
    return not is_reasoning(record)


def new_request_id() -> str:
    """A short id that ties together all log lines of one question."""
    return uuid.uuid4().hex[:8]


def setup_logging() -> None:
    """Terminal (coloured), logs/familyhub.log (rotated) and logs/reasoning.log (reasoning lines only)."""
    for output in our_outputs:                 # running it again does not double the lines
        logger.remove(output)
    our_outputs.clear()
    try:
        logger.remove(0)                       # loguru's own default output
    except ValueError:
        pass
    logger.configure(extra={"request_id": "-"})

    our_outputs.append(logger.add(sys.stderr, level=config.LOG_LEVEL, format=TERMINAL_FORMAT,
                                  colorize=True, filter=not_reasoning))
    our_outputs.append(logger.add(config.LOG_DIR / "familyhub.log", level=config.LOG_LEVEL, format=FILE_FORMAT,
                                  filter=not_reasoning, rotation="10 MB", retention="14 days", encoding="utf-8"))
    our_outputs.append(logger.add(config.LOG_DIR / "reasoning.log", level="DEBUG", format=FILE_FORMAT,
                                  filter=is_reasoning, retention="3 days", encoding="utf-8"))


def log_reasoning(step: str, message) -> None:
    """Write what the model returned for one step to logs/reasoning.log: its reasoning (if the model gives one)
    and the form it filled in."""
    reasoning = getattr(message, "reasoning_content", None) or getattr(message, "reasoning", None)
    logger.bind(reasoning=True).debug("{} | reasoning: {} | form: {}", step,
                                      reasoning or "(the model returned no reasoning)", message.content)
