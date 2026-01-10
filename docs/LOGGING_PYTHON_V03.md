# Python Logging Requirements for News Nexus Applications (V03)

## Overview

This document specifies logging requirements for all Python applications in the News Nexus ecosystem using the [loguru](https://github.com/Delgan/loguru) package. The configuration ensures consistent, production-ready logging across Flask apps, FastAPI apps, and standalone Python scripts.

**Key Requirements:**

- Logging configuration must be placed in `src/config/logging.py` (for projects with `src/` directory) or `config/logging.py` (for projects without `src/` directory)
- All required environment variables must be set; missing variables trigger fatal errors at application startup
- Each microservice/process must have a unique `NAME_APP` to ensure separate log files

## Environment Variables

### Required Variables

**IMPORTANT**: Missing required environment variables will trigger a fatal error (ValueError) at microservice startup, preventing the application from running. This ensures proper configuration before any processing begins.

| Variable          | Description                                                     | Example                   | Fatal Error if Missing |
| ----------------- | --------------------------------------------------------------- | ------------------------- | ---------------------- |
| `NAME_APP`        | Application name used in log filenames                          | `NewsNexusPythonQueuer01` | Yes (all environments) |
| `RUN_ENVIRONMENT` | Environment mode (`development`, `testing`, or `production`)    | `production`              | Yes (all environments) |
| `PATH_TO_LOGS`    | Directory path for log file storage (testing & production only) | `/var/log/newsnexus`      | Yes (testing/production only) |

### Optional Variables

| Variable        | Default | Description                                                                                                                                               |
| --------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LOG_MAX_SIZE`  | `5`     | Maximum size of each log file before rotation. Specify value in megabytes (e.g., `5` = 5MB). Logger implementation converts to bytes internally.         |
| `LOG_MAX_FILES` | `5`     | Number of rotated log files to retain                                                                                                                     |

## Log File Naming Convention

**Format**: `{NAME_APP}.log`

**Rotation**: `{NAME_APP}.{number}.log` (e.g., `NewsNexusPythonQueuer01.1.log`, `NewsNexusPythonQueuer01.2.log`)

**Full Path Example**: `/var/log/newsnexus/NewsNexusPythonQueuer01.log`

## Configuration Requirements

### Development Environment (`RUN_ENVIRONMENT=development`)

- **Output**: Console/terminal (stdout/stderr) with colorized output
- **Level**: `DEBUG` (all log levels)
- **Format**: Simplified format optimized for readability
- **Rotation**: Not applicable
- **Use Case**: Local development, debugging, interactive testing

### Testing Environment (`RUN_ENVIRONMENT=testing`)

- **Output**: File-based logging in `PATH_TO_LOGS` directory
- **Level**: `DEBUG` (all log levels)
- **Rotation**: Size-based rotation using `LOG_MAX_SIZE` and `LOG_MAX_FILES`
- **Format**: Structured format with timestamp, level, module, and message
- **Process Safety**: Enable `enqueue=True` for thread/process-safe logging
- **Child Process Handling**: Environment Injection - each process writes to its own log file
- **Use Case**: Automated testing, CI/CD pipelines, pre-production validation

### Production Environment (`RUN_ENVIRONMENT=production`)

- **Output**: File-based logging in `PATH_TO_LOGS` directory
- **Level**: `ERROR` (only ERROR and CRITICAL messages)
- **Rotation**: Size-based rotation using `LOG_MAX_SIZE` and `LOG_MAX_FILES`
- **Format**: Structured format with timestamp, level, module, and message
- **Process Safety**: Enable `enqueue=True` for thread/process-safe logging
- **Child Process Handling**: Environment Injection - each process writes to its own log file
- **Use Case**: Production deployment, minimal logging overhead

## Loguru Configuration

### File Structure and Placement

The logging configuration must be placed in a dedicated configuration file named `logging.py`:

**File Placement Rules:**

- **Projects with `src/` directory**: Place logging configuration in `src/config/logging.py`
- **Projects without `src/` directory**: Place logging configuration in `config/logging.py`

**Example Project Structures:**

```
# Project with src/ directory
my-microservice/
├── src/
│   ├── config/
│   │   └── logging.py          ← Logging configuration here
│   ├── main.py
│   └── modules/
│       └── ...
├── .env
└── requirements.txt

# Project without src/ directory
my-microservice/
├── config/
│   └── logging.py              ← Logging configuration here
├── main.py
├── .env
└── requirements.txt
```

**Import Examples:**

```python
# From main.py in project WITH src/ directory
from config.logging import configure_logging

# From main.py in project WITHOUT src/ directory
from config.logging import configure_logging

# From modules in subdirectories (adjust path as needed)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.logging import configure_logging
```

### Base Configuration Function

```python
import os
import sys
from loguru import logger

def configure_logging():
    """
    Configure loguru based on environment variables.
    Should be called once at application startup.

    Raises:
        ValueError: If required environment variables are missing or invalid
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
```

## Framework-Specific Integration

### Flask Applications

```python
from flask import Flask
from loguru import logger
import logging
from config.logging import configure_logging

def create_app():
    app = Flask(__name__)

    # Configure loguru
    configure_logging()

    # Intercept Flask's default logger
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # Replace Flask's logger handlers
    app.logger.handlers = [InterceptHandler()]
    app.logger.setLevel(logging.DEBUG)  # Let loguru filter by level

    # Also intercept werkzeug logger (Flask's server)
    logging.getLogger('werkzeug').handlers = [InterceptHandler()]
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)  # Let loguru filter by level

    return app
```

### FastAPI Applications

```python
from fastapi import FastAPI
from loguru import logger
import logging
from config.logging import configure_logging

def create_app():
    app = FastAPI()

    # Configure loguru
    configure_logging()

    # Intercept uvicorn loggers
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # Replace uvicorn and fastapi loggers
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("fastapi").handlers = [InterceptHandler()]

    # Set to DEBUG to allow loguru to filter by level
    logging.getLogger("uvicorn").setLevel(logging.DEBUG)
    logging.getLogger("uvicorn.access").setLevel(logging.DEBUG)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)

    return app
```

### Standalone Python Scripts

```python
#!/usr/bin/env python3
from loguru import logger
from config.logging import configure_logging

def main():
    # Configure logging at script start
    configure_logging()

    logger.info("Script started")

    try:
        # Your script logic here
        logger.debug("Processing data...")
        # ...
    except Exception as e:
        logger.exception("Script failed with error")
        raise
    finally:
        logger.info("Script completed")

if __name__ == "__main__":
    main()
```

## Parent/Child Process Logging

### Environment Injection Strategy

All processes (parent and child) must write to their own unique log files. When spawning a child process, the parent **must inject** a unique `NAME_APP` into the child's environment variables. This ensures the child's call to `configure_logging()` generates a distinct log file rather than attempting to write to the parent's file.

**Key Principles:**

1. Each microservice/process has its own log file identified by `NAME_APP`
2. Multiple instances of the same microservice can safely write to the same log file (loguru's `enqueue=True` handles concurrent writes)
3. Parent processes inject `NAME_APP` when spawning child processes
4. If `NAME_APP` is missing or empty, `configure_logging()` will raise an error to alert engineers
5. Child processes inherit `RUN_ENVIRONMENT` from parent unless explicitly overridden

### Log File Separation

Example log file distribution:

- `NewsNexusPythonQueuer01.log` - Flask queuer service (parent)
- `NewsNexusDeduper02.log` - Deduper microservice (child process)
- `NewsNexusClassifierLocationScorer01.log` - Location scorer microservice (child process)

Multiple deduper jobs spawned simultaneously will all write to `NewsNexusDeduper02.log` safely.

### Implementation: Spawning Child Processes

When spawning child processes via `subprocess`, inject the child's `NAME_APP` into its environment using environment variables with the naming pattern `NAME_CHILD_PROCESS_` + [Descriptor].

**Environment Variable Pattern:**

Define child process names in the parent's `.env` file:
```bash
NAME_CHILD_PROCESS_SEMANTIC_SCORER=NewsNexusSemanticScorer02
NAME_CHILD_PROCESS_DEDUPER=NewsNexusDeduper02
NAME_CHILD_PROCESS_LOCATION_SCORER=NewsNexusClassifierLocationScorer01
```

**Implementation:**

```python
import subprocess
import os
from loguru import logger

def run_deduper_job(job_id):
    """Spawn deduper microservice with its own NAME_APP."""
    logger.info(f"Starting deduper job {job_id}")

    # Get deduper path from environment
    deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
    python_venv = os.getenv('PATH_TO_PYTHON_VENV')

    # Build command
    cmd = [
        f"{python_venv}/bin/python",
        f"{deduper_path}/src/main.py",
        "analyze_fast"
    ]

    # CRITICAL: Get child process NAME_APP from environment variable
    child_process_name = os.getenv('NAME_CHILD_PROCESS_DEDUPER')
    if not child_process_name:
        raise ValueError("NAME_CHILD_PROCESS_DEDUPER environment variable is required")

    # Copy parent's environment and inject child's NAME_APP
    child_env = os.environ.copy()
    child_env['NAME_APP'] = child_process_name

    # Spawn process with injected environment
    process = subprocess.Popen(
        cmd,
        env=child_env,  # Use modified environment
        text=True
    )

    # Wait for completion
    exit_code = process.wait()
    logger.info(f"Deduper job {job_id} completed with exit code {exit_code}")

    return exit_code
```

**Key Points:**

- Parent process defines `NAME_CHILD_PROCESS_*` variables in its `.env` file
- Each child process type has a corresponding environment variable (e.g., `NAME_CHILD_PROCESS_DEDUPER`, `NAME_CHILD_PROCESS_SEMANTIC_SCORER`)
- The value from the parent's environment variable is passed to the child's `NAME_APP`
- This ensures centralized configuration and prevents hardcoding child process names

### Real-World Example

```python
import subprocess
import os
from loguru import logger

def spawn_microservice(env_var_name, script_path, args=None):
    """
    Generic function to spawn microservices with proper NAME_APP injection.

    Args:
        env_var_name: Environment variable name containing child process NAME_APP
                      (e.g., 'NAME_CHILD_PROCESS_DEDUPER')
        script_path: Path to the microservice script
        args: Optional list of command-line arguments
    """
    python_venv = os.getenv('PATH_TO_PYTHON_VENV')

    # Get child process name from environment variable
    child_process_name = os.getenv(env_var_name)
    if not child_process_name:
        raise ValueError(f"{env_var_name} environment variable is required")

    cmd = [f"{python_venv}/bin/python", script_path]
    if args:
        cmd.extend(args)

    # Inject NAME_APP for the child process
    child_env = os.environ.copy()
    child_env['NAME_APP'] = child_process_name

    logger.info(f"Spawning {child_process_name} with command: {' '.join(cmd)}")

    process = subprocess.Popen(cmd, env=child_env, text=True)
    return process

# Usage examples
deduper_path = os.getenv('PATH_TO_MICROSERVICE_DEDUPER')
deduper_process = spawn_microservice(
    env_var_name='NAME_CHILD_PROCESS_DEDUPER',
    script_path=f"{deduper_path}/src/main.py",
    args=['analyze_fast', '--report-id', '12345']
)

scorer_path = os.getenv('PATH_TO_MICROSERVICE_LOCATION_SCORER')
scorer_process = spawn_microservice(
    env_var_name='NAME_CHILD_PROCESS_LOCATION_SCORER',
    script_path=f"{scorer_path}/src/main.py",
    args=['score', '--batch-id', '67890']
)
```

### Error Handling

#### Required Environment Variable Errors

All missing required environment variables trigger fatal errors (ValueError) at application startup, preventing the microservice from running with incorrect configuration.

**Missing NAME_APP:**
```
ValueError: NAME_APP environment variable is required and must not be empty.
This ensures each process writes to its own unique log file.
If spawning child processes, inject NAME_APP into the child's environment.
```

**Missing RUN_ENVIRONMENT:**
```
ValueError: RUN_ENVIRONMENT environment variable is required and must not be empty.
Valid values: 'development', 'testing', 'production'
```

**Missing PATH_TO_LOGS (in testing/production):**
```
ValueError: PATH_TO_LOGS environment variable is required in testing environment
```
or
```
ValueError: PATH_TO_LOGS environment variable is required in production environment
```

These intentional failures ensure engineers are alerted to properly configure the environment before the application processes any data.

## Implementation Checklist

- [ ] Install loguru: `pip install loguru`
- [ ] Create `config/` directory in project root (or `src/config/` if project has `src/` directory)
- [ ] Create `logging.py` file in `config/` (or `src/config/`) with `configure_logging()` function
- [ ] Add **required** environment variables to `.env` (`NAME_APP`, `RUN_ENVIRONMENT`, `PATH_TO_LOGS`)
  - Note: Missing required variables will cause fatal error at startup
- [ ] Add optional environment variables to `.env` (`LOG_MAX_SIZE`, `LOG_MAX_FILES`)
- [ ] Add child process name environment variables using pattern `NAME_CHILD_PROCESS_*` (e.g., `NAME_CHILD_PROCESS_DEDUPER=NewsNexusDeduper02`)
- [ ] Set `RUN_ENVIRONMENT` to `development`, `testing`, or `production` (no other values accepted)
- [ ] Update Flask apps to import and integrate loguru with InterceptHandler
- [ ] Update FastAPI apps to import and integrate loguru with InterceptHandler
- [ ] Update standalone scripts to import and call `configure_logging()` at startup
- [ ] Update subprocess spawning code to read `NAME_CHILD_PROCESS_*` environment variables and inject as child's `NAME_APP`
- [ ] Verify each microservice has its own unique `NAME_APP` configured
- [ ] Test that missing/empty `NAME_APP` raises fatal error (ValueError) at startup
- [ ] Test that missing/empty `RUN_ENVIRONMENT` raises fatal error (ValueError) at startup
- [ ] Test that missing `PATH_TO_LOGS` raises fatal error in testing/production environments
- [ ] Test that missing `NAME_CHILD_PROCESS_*` variable raises clear error when spawning child processes
- [ ] Test development mode uses console logging with all log levels
- [ ] Test testing mode writes all log levels to files with rotation
- [ ] Test production mode writes only ERROR and CRITICAL to files
- [ ] Test log rotation by generating logs exceeding `LOG_MAX_SIZE` (specified in MB)
- [ ] Verify log files are created in `PATH_TO_LOGS` directory with correct names
- [ ] Verify multiple instances of same microservice can write to same log file
- [ ] Ensure PM2 can read logs (check file permissions)

## Log Levels

Use appropriate log levels following these guidelines:

| Level      | Usage                                                       | Development | Testing | Production |
| ---------- | ----------------------------------------------------------- | ----------- | ------- | ---------- |
| `DEBUG`    | Detailed debugging information                              | ✓           | ✓       | ✗          |
| `INFO`     | General informational messages (requests, job status, etc.) | ✓           | ✓       | ✗          |
| `WARNING`  | Warning messages (deprecated features, recoverable errors)  | ✓           | ✓       | ✗          |
| `ERROR`    | Error messages (exceptions, failed operations)              | ✓           | ✓       | ✓          |
| `CRITICAL` | Critical errors (service failures, data corruption)         | ✓           | ✓       | ✓          |

## Example Log Output

### Development Format (Console)

```
14:23:45.123 | DEBUG    | src.routes.deduper:process_data:23 | Validating input parameters
14:23:45.456 | INFO     | src.routes.deduper:create_job:45 | Creating deduper job for report ID 12345
14:23:45.789 | INFO     | src.routes.deduper:create_job:67 | Job 42 enqueued successfully
14:23:46.012 | WARNING  | src.utils.cache:get_cached:89 | Cache miss for key 'report_12345'
14:24:12.345 | ERROR    | src.routes.deduper:check_job_status:156 | Job 42 failed with exit code 1
```

### Testing Format (File - All Levels)

```
2025-12-29 14:23:45.123 | DEBUG    | src.routes.deduper:process_data:23 | Validating input parameters
2025-12-29 14:23:45.456 | INFO     | src.routes.deduper:create_job:45 | Creating deduper job for report ID 12345
2025-12-29 14:23:45.789 | INFO     | src.routes.deduper:create_job:67 | Job 42 enqueued successfully
2025-12-29 14:23:46.012 | WARNING  | src.utils.cache:get_cached:89 | Cache miss for key 'report_12345'
2025-12-29 14:24:12.345 | ERROR    | src.routes.deduper:check_job_status:156 | Job 42 failed with exit code 1
```

### Production Format (File - Errors Only)

```
2025-12-29 14:24:12.345 | ERROR    | src.routes.deduper:check_job_status:156 | Job 42 failed with exit code 1
2025-12-29 14:25:03.678 | CRITICAL | src.database.connection:reconnect:234 | Database connection lost after 3 retry attempts
```

## Environment Comparison

| Feature           | Development       | Testing                  | Production            |
| ----------------- | ----------------- | ------------------------ | --------------------- |
| Output Target     | Console (stderr)  | File                     | File                  |
| Log Level         | DEBUG (all)       | DEBUG (all)              | ERROR (errors only)   |
| Colorized Output  | Yes               | No                       | No                    |
| File Rotation     | N/A               | Yes                      | Yes                   |
| File Compression  | N/A               | Yes (zip)                | Yes (zip)             |
| Process Safety    | N/A               | Yes (enqueue=True)       | Yes (enqueue=True)    |
| PATH_TO_LOGS Req. | No                | Yes                      | Yes                   |
| Use Case          | Local development | Automated testing, CI/CD | Production deployment |
