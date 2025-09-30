from flask import Flask
# to relative (works when importing src.app)
from .routes.index import bp_index
from .routes.deduper import bp_deduper

# load .env file -> needed for prod (Ubuntu/pm2 setup)
from pathlib import Path
from dotenv import load_dotenv

# project root = one level above src/
BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(bp_index)
    app.register_blueprint(bp_deduper)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)