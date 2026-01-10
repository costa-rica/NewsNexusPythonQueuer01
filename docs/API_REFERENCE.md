# API Reference - News Nexus Python Queuer 01

This document provides comprehensive documentation for all available API endpoints in the News Nexus Python Queuer service.

## Base URL
```
http://localhost:5000
```

## Content Type Requirements
POST and PUT requests with request bodies must include:
```
Content-Type: application/json
```

## Response Format
All responses are in JSON format. Successful responses return appropriate HTTP status codes (200, 201) with relevant data. Error responses return 4xx/5xx status codes with a standardized error structure containing a machine-readable error code, human-readable message, HTTP status, and optional details. See the [Error Handling](#error-handling) section for complete documentation.

---

## Index Endpoints

### GET /
Returns the main application page.

**Response:**
- Content-Type: `text/html`
- Returns HTML page with "News Nexus Python Queuer 01"

**Example:**
```bash
curl http://localhost:5000/
```

---

## Deduper Endpoints

All deduper endpoints are prefixed with `/deduper`.

### GET /deduper/jobs
Trigger a new deduper job to run the `analyze_fast` command.

**Response (201 Created):**
```json
{
  "jobId": 1,
  "status": "pending"
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": {
    "code": "JOB_CREATION_FAILED",
    "message": "Failed to create deduper job",
    "status": 500,
    "details": "ValueError: Invalid configuration"
  }
}
```

**Example:**
```bash
curl http://localhost:5000/deduper/jobs
```

### GET /deduper/jobs/reportId/{reportId}
Trigger a new deduper job for a specific report ID. This runs the `analyze_fast` command with the `--report-id` argument to process articles associated with a specific report.

**Parameters:**
- `reportId` (integer): The report ID to analyze

**Response (201 Created):**
```json
{
  "jobId": 1,
  "reportId": 84,
  "status": "pending"
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": {
    "code": "JOB_CREATION_FAILED",
    "message": "Failed to create deduper job for report ID 84",
    "status": 500,
    "details": "ValueError: NAME_CHILD_PROCESS_DEDUPER environment variable is required"
  }
}
```

**Example:**
```bash
curl http://localhost:5000/deduper/jobs/reportId/84
```

**Notes:**
- This endpoint is used to deduplicate articles for a specific report
- The command executed is: `{python_venv}/bin/python {deduper_path}/src/main.py analyze_fast --report-id {reportId}`
- Use this when you want to analyze only articles associated with a particular report instead of all articles

### GET /deduper/jobs/{jobId}
Fetch detailed status, timestamps, and logs for a specific job.

**Parameters:**
- `jobId` (integer): The job ID to query

**Response (200 OK):**
```json
{
  "jobId": 1,
  "reportId": 84,
  "status": "completed",
  "createdAt": "2025-09-28T17:45:30.123Z",
  "startedAt": "2025-09-28T17:45:30.456Z",
  "completedAt": "2025-09-28T17:46:15.789Z",
  "exitCode": 0,
  "stdout": "Process output streamed to terminal",
  "stderr": "Process errors streamed to terminal"
}
```

**Response (404 Not Found):**
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found",
    "status": 404
  }
}
```

**Response Fields:**
- `jobId`: The unique job identifier
- `reportId`: (optional) The report ID if the job was created for a specific report
- `status`: Current job status (see below)
- `createdAt`: ISO 8601 timestamp when job was created
- `startedAt`: ISO 8601 timestamp when job started running
- `completedAt`: ISO 8601 timestamp when job finished
- `exitCode`: Process exit code (0 = success, non-zero = error)
- `stdout`: Standard output message
- `stderr`: Standard error message

**Job Status Values:**
- `pending`: Job created but not yet started
- `running`: Job is currently executing
- `completed`: Job finished successfully (exit code 0)
- `failed`: Job finished with errors (non-zero exit code)
- `cancelled`: Job was manually terminated

**Example:**
```bash
curl http://localhost:5000/deduper/jobs/1
```

### POST /deduper/jobs/{jobId}/cancel
Terminate a running or pending job.

**Parameters:**
- `jobId` (integer): The job ID to cancel

**Response (200 OK):**
```json
{
  "jobId": 1,
  "status": "cancelled",
  "message": "Job cancelled successfully"
}
```

**Response (400 Bad Request):**
```json
{
  "error": {
    "code": "INVALID_JOB_STATE",
    "message": "Cannot cancel job with status: completed",
    "status": 400
  }
}
```

**Response (404 Not Found):**
```json
{
  "error": {
    "code": "JOB_NOT_FOUND",
    "message": "Job not found",
    "status": 404
  }
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": {
    "code": "JOB_CANCELLATION_FAILED",
    "message": "Failed to cancel job",
    "status": 500,
    "details": "Process termination failed"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/deduper/jobs/1/cancel
```

### GET /deduper/jobs/list
List all jobs.

**Response:**
```json
{
  "jobs": [
    {
      "jobId": 1,
      "status": "completed",
      "createdAt": "2025-09-28T17:45:30.123Z"
    },
    {
      "jobId": 2,
      "status": "running",
      "createdAt": "2025-09-28T17:50:15.456Z"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/deduper/jobs/list
```

### GET /deduper/health
Service health check and system status.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-28T17:45:30.123Z",
  "environment": {
    "deduper_path_configured": true,
    "python_venv_configured": true,
    "deduper_path_exists": true
  },
  "jobs": {
    "total": 5,
    "pending": 0,
    "running": 1,
    "completed": 3,
    "failed": 0,
    "cancelled": 1
  }
}
```

**Response (500 Internal Server Error):**
```json
{
  "error": {
    "code": "HEALTH_CHECK_FAILED",
    "message": "Health check failed",
    "status": 500,
    "details": "Missing environment variables"
  }
}
```

**Example:**
```bash
curl http://localhost:5000/deduper/health
```

### DELETE /deduper/clear-db-table
Cancel all running/pending deduper jobs and clear the database table used by the deduper microservice.

**Important:** This is a destructive operation that:
1. Immediately cancels ALL pending and running deduper jobs
2. Executes the `clear_table -y` command from NewsNexusDeduper02
3. Clears the ArticleDuplicateAnalysis table in the database

**Response (200 OK):**
```json
{
  "cleared": true,
  "cancelledJobs": [3, 5, 7],
  "exitCode": 0,
  "stdout": "Table cleared successfully...",
  "stderr": "",
  "timestamp": "2025-09-28T17:45:30.123Z"
}
```

**Response (500 Internal Server Error - Command Failed):**
```json
{
  "error": {
    "code": "CLEAR_TABLE_FAILED",
    "message": "Clear table command failed",
    "status": 500,
    "details": {
      "exitCode": 1,
      "cancelledJobs": [3, 5],
      "stdout": "",
      "stderr": "Error clearing table..."
    }
  }
}
```

**Response (500 Internal Server Error - Timeout):**
```json
{
  "error": {
    "code": "CLEAR_TABLE_TIMEOUT",
    "message": "Clear table command timed out after 60 seconds",
    "status": 500,
    "details": {
      "cancelledJobs": [3, 5]
    }
  }
}
```

**Response Fields:**
- `cleared`: Boolean indicating if the table was successfully cleared
- `cancelledJobs`: Array of job IDs that were cancelled before clearing
- `exitCode`: Exit code from the clear_table command
- `stdout`: Standard output from the clear_table command
- `stderr`: Standard error from the clear_table command
- `timestamp`: ISO 8601 timestamp of when the operation completed

**Example:**
```bash
curl -X DELETE http://localhost:5000/deduper/clear-db-table
```

**Notes:**
- This operation runs synchronously (not queued)
- Has a 60-second timeout for safety
- The `-y` flag bypasses the microservice's confirmation prompt
- All active jobs are cancelled before the table is cleared
- Use with caution - this removes all deduplication analysis data

---

## Environment Configuration

The service requires these environment variables (configured in `.env`):

- `PATH_TO_PYTHON_VENV`: Path to Python virtual environment
- `PATH_TO_MICROSERVICE_DEDUPER`: Path to NewsNexusDeduper02 microservice

---

## Job Processing Details

### Deduper Job Execution
- Jobs run the `analyze_fast` command from NewsNexusDeduper02
- Default command: `{python_venv}/bin/python {deduper_path}/src/main.py analyze_fast`
- Report-specific command: `{python_venv}/bin/python {deduper_path}/src/main.py analyze_fast --report-id {reportId}`
- Output streams live to the Flask application terminal
- Jobs run asynchronously in background threads
- Child processes terminate when parent service stops

### Job Types
1. **General Deduplication** (`GET /deduper/jobs`)
   - Processes all available articles
   - No report filtering

2. **Report-Specific Deduplication** (`GET /deduper/jobs/reportId/{reportId}`)
   - Processes only articles associated with the specified report ID
   - Useful for targeted analysis of specific reports

### Job ID Generation
- Job IDs are sequential integers starting from 1
- IDs reset when the service restarts
- Simple, human-readable format for easy reference

### Job Creation
- Each GET request to `/deduper/jobs` or `/deduper/jobs/reportId/{reportId}` creates a new job
- No idempotency checks - each request creates a separate job
- Jobs are identified by sequential integer IDs
- Report-specific jobs store the `reportId` in job metadata for reference

---

## Error Handling

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: New resource created successfully
- `400 Bad Request`: Invalid request format or parameters
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side error

### Error Response Format
All errors follow a consistent structure with machine-readable error codes:

```json
{
  "error": {
    "code": "ERROR_CODE_HERE",
    "message": "Human-readable error message",
    "status": 500
  }
}
```

With optional details for debugging (sanitized in production):
```json
{
  "error": {
    "code": "JOB_CREATION_FAILED",
    "message": "Failed to create deduper job",
    "status": 500,
    "details": "ValueError: Invalid configuration"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `JOB_NOT_FOUND` | 404 | The requested job does not exist |
| `INVALID_JOB_STATE` | 400 | Job is in an invalid state for the requested operation |
| `JOB_CREATION_FAILED` | 500 | Failed to create a new job |
| `JOB_CANCELLATION_FAILED` | 500 | Failed to cancel the job |
| `MISSING_CONFIGURATION` | 500 | Required environment variables are missing |
| `CLEAR_TABLE_FAILED` | 500 | Clear table command failed |
| `CLEAR_TABLE_TIMEOUT` | 500 | Clear table command timed out |
| `HEALTH_CHECK_FAILED` | 500 | Health check encountered an error |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Integration Notes

### ExpressJS Integration
This API is designed to be called from NewsNexusAPI09 (ExpressJS application):
- All endpoints accept JSON payloads
- RESTful design follows standard conventions
- Error responses include descriptive messages
- Async job processing allows non-blocking requests

### PM2 Logging
- Job output streams to terminal for visibility under `pm2 logs`
- Job start/completion events are logged
- Process lifecycle events are captured