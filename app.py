import os
from flask import Flask
from models import setup_db
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    db = setup_db(app)
    CORS(app)
    Migrate(app, db)

    @app.route('/')
    def get_greeting():
        return "hi there"

    return app

app = create_app()


if __name__ == '__main__':
    app.run()
