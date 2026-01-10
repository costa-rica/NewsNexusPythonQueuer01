"""
Logging configuration for News Nexus Python applications.

This module provides centralized logging configuration using loguru.
All applications must call configure_logging() at startup.
"""

import os
import sys
from loguru import logger


def configure_logging():
    """
    Configure loguru based on environment variables.
    Should be called once at application startup.

    Raises:
        ValueError: If required environment variables are missing or invalid

    Returns:
        logger: Configured loguru logger instance
    """
    # Remove default handler
    logger.remove()

    # Validate NAME_APP is set and not empty
    app_name = os.getenv('NAME_APP')
    if not app_name or app_name.strip() == '':
        raise ValueError(
            "NAME_APP environment variable is required and must not be empty. "
            "This ensures each process writes to its own unique log file. "
            "If spawning child processes, inject NAME_APP into the child's environment."
        )

    # Validate RUN_ENVIRONMENT is set and not empty
    RUN_ENVIRONMENT = os.getenv('RUN_ENVIRONMENT')
    if not RUN_ENVIRONMENT or RUN_ENVIRONMENT.strip() == '':
        raise ValueError(
            "RUN_ENVIRONMENT environment variable is required and must not be empty. "
            "Valid values: 'development', 'testing', 'production'"
        )

    if RUN_ENVIRONMENT == 'development':
        # Development: Console logging with colors and all log levels
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment (console output, DEBUG level)")

    elif RUN_ENVIRONMENT == 'testing':
        # Testing: File-based logging with all log levels (mirrors production structure)
        log_path = os.getenv('PATH_TO_LOGS')
        log_max_size_mb = int(os.getenv('LOG_MAX_SIZE', '5'))  # 5 MB default
        log_max_size = log_max_size_mb * 1024 * 1024  # Convert MB to bytes for loguru
        log_max_files = int(os.getenv('LOG_MAX_FILES', '5'))

        if not log_path:
            raise ValueError("PATH_TO_LOGS environment variable is required in testing environment")

        # Ensure log directory exists
        os.makedirs(log_path, exist_ok=True)

        log_file = os.path.join(log_path, f"{app_name}.log")

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="DEBUG",  # All log levels for testing
            rotation=log_max_size,  # Rotate when file reaches max size
            retention=log_max_files,  # Keep max number of old logs
            compression="zip",  # Compress rotated logs
            enqueue=True,  # Thread/process-safe logging via queue
            backtrace=True,  # Enable exception tracing
            diagnose=True  # Enable variable values in exceptions
        )
        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment (file: {log_file}, DEBUG level)")

    elif RUN_ENVIRONMENT == 'production':
        # Production: File-based logging with ERROR level only
        log_path = os.getenv('PATH_TO_LOGS')
        log_max_size_mb = int(os.getenv('LOG_MAX_SIZE', '5'))  # 5 MB default
        log_max_size = log_max_size_mb * 1024 * 1024  # Convert MB to bytes for loguru
        log_max_files = int(os.getenv('LOG_MAX_FILES', '5'))

        if not log_path:
            raise ValueError("PATH_TO_LOGS environment variable is required in production environment")

        # Ensure log directory exists
        os.makedirs(log_path, exist_ok=True)

        log_file = os.path.join(log_path, f"{app_name}.log")

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",  # Only ERROR and CRITICAL in production
            rotation=log_max_size,  # Rotate when file reaches max size
            retention=log_max_files,  # Keep max number of old logs
            compression="zip",  # Compress rotated logs
            enqueue=True,  # Thread/process-safe logging via queue
            backtrace=True,  # Enable exception tracing
            diagnose=True  # Enable variable values in exceptions
        )
        logger.error(f"Logging configured for {RUN_ENVIRONMENT} environment (file: {log_file}, ERROR level)")

    else:
        # Unknown environment - default to development behavior with warning
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )
        logger.warning(f"Unknown RUN_ENVIRONMENT '{RUN_ENVIRONMENT}' - defaulting to development mode")

    return logger
