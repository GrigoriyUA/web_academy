import os
import sys
import json
import logging
import structlog
from structlog.stdlib import ProcessorFormatter

_json_dumps = lambda obj, **kw: json.dumps(obj, ensure_ascii=False, **kw)


def setup_logging(log_file: str = "app.log") -> None:
    env = os.getenv("APP_ENV", "development")

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=shared_processors + [
            ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if env == "production":
        console_formatter = ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )
    else:
        console_formatter = ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
        )

    file_formatter = ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(serializer=_json_dumps),
    )

    # sys.stdout вже reconfigure(encoding="utf-8") в agent.py
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(file_formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(console_handler)
    root.addHandler(file_handler)
    root.setLevel(logging.DEBUG if env == "development" else logging.INFO)

    # Заглушуємо spam від httpx / httpcore / groq внутрішніх логерів
    for noisy in ("httpx", "httpcore", "groq._base_client"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
