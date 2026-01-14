"""
Logging configuration for News Nexus Python applications.

This module provides centralized logging configuration using loguru.
All applications must call configure_logging() at startup.

Compliant with LOGGING_PYTHON_V06.md requirements.
"""

import os
import sys
from loguru import logger


def _fatal_error(message: str) -> None:
    """
    Log a fatal error to stderr and exit with non-zero code.

    Args:
        message: The error message to log
    """
    # Add a temporary stderr handler to ensure the error is logged
    logger.add(
        sys.stderr,
        format="{time:HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} | {message}",
        level="CRITICAL",
        colorize=False
    )
    logger.critical(message)
    sys.exit(1)


def _install_exception_handler():
    """
    Install sys.excepthook to catch and log all uncaught exceptions.

    This ensures that crashes are logged to file in production environments,
    preventing silent failures under systemd or PM2.
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        # Preserve KeyboardInterrupt (allow Ctrl+C)
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log all other uncaught exceptions at CRITICAL level
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).critical(
            "Uncaught exception - service crashed"
        )

    sys.excepthook = exception_handler


def configure_logging():
    """
    Configure loguru based on environment variables.
    Should be called once at application startup.

    Fatal errors (exits with non-zero code) if:
    - NAME_APP is missing or empty
    - RUN_ENVIRONMENT is missing, empty, or invalid
    - PATH_TO_LOGS is missing in testing/production

    Returns:
        logger: Configured loguru logger instance
    """
    # Remove default handler
    logger.remove()

    # Validate NAME_APP is set and not empty (required in all environments)
    app_name = os.getenv('NAME_APP')
    if not app_name or app_name.strip() == '':
        _fatal_error(
            "FATAL: NAME_APP environment variable is required and must not be empty. "
            "This ensures each process writes to its own unique log file. "
            "If spawning child processes, inject NAME_APP into the child's environment."
        )

    # Validate RUN_ENVIRONMENT is set and not empty (required in all environments)
    RUN_ENVIRONMENT = os.getenv('RUN_ENVIRONMENT')
    if not RUN_ENVIRONMENT or RUN_ENVIRONMENT.strip() == '':
        _fatal_error(
            "FATAL: RUN_ENVIRONMENT environment variable is required and must not be empty. "
            "Valid values: 'development', 'testing', 'production'"
        )

    # Validate RUN_ENVIRONMENT has valid value
    valid_environments = ['development', 'testing', 'production']
    if RUN_ENVIRONMENT not in valid_environments:
        _fatal_error(
            f"FATAL: Invalid RUN_ENVIRONMENT '{RUN_ENVIRONMENT}'. "
            f"Valid values: {', '.join(valid_environments)}"
        )

    if RUN_ENVIRONMENT == 'development':
        # Development: Console output only, DEBUG level
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment (console output, DEBUG level)")

    elif RUN_ENVIRONMENT == 'testing':
        # Testing: BOTH console and file output, INFO level

        # Validate PATH_TO_LOGS (required in testing)
        log_path = os.getenv('PATH_TO_LOGS')
        if not log_path or log_path.strip() == '':
            _fatal_error(
                "FATAL: PATH_TO_LOGS environment variable is required in testing environment"
            )

        log_max_size_mb = int(os.getenv('LOG_MAX_SIZE', '5'))  # 5 MB default
        log_max_size = log_max_size_mb * 1024 * 1024  # Convert MB to bytes for loguru
        log_max_files = int(os.getenv('LOG_MAX_FILES', '5'))

        # Ensure log directory exists
        try:
            os.makedirs(log_path, exist_ok=True)
        except Exception as e:
            _fatal_error(f"FATAL: Failed to create log directory '{log_path}': {e}")

        log_file = os.path.join(log_path, f"{app_name}.log")

        # Console output
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="INFO",
            colorize=True,
            backtrace=True,
            diagnose=True
        )

        # File output with rotation
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} | {message}",
            level="INFO",
            rotation=log_max_size,  # Rotate when file reaches max size
            retention=log_max_files,  # Keep max number of old logs
            compression="zip",  # Compress rotated logs
            enqueue=True,  # Thread/process-safe logging via queue
            backtrace=True,  # Enable exception tracing
            diagnose=True  # Enable variable values in exceptions
        )
        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment (console + file: {log_file}, INFO level)")

    elif RUN_ENVIRONMENT == 'production':
        # Production: File output only, INFO level

        # Validate PATH_TO_LOGS (required in production)
        log_path = os.getenv('PATH_TO_LOGS')
        if not log_path or log_path.strip() == '':
            _fatal_error(
                "FATAL: PATH_TO_LOGS environment variable is required in production environment"
            )

        log_max_size_mb = int(os.getenv('LOG_MAX_SIZE', '5'))  # 5 MB default
        log_max_size = log_max_size_mb * 1024 * 1024  # Convert MB to bytes for loguru
        log_max_files = int(os.getenv('LOG_MAX_FILES', '5'))

        # Ensure log directory exists
        try:
            os.makedirs(log_path, exist_ok=True)
        except Exception as e:
            _fatal_error(f"FATAL: Failed to create log directory '{log_path}': {e}")

        log_file = os.path.join(log_path, f"{app_name}.log")

        # File output only with rotation
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{function}:{line} | {message}",
            level="INFO",  # INFO and above in production
            rotation=log_max_size,  # Rotate when file reaches max size
            retention=log_max_files,  # Keep max number of old logs
            compression="zip",  # Compress rotated logs
            enqueue=True,  # Thread/process-safe logging via queue
            backtrace=True,  # Enable exception tracing
            diagnose=True  # Enable variable values in exceptions
        )
        logger.info(f"Logging configured for {RUN_ENVIRONMENT} environment (file: {log_file}, INFO level)")

    # Install uncaught exception handler (mandatory for all environments)
    _install_exception_handler()

    return logger
