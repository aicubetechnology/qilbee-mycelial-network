"""
Structured logging configuration for QMN services.

Provides JSON-formatted structured logging with tenant_id, trace_id,
and service context in every log line.
"""

import logging
import os
import sys

import structlog


def configure_logging(service_name: str, log_level: str = "INFO"):
    """
    Configure structured JSON logging for a QMN service.

    Args:
        service_name: Name of the service (e.g., "router", "reinforcement")
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR)
    """
    log_level_num = getattr(logging, log_level.upper(), logging.INFO)

    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    # Use JSON rendering for production, console for dev
    use_json = os.getenv("QMN_LOG_FORMAT", "json") == "json"

    if use_json:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level_num)

    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    return structlog.get_logger(service=service_name)


def bind_context(**kwargs):
    """Bind context variables for structured logging (tenant_id, trace_id, etc.)."""
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context():
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()
