# News Nexus Python Queuer 01

This is the first version of the News Nexus Python Queuer. It is a simple program that will queue up Python micro services on the News Nexus platform.

## .env

```
PATH_TO_PYTHON_VENV=/Users/nick/Documents/_environments/news_nexus
PATH_TO_MICROSERVICE_DEDUPER=/Users/nick/Documents/NewsNexusDeduper02
PATH_TO_MICROSERVICE_LOCATION_SCORER=/Users/nick/Documents/NewsNexusClassifierLocationScorer01
```

## References

- [Overview of News Nexus 09](docs/NEWS_NEXUS_09.md)
- [Database schema and relationships](docs/DATABASE_OVERVIEW.md)

## TODO

- Implement Flask application structure with code in `src/`
- Use Flask blueprints and configure logging for visibility under `pm2 logs`
- Add a `deduper` blueprint with endpoints:
  - `POST /jobs/deduper` to enqueue a deduper job and return `{ jobId, status }`
  - `GET /jobs/:id` to fetch job status, timestamps, and logs
  - `POST /jobs/:id/cancel` to terminate a running job
  - `GET /jobs?reportId=123` to check for existing jobs (idempotency)
  - `GET /health` for service health check
- Add an `index` blueprint with `GET /` returning a simple HTML page: "News Nexus Python Queuer 01"
- Manage deduper jobs asynchronously with `subprocess`, capturing exit codes and allowing polling
- Keep modular structure: `src/app.py` for app initialization, routes under `src/routes/`
