import os
from flask import Flask
from flask import abort
from models import setup_db
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv

from error import setup_error_handlers
from error import success
from error import failure
from error import err_bad_request
from error import err_unauthorized
from error import err_forbidden
from error import err_not_found
from error import err_method_not_allowed
from error import err_unprocessable
from error import err_server_error


load_dotenv()

app = Flask(__name__)
db = setup_db(app)
setup_error_handlers(app)
CORS(app)
Migrate(app, db)


@app.route('/recipe')
def get_recipe_list():
    return "hi there"


@app.route('/recipe/<int:recipe_id>')
def get_recipe(recipe_id):
    return "hi there"


@app.route('/recipe', methods=("POST",))
def add_recipe():
    return "hi there"


@app.route('/recipe/<int:id>', methods=("PATCH",))
def update_recipe():
    return "hi there"


@app.route('/recipe/<int:id>', methods=("DELETE",))
def delete_recipe():
    return "hi there"


@app.route('/menu')
def get_menu_list():
    return "hi there"


@app.route('/menu/<int:id>')
def get_menu(menu_id):
    return "hi there"


@app.route('/menu', methods=("POST",))
def add_menu():
    return "hi there"


@app.route('/menu/<int:id>', methods=("PATCH",))
def update_menu():
    return "hi there"


@app.route('/menu/<int:id>', methods=("DELETE",))
def delete_menu():
    return "hi there"


if __name__ == '__main__':
    app.run()
