from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
import psycopg
from ..db import *
orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders/addToCart', methods=['POST'])
@jwt_required() # Atm we only allow loged in users to add to cart
def addToCart():
    productId = request.json.get('product_id', None)
    db = get_db()

    if not productId:
        return jsonify({'error': 'Product_id is required.'}), 400
    
    user_id = get_jwt_identity()

    try:
        with db.cursor() as cur:

            # Try to get order_id
            cur.execute(
                "SELECT order_id FROM orders WHERE user_id = %s AND order_status = 0",
                (user_id,)
            )

            result = cur.fetchone();
            
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

            # Add item to cart and if the given item already exsists just add one to it 
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity) VALUES(%s, %s, 1)
                ON CONFLICT (order_id, product_id)
                DO UPDATE SET quantity = order_items.quantity + 1
                """,(order_id,productId,)
            )
            
            db.commit()
            return jsonify({'message': 'Item added to cart successfully'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500