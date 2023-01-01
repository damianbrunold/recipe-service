import os
from functools import wraps

import jwt
from flask import request
from flask import g
from flask import _request_ctx_stack

from error import AuthError


AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
ALGORITHMS = os.environ.get("AUTH0_ALGORITHMS", "").split(",")
API_AUDIENCE = os.environ.get("AUTH0_API_AUDIENCE")


'''
Extract token from request header.

Raise AuthError if header missing, invalid type or token missing
'''
def get_token_auth_header():
    auth = request.headers.get('Authorization', None)
    if not auth:
        raise AuthError({
            'code': 'authorization_header_missing',
            'description': 'Authorization header is expected.'
        }, 401)
    parts = auth.split()
    if parts[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must start with "Bearer".'
        }, 401)
    elif len(parts) == 1:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Token not found.'
        }, 401)
    elif len(parts) > 2:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization header must be bearer token.'
        }, 401)
    token = parts[1]
    return token


'''
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    if "permissions" not in payload:
        raise AuthError({
            'code': 'unauthorized',
            'description': f'Permissions missing in token',
        }, 403)
    if permission not in payload['permissions']:
        raise AuthError({
            'code': 'forbidden',
            'description': f'User does not have permission {permission}',
        }, 403)
    return True


'''
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload
'''
def verify_decode_jwt(token):
    if os.environ.get("TEST", "") == "true":
        return jwt.decode(token, "test", algorithms=["HS256"])
    else:
        try:
            url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
            jwks_client = jwt.PyJWKClient(url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                options={"verify_signature": True},
            )
            return payload
        except jwt.exceptions.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)
        except (
            jwt.exceptions.InvalidAudienceError,
            jwt.exceptions.InvalidIssuerError,
            jwt.exceptions.InvalidIssuedAtError,
        ):
            raise AuthError({
                'code': 'invalid_claim',
                'description': 'There is an issue with the claims of the token.'
            }, 401)
        except jwt.exceptions.InvalidSignatureError:
            raise AuthError({
                'code': 'invalid_signature',
                'description': 'The signature does not match.'
            }, 401)
        raise AuthError({
            'code': 'invalid_token',
            'description': 'Cannot decode token.'
        }, 400)

'''
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=""):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            g.username = payload.get("user-email", "")
            return f(*args, **kwargs)
        return wrapper
    return requires_auth_decorator


def has_permission(permission):
    token = get_token_auth_header()
    payload = verify_decode_jwt(token)
    return permission in payload["permissions"]
