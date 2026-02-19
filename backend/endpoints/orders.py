from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from psycopg.errors import ForeignKeyViolation
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
            # Need to figure out price
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity) VALUES(%s, %s, 1)
                ON CONFLICT (order_id, product_id)
                DO UPDATE SET quantity = order_items.quantity + 1
                """,(order_id,productId,)
            )
            
            db.commit()
            return jsonify({'message': 'Item added to cart successfully'}), 200
        
    except ForeignKeyViolation as e:
        return jsonify({'error': 'Product does not exsist'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@orders_bp.route('/orders/getUsersCart', methods=['GET'])
@jwt_required() # You can only get your own cart
def getUsersCartInfo():
    db = get_db()
    user_id = get_jwt_identity()

    try:
        with db.cursor() as cur:

            # Try to get order_id
            cur.execute("""
                SELECT 
                    product_id,
                    product_name,
                    quantity,
                    (price * quantity) AS total_price,
                    price AS unit_price,
                    image AS image_url
                FROM orders 
                JOIN order_items USING (order_id)
                JOIN products using (product_id)
                WHERE user_id = %s AND order_status = 0
                """,(user_id,)
            )
            items = cur.fetchall()

            cur.execute("""
                SELECT 
                    sum (price * quantity) AS total_price,
                    sum (weight * quantity) AS total_weight
                FROM orders 
                JOIN order_items USING (order_id)
                JOIN products using (product_id)
                WHERE user_id = %s AND order_status = 0
                """,(user_id,)
            )
            total_price = cur.fetchone()

            return jsonify({"items":items, "total_price":total_price}),200
    except ForeignKeyViolation as e:
        return jsonify({'error': 'Product does not exsist'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500