from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, unset_jwt_cookies
from werkzeug.security import check_password_hash, generate_password_hash
from .decorators import admin_required
import psycopg
from ..db import *
auth_bp = Blueprint('auth', __name__)

# https://dev.to/nagatodev/how-to-add-login-authentication-to-a-flask-and-react-application-23i7
# For auth things

# Flask docs and gemini and own and dev.to
# We will verify email in frontend
@auth_bp.route('/auth/register', methods=['POST'])
def register():
    email = request.json.get('email')
    password = request.json.get('password')
    isAdmin = request.json.get('isAdmin')
    db = get_db()

    if not email:
        return jsonify({'error': 'Email is required.'}), 409
    elif not password:
        return jsonify({'error': 'Password is required.'}), 409
    elif isAdmin is None:
        return jsonify({'error': 'isAdmin is required'}), 409
    try:
        with db.cursor() as cur:

            cur.execute(
                "INSERT INTO users (email, password, admin) VALUES (%s, %s, %s)",
                (email, generate_password_hash(password),isAdmin,)
            )

            db.commit()
 
    except psycopg.errors.UniqueViolation:
        return jsonify({'error': 'User already exists.'}), 409
    except Exception as e:
        abort(500, description=str(e))

    return jsonify({'message': 'User registered successfully'}), 200

# Flask docs and gemini and own
# We will verify email in frontend
@auth_bp.route('/auth/login', methods=['POST'])
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    db = get_db()

    if not email:
        return jsonify({'error': 'Email is required.'}), 400
    elif not password:
        return jsonify({'error': 'Password is required.'}), 400
    try:
        with db.cursor() as cur:
            
            cur.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )

            user = cur.fetchone()
            if user is None or not check_password_hash(user['password'], password):
                return jsonify({'error': 'Invalid credentials.'}), 401
            
            access_token = create_access_token(identity=str(user["user_id"]), additional_claims={"is_administrator": user['admin']})
            return jsonify({'access_token': access_token}), 200
            
    except Exception as e:
        return jsonify({'error':'No is work'}), 500

#dev.to link
@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    try:
        response = jsonify({"message": "Logout successful YIPPIE"})
        unset_jwt_cookies(response)
        return  response, 200
            
    except Exception as e:
        return jsonify({'error':'No is work'}), 500

#dev.to link
@auth_bp.route('/auth/verify', methods=['GET'])
@jwt_required() # Just check if user is logged in 
def testUser():
    response = jsonify({
        "type": "Cho",
        "about": "R"
    })

    return response, 200

@auth_bp.route('/auth/verifyAdmin', methods=['GET'])
@admin_required() # Checks if user is admin
def testAdmin():
    response = jsonify({
        "type": "Cho",
        "about": "W"
    })

    return response, 200

