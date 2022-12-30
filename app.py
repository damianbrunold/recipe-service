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

    @app.route('/recipe')
    def get_recipe_list():
        return "hi there"

    @app.route('/recipe/<int:id>')
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

    @app.errorhandler(400)
    def bad_request(error):
        return (
            jsonify({
                'success': False,
                'error': 400,
                'message': 'bad request',
            }),
            400
        )

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({
                'success': False,
                'error': 404,
                'message': 'resource not found',
            }),
            404
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        return (
            jsonify({
                'success': False,
                'error': 405,
                'message': 'method not allowed',
            }),
            405
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({
                'success': False,
                'error': 422,
                'message': 'unprocessable',
            }),
            422
        )

    @app.errorhandler(500)
    def server_error(error):
        return (
            jsonify({
                'success': False,
                'error': 500,
                'message': 'server error',
            }),
            500
        )
    return app


app = create_app()

if __name__ == '__main__':
    app.run()
