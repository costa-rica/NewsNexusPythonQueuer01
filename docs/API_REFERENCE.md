# API Reference - News Nexus Python Queuer 01

This document provides comprehensive documentation for all available API endpoints in the News Nexus Python Queuer service.

## Base URL
```
http://localhost:5000
```

## Content Type Requirements
All POST, PUT, and PATCH requests must include:
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

### POST /deduper/jobs
Enqueue a new deduper job to run the `analyze_fast` command.

**Request Body:**
```json
{
  "reportId": "123",  // Optional: for tracking and idempotency
  "embeddingThresholdMinimum": 0.8  // Optional: not used by deduper but stored for reference
}
```

**Response (201 Created):**
```json
{
  "jobId": 1,
  "status": "pending"
}
```

**Response (200 OK - Existing Job):**
```json
{
  "jobId": 1,
  "status": "running",
  "message": "Job already exists for this reportId"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/deduper/jobs \
  -H "Content-Type: application/json" \
  -d '{"reportId": "123"}'
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
  "stderr": "Process errors streamed to terminal",
  "reportId": "123"
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
curl -X POST http://localhost:5000/deduper/jobs/1/cancel \
  -H "Content-Type: application/json"
```

### GET /deduper/jobs
List jobs with optional filtering by reportId.

**Query Parameters:**
- `reportId` (optional): Filter jobs by report ID

**Response - All Jobs:**
```json
{
  "jobs": [
    {
      "jobId": 1,
      "status": "completed",
      "createdAt": "2025-09-28T17:45:30.123Z",
      "reportId": "123"
    },
    {
      "jobId": 2,
      "status": "running",
      "createdAt": "2025-09-28T17:50:15.456Z",
      "reportId": "124"
    }
  ]
}
```

**Response - Filtered by reportId:**
```json
{
  "jobs": [
    {
      "jobId": 1,
      "status": "completed",
      "createdAt": "2025-09-28T17:45:30.123Z",
      "reportId": "123"
    }
  ]
}
```

**Examples:**
```bash
# Get all jobs
curl http://localhost:5000/deduper/jobs

# Get jobs for specific reportId
curl http://localhost:5000/deduper/jobs?reportId=123
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

### Idempotency
- Providing the same `reportId` prevents duplicate job creation
- If a job with the same `reportId` is pending or running, the existing job details are returned
- Completed, failed, or cancelled jobs allow new jobs with the same `reportId`

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