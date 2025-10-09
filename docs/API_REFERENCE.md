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
All responses are in JSON format. Successful responses return appropriate HTTP status codes (200, 201) with relevant data. Error responses return 4xx/5xx status codes with error details.

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

**Example:**
```bash
curl http://localhost:5000/deduper/jobs
```

### GET /deduper/jobs/{jobId}
Fetch detailed status, timestamps, and logs for a specific job.

**Parameters:**
- `jobId` (integer): The job ID to query

**Response (200 OK):**
```json
{
  "jobId": 1,
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
  "error": "Job not found"
}
```

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
  "error": "Cannot cancel job with status: completed"
}
```

**Response (404 Not Found):**
```json
{
  "error": "Job not found"
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
  "status": "unhealthy",
  "error": "Missing environment variables",
  "timestamp": "2025-09-28T17:45:30.123Z"
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
  "cleared": false,
  "cancelledJobs": [3, 5],
  "exitCode": 1,
  "stdout": "",
  "stderr": "Error clearing table...",
  "error": "Clear table command failed",
  "timestamp": "2025-09-28T17:45:30.123Z"
}
```

**Response (500 Internal Server Error - Timeout):**
```json
{
  "error": "Clear table command timed out",
  "cancelledJobs": [3, 5],
  "timestamp": "2025-09-28T17:45:30.123Z"
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
- Command executed: `{python_venv}/bin/python {deduper_path}/main.py analyze_fast`
- Output streams live to the Flask application terminal
- Jobs run asynchronously in background threads
- Child processes terminate when parent service stops

### Job ID Generation
- Job IDs are sequential integers starting from 1
- IDs reset when the service restarts
- Simple, human-readable format for easy reference

### Job Creation
- Each GET request to `/deduper/jobs` creates a new job
- No idempotency checks - each request creates a separate job
- Jobs are identified by sequential integer IDs

---

## Error Handling

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: New resource created successfully
- `400 Bad Request`: Invalid request format or parameters
- `404 Not Found`: Requested resource not found
- `500 Internal Server Error`: Server-side error

### Error Response Format
```json
{
  "error": "Description of the error"
}
```

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