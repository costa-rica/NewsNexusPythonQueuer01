from flask import Flask
import logging

# to relative (works when importing src.app)
from .routes.index import bp_index
from .routes.deduper import bp_deduper
from .config.logging import configure_logging

# load .env file -> needed for prod (Ubuntu/pm2 setup)
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# project root = one level above src/
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging calls and redirect them to loguru.
    This allows Flask and werkzeug logs to be captured by loguru.
    """
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


def create_app():
    # Configure loguru BEFORE creating Flask app
    configure_logging()

    app = Flask(__name__)

    # Replace Flask's logger handlers with InterceptHandler
    app.logger.handlers = [InterceptHandler()]
    app.logger.setLevel(logging.DEBUG)  # Let loguru filter by level

    # Also intercept werkzeug logger (Flask's development server)
    logging.getLogger('werkzeug').handlers = [InterceptHandler()]
    logging.getLogger('werkzeug').setLevel(logging.DEBUG)  # Let loguru filter by level

    # Register blueprints
    app.register_blueprint(bp_index)
    app.register_blueprint(bp_deduper)

    logger.info("Flask application created successfully")

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)