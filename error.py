from flask import abort
from flask import jsonify


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def success(key, payload):
    return (jsonify({"success": True, key: payload}), 200)


def success2(key, payload, key2, payload2):
    return (jsonify({"success": True, key: payload, key2: payload2}), 200)


def failure(message):
    return (jsonify({"success": False, "message": message}), 200)


def err_bad_request(msg):
    abort(400, description=msg)


def err_unauthorized(msg):
    abort(401, description=msg)


def err_forbidden(msg):
    abort(403, description=msg)


def err_not_found(msg):
    abort(404, description=msg)


def err_method_not_allowed(msg):
    abort(405, description=msg)


def err_unprocessable(msg):
    abort(422, description=msg)


def err_server_error(msg):
    abort(500, description=msg)


def setup_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return generic_error(400, error)

    @app.errorhandler(401)
    def unauthorized(error):
        return generic_error(401, error)

    @app.errorhandler(403)
    def forbidden(error):
        return generic_error(403, error)

    @app.errorhandler(404)
    def not_found(error):
        return generic_error(404, error)

    @app.errorhandler(405)
    def method_not_allowed(error):
        return generic_error(405, error)

    @app.errorhandler(422)
    def unprocessable(error):
        return generic_error(422, error)

    @app.errorhandler(500)
    def unprocessable(error):
        return generic_error(500, error)

    @app.errorhandler(AuthError)
    def auth_error(error):
        return generic_error(error.status_code, error.error)


def generic_error(status_code, error):
    return (
        jsonify({
            'success': False,
            'error': status_code,
            'message': str(error),
        }),
        status_code
    )
