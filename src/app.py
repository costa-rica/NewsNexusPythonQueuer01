from flask import Flask
# to relative (works when importing src.app)
from .routes.index import bp_index
from .routes.deduper import bp_deduper

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(bp_index)
    app.register_blueprint(bp_deduper)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)