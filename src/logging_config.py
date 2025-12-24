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

    Environment Variables:
        NAME_APP (required): Application name for log file naming
        RUN_ENVIRONMENT (optional): Environment mode ('production' or 'development', defaults to 'development')
        PATH_TO_LOGS (required in production): Directory for log files
        LOG_MAX_SIZE (optional): Max log file size in bytes (default: 10485760 = 10 MB)
        LOG_MAX_FILES (optional): Max number of rotated log files (default: 10)

    Raises:
        ValueError: If NAME_APP is missing, empty, or required production variables are missing

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

    RUN_ENVIRONMENT = os.getenv('RUN_ENVIRONMENT', 'development')

    if RUN_ENVIRONMENT == 'production':
        # Production: File-based logging with rotation
        log_path = os.getenv('PATH_TO_LOGS')
        log_max_size = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10 MB default
        log_max_files = int(os.getenv('LOG_MAX_FILES', '10'))

        if not log_path:
            raise ValueError("PATH_TO_LOGS environment variable is required in production")

        # Ensure log directory exists
        os.makedirs(log_path, exist_ok=True)

        log_file = os.path.join(log_path, f"{app_name}.log")

        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO",
            rotation=log_max_size,  # Rotate when file reaches max size
            retention=log_max_files,  # Keep max number of old logs
            compression="zip",  # Compress rotated logs
            enqueue=True,  # Thread/process-safe logging via queue
            backtrace=True,  # Enable exception tracing
            diagnose=True  # Enable variable values in exceptions
        )

        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment: {log_file}")
    else:
        # Development: Console logging with colors
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True
        )

        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment (console output)")

    return logger
