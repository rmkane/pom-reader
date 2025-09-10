"""Logging configuration for POM Reader."""

import logging
import logging.handlers
from pathlib import Path
from typing import Any


def setup_logging(
    level: str = "INFO",
    log_dir: str | Path | None = None,
    app_name: str = "pom-reader",
) -> logging.Logger:
    """
    Set up logging with rolling daily logs.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files. Defaults to ~/.local/logs/{app_name}/
        app_name: Application name for log directory structure

    Returns:
        Configured logger instance
    """
    # Determine log directory
    if log_dir is None:
        home_dir = Path.home()
        log_dir = home_dir / ".local" / "logs" / app_name
    else:
        log_dir = Path(log_dir)

    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Set up logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
    )

    # Console handler (stderr)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(
        logging.WARNING
    )  # Only show warnings and errors on console
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)

    # File handler for all logs (daily rolling)
    log_file = log_dir / f"{app_name}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Error file handler (errors only)
    error_log_file = log_dir / f"{app_name}-errors.log"
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=error_log_file,
        when="midnight",
        interval=1,
        backupCount=90,  # Keep 90 days of error logs
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # Log the setup
    logger.info("Logging initialized - Level: %s", level.upper())
    logger.info("Log directory: %s", log_dir)
    logger.info("Log files: %s, %s", log_file.name, error_log_file.name)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"pom-reader.{name}")


# Convenience function for common logging patterns
def log_function_call(logger: logging.Logger, func_name: str, **kwargs: Any) -> None:
    """Log function call with parameters."""
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug("Calling %s(%s)", func_name, params)


def log_parsing_result(logger: logging.Logger, element_type: str, count: int) -> None:
    """Log parsing results."""
    logger.info("Parsed %d %s(s)", count, element_type)


def log_error_with_context(
    logger: logging.Logger, error: Exception, context: str
) -> None:
    """Log error with additional context."""
    logger.error(
        "Error in %s: %s: %s", context, type(error).__name__, error, exc_info=True
    )
