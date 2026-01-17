"""
Logger Utility.

This module provides logging configuration using Python's logging module
and rich for colored console output.
"""

import logging
import sys
from pathlib import Path

from rich.logging import RichHandler


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance with both file and console handlers.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Don't configure if already configured
    if logger.handlers:
        return logger

    # Set level
    logger.setLevel(logging.DEBUG)

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create formatters
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create file handler (DEBUG and above)
    file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Create console handler with Rich (INFO and above)
    console_handler = RichHandler(
        console=None,  # Use default console
        show_time=False,  # Time already in format
        show_path=False,  # Don't show full path
        enable_link_path=False,
        markup=True,  # Enable rich markup
        rich_tracebacks=True,  # Rich tracebacks
        tracebacks_word_wrap=True,
        tracebacks_extra_lines=3,
        tracebacks_theme="monokai",
        tracebacks_show_locals=True
    )
    console_handler.setLevel(logging.INFO)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent duplicate messages from parent loggers
    logger.propagate = False

    return logger


def setup_global_logging(level: str = "INFO"):
    """
    Set up global logging configuration for the entire application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # File handler for all logs
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler with Rich
    console_handler = RichHandler(
        console=None,
        show_time=False,
        show_path=False,
        enable_link_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_word_wrap=True,
        tracebacks_extra_lines=3,
        tracebacks_theme="monokai",
        tracebacks_show_locals=False  # Less verbose for global logging
    )
    console_handler.setLevel(numeric_level)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log the setup
    root_logger.info(f"Global logging configured with level: {level}")


def get_workflow_logger(workflow_id: str) -> logging.Logger:
    """
    Get a logger specifically for workflow execution.

    Args:
        workflow_id: Unique workflow identifier

    Returns:
        Configured workflow logger
    """
    return get_logger(f"workflow.{workflow_id}")


def get_agent_logger(agent_name: str) -> logging.Logger:
    """
    Get a logger specifically for agent execution.

    Args:
        agent_name: Name of the agent

    Returns:
        Configured agent logger
    """
    return get_logger(f"agent.{agent_name}")


# Convenience functions for different log levels
def log_workflow_start(workflow_id: str, config: dict = None):
    """Log the start of a workflow execution."""
    logger = get_workflow_logger(workflow_id)
    logger.info(f"Starting workflow execution (ID: {workflow_id})")
    if config:
        logger.debug(f"Workflow config: {config}")


def log_workflow_complete(workflow_id: str, duration: float = None, errors: int = 0):
    """Log the completion of a workflow execution."""
    logger = get_workflow_logger(workflow_id)
    status = "completed" if errors == 0 else f"completed with {errors} errors"
    message = f"Workflow {status}"
    if duration:
        message += f" in {duration:.2f}s"

    if errors == 0:
        logger.info(message)
    else:
        logger.warning(message)


def log_agent_execution(agent_name: str, status: str, duration: float = None, error: str = None):
    """Log agent execution results."""
    logger = get_agent_logger(agent_name)

    message = f"Agent {agent_name} {status}"
    if duration:
        message += f" in {duration:.2f}s"

    if status == "failed" and error:
        logger.error(f"{message}: {error}")
    elif status == "completed":
        logger.info(message)
    else:
        logger.debug(message)