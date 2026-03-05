import os
import secrets

from . import db
from flask import Flask, app
from flask_jwt_extended import  JWTManager
from flask_cors import CORS

jwt = JWTManager()


# Might need to change here for pool
# Mainly flask docs

# Combo of docs, ai, and own
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        # Use ONE variable name everywhere: DATABASE_URL
        DATABASE_URL=os.environ.get("DATABASE_URL"),
        # Use a stable key from env; fallback only for dev
        JWT_SECRET_KEY=os.environ.get("JWT_SECRET_KEY", secrets.token_hex(64)),
    )
    if not app.config["DATABASE_URL"]:
        raise RuntimeError("DATABASE_URL is not set")

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    jwt.init_app(app)

    db.init_app(app)

    from .endpoints import products, review, checkout, cart, auth, admin, orders
    app.register_blueprint(products.products_bp)
    app.register_blueprint(checkout.checkout_bp)
    app.register_blueprint(review.review_bp)
    app.register_blueprint(orders.orders_bp)
    app.register_blueprint(cart.cart_bp)
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(admin.admin_bp)
    

    return app
