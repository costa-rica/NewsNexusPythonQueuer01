"""
Error response utilities for consistent API error formatting.

Implements the standard error response format defined in docs/ERROR_REQUIREMENTS.md
"""

import os
from flask import jsonify


def error_response(code, message, status, details=None):
    """
    Create a standardized error response following News Nexus error format.

    Args:
        code (str): Machine-readable error code (e.g., 'JOB_NOT_FOUND', 'INTERNAL_ERROR')
        message (str): Human-readable error message for display to users
        status (int): HTTP status code (e.g., 404, 500)
        details (str|dict|list, optional): Additional context for debugging.
                                          Sanitized based on RUN_ENVIRONMENT.

    Returns:
        tuple: (Flask JSON response, HTTP status code)

    Example:
        return error_response(
            code='JOB_NOT_FOUND',
            message='Job not found',
            status=404
        )
    """
    # Sanitize details based on environment
    run_environment = os.getenv('RUN_ENVIRONMENT', 'development')

    # In production, omit details unless explicitly safe to expose
    if run_environment == 'production' and details is not None:
        # Only include details if it's a structured error (dict/list), not exception messages
        if not isinstance(details, (dict, list)):
            details = None

    error_body = {
        "error": {
            "code": code,
            "message": message,
            "status": status
        }
    }

    # Only add details key if details is not None
    if details is not None:
        error_body["error"]["details"] = details

    return jsonify(error_body), status
