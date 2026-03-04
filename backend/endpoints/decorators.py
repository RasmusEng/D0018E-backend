from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            # .get() returns False if the key doesn't exist, preventing a 422 crash
            if claims.get("is_administrator") is True:
                return fn(*args, **kwargs)
            else:
                return jsonify(msg="Unauthorized: Level 5 Clearance Required"), 403
        return decorator
    return wrapper
