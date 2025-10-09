# News Nexus Python Queuer 01

This is the first version of the News Nexus Python Queuer. It is a simple program that will queue up Python micro services on the News Nexus platform.

## Project Structure

```
src/
├── app.py              # Flask app initialization
└── routes/             # Route blueprints
    ├── deduper.py      # Deduper job management
    └── index.py        # Basic routes
```

## API

Routes see the docs [API Reference](docs/API_REFERENCE.md)

- set off a job use GET `http://127.0.0.1:5000/deduper/jobs`

## Queues

Each route ( and therefore microservice) has its own queue.

## .env

```
PATH_TO_PYTHON_VENV=/Users/nick/Documents/_environments/news_nexus
PATH_TO_MICROSERVICE_DEDUPER=/Users/nick/Documents/NewsNexusDeduper02
PATH_TO_MICROSERVICE_LOCATION_SCORER=/Users/nick/Documents/NewsNexusClassifierLocationScorer01
```

## References

- [API Reference](docs/API_REFERENCE.md)
- [Overview of News Nexus 09](docs/NEWS_NEXUS_09.md)
- [Database schema and relationships](docs/DATABASE_OVERVIEW.md)
