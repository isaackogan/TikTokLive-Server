import logging

logger: logging.Logger = logging.getLogger("uvicorn.error")


def get_logger() -> logging.Logger:
    return logger
