from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
import psycopg
from ..db import *
orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders/addToCart', methods=['POST'])
@jwt_required()
def addToCart():
    productId = request.json.get('product_id', None)
    db = get_db()

    if not productId:
        return jsonify({'error': 'Product_id is required.'}), 400
    
    user_id = get_jwt_identity()

    try:
        with db.cursor() as cur:
            
            # If have user_id check if user has a active cart
            #if(user_id):
            cur.execute(
                "SELECT order_id FROM orders WHERE user_id = %s AND order_status = 0",
                (user_id,)
            )

            result = cur.fetchone();
            
            #else: # We dont have a user_id so we need to create a user
            #    cur.execute("""
            #        INSERT INTO users (email, password, admin) VALUES (%s, %s, %s)
            #        RETURNING user_id
            #        """,(None, None, False)
            #    )
            #    user_id = cur.fetchone()['user_id']

            # We have a order_id
            if(result): 
                order_id = result['order_id']
            else: # If we didnt get a order id we need to create one
                cur.execute("""
                    INSERT INTO orders (order_status, user_id) VALUES (0, %s)
                    RETURNING order_id
                    """,(user_id,)
                )
                order_id = cur.fetchone()['order_id']

            # Add item to cart
            cur.execute("""
                INSERT INTO order_items (order_id, product_id) VALUES(%s, %s)
                ON CONFLICT (order_id, product_id)
                DO UPDATE SET quantity = order_items.quantity + 1
                """,(order_id,productId,)
            )
            
            db.commit()
            return jsonify({}), 200
            
    except Exception as e:
        return jsonify({'error':'No is work'}), 500