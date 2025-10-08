# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NewsNexusPythonQueuer01 is a Flask application that queues Python microservices for the News Nexus platform. It serves as the orchestration layer for running AI analysis tools like deduplication and location scoring on news articles collected from various sources.

## Architecture

### Core System Components
- **NewsNexusDb09**: TypeScript/SQLite database with Sequelize ORM containing articles, users, reports, and analysis results
- **NewsNexusPythonQueuer01**: This Flask queuing service (Python)
- **NewsNexusDeduper02**: Python microservice for article deduplication
- **NewsNexusClassifierLocationScorer01**: Python microservice for US location classification

### Environment Configuration
The application uses these environment variables from `.env`:
- `PATH_TO_PYTHON_VENV`: Python virtual environment path
- `PATH_TO_MICROSERVICE_DEDUPER`: Path to deduper microservice
- `PATH_TO_MICROSERVICE_LOCATION_SCORER`: Path to location scorer microservice

## Development Setup

### Python Environment
Use the virtual environment specified in `.env`:
```bash
source $PATH_TO_PYTHON_VENV/bin/activate
```

### Project Structure
```
src/
├── app.py              # Flask app initialization
└── routes/             # Route blueprints
    ├── deduper.py      # Deduper job management
    └── index.py        # Basic routes
```

### Flask Blueprints
1. **Deduper Blueprint** (`/deduper`):
   - `GET /deduper/jobs` - Create and enqueue deduper job, return `{ jobId, status }`
   - `GET /deduper/jobs/:id` - Fetch job status, timestamps, logs
   - `POST /deduper/jobs/:id/cancel` - Terminate running job
   - `GET /deduper/jobs/list` - List all jobs
   - `GET /deduper/health` - Health check with environment and job statistics

2. **Index Blueprint**:
   - `GET /` - Return HTML: "News Nexus Python Queuer 01"

### Job Management Implementation
- Uses `subprocess` for asynchronous job execution in background threads
- Captures exit codes and provides status polling via job ID
- Supports job cancellation (terminate/kill processes)
- Output streams to terminal for PM2 logging visibility (`pm2 logs`)
- In-memory job storage with sequential integer IDs (resets on service restart)
- Jobs run the `analyze_fast` command from NewsNexusDeduper02

## Database Integration

### Key Models (from NewsNexusDb09)
- **Article**: Core news article storage with metadata
- **ArticleDuplicateAnalysis**: Deduplication comparison results
- **Report**: Client report generation tracking
- **User**: System users for workflows

### Analysis Pipeline
1. Articles collected by various NewsNexus*Requester* tools
2. Queued through this service for Python analysis
3. **NewsNexusDeduper02**: Removes duplicate articles
4. **NewsNexusClassifierLocationScorer01**: Scores US location relevance
5. Results stored back in NewsNexusDb09

## Production Environment
- Deployed on Ubuntu VM behind reverse proxy
- Managed by PM2 process manager
- All News Nexus applications run on same server
- SQLite database shared across applications

## Key Development Practices
- Use Flask blueprints for modular routes
- Configure logging for PM2 visibility
- Implement proper error handling and job status tracking
- Follow existing News Nexus naming conventions
- Ensure idempotent job creation via reportId checking