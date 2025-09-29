from flask import Flask
from routes.index import index_bp

def create_app():
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(index_bp)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)