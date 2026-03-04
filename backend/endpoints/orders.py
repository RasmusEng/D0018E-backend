from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from psycopg.errors import ForeignKeyViolation
from ..db import *
orders_bp = Blueprint('orders', __name__)


@orders_bp.route('/orders/addToCart', methods=['POST'])
@jwt_required()  # Atm we only allow logged in users to add to cart
def addToCart():
    # request.get_json(silent=True) prevents crashes if headers are missing
    data = request.get_json(silent=True)
    if not data or not data.get('product_id'):
        return jsonify({'error': 'product_id is required.'}), 400

    product_id = data.get('product_id')
    user_id = get_jwt_identity()
    db = get_db()

    try:
        with db.cursor() as cur:
            # 1. Try to find the user's cart (Removed order_status)
            cur.execute(
                "SELECT cart_id FROM cart WHERE user_id = %s",
                (user_id,)
            )
            result = cur.fetchone()

            # 2. Get existing cart_id OR create a new cart
            if result:
                # Using [0] handles standard tuple cursors safely
                cart_id = result[0] if isinstance(
                    result, tuple) else result['cart_id']
            else:
                cur.execute("""
                    INSERT INTO cart (user_id) VALUES (%s)
                    RETURNING cart_id
                    """, (user_id,)
                )
                inserted = cur.fetchone()
                cart_id = inserted[0] if isinstance(
                    inserted, tuple) else inserted['cart_id']

            # 3. Check if the product is already in the cart_items
            cur.execute("""
                SELECT quantity FROM cart_items 
                WHERE cart_id = %s AND product_id = %s
                """, (cart_id, product_id)
            )
            existing_item = cur.fetchone()

            # 4. Insert or Update quantity based on existence
            if existing_item:
                cur.execute("""
                    UPDATE cart_items 
                    SET quantity = quantity + 1 
                    WHERE cart_id = %s AND product_id = %s
                    """, (cart_id, product_id)
                )
            else:
                cur.execute("""
                    INSERT INTO cart_items (cart_id, product_id, quantity) 
                    VALUES (%s, %s, 1)
                    """, (cart_id, product_id)
                )

            db.commit()
            return jsonify({'message': 'Item added to cart successfully'}), 200

    except ForeignKeyViolation as e:
        db.rollback()  # Always rollback on error to free the DB transaction
        return jsonify({'error': 'Product does not exist'}), 404

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500


@orders_bp.route('/orders/getUsersCart', methods=['GET'])
@jwt_required()  # You can only get your own cart
def getUsersCartInfo():
    db = get_db()
    user_id = get_jwt_identity()

    try:
        with db.cursor() as cur:
            cur.execute("""
            SELECT 
                product_id,
                product_name,
                quantity,
                (price * quantity) AS total_price,  
                price AS unit_price,
                image AS image_url
            FROM cart 
            JOIN cart_items USING (cart_id)
            JOIN products USING (product_id)
            WHERE user_id = %s
            """, (user_id,)
            )
            # Indented these so the cursor stays open!
            items = cur.fetchall()

            # Query 2: Get the total price and weight of the cart
            cur.execute("""
            SELECT 
                sum(price * quantity) AS total_price,
                sum(weight * quantity) AS total_weight
            FROM cart 
            JOIN cart_items USING (cart_id)
            JOIN products USING (product_id)
            WHERE user_id = %s
            """, (user_id,)
            )
            total_price = cur.fetchone()

            return jsonify({"items": items, "total_price": total_price}), 200

    except ForeignKeyViolation as e:
        return jsonify({'error': 'Product does not exist'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Added /api/ to the route prefix
@orders_bp.route('/orders/removeFromCart', methods=['POST'])
@jwt_required()
def removeFromCart():
    db = get_db()
    user_id = get_jwt_identity()

    # Added silent=True here as best practice (like your addToCart route)
    data = request.get_json(silent=True)
    if not data or not data.get('product_id'):
        return jsonify({'error': 'Product ID is required'}), 400
        
    product_id = data.get('product_id')

    try:
        with db.cursor() as cur:
            cur.execute("""
                DELETE FROM cart_items 
                WHERE product_id = %s 
                AND cart_id = (
                    SELECT cart_id 
                    FROM cart  
                    WHERE user_id = %s
                )
                RETURNING product_id; 
            """, (product_id, user_id,)
            )
            deleted_item = cur.fetchone()

            if not deleted_item:
                return jsonify({'error': 'Specimen not found in incubator'}), 404

            db.commit()
            return jsonify({'message': 'Specimen safely removed'}), 200

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    

@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_users_orders():
    user_id = get_jwt_identity()

    db = get_db()

    try:
        with db.cursor() as cur:

            cur.execute(
                """SELECT 
                        o.order_id,
                        o.order_complete,
                        o.order_date,
                        o.shipped_date,
                        oi.product_name,
                        oi.quantity,
                        oi.list_price,
                        (oi.quantity * oi.list_price) AS total_item
                    FROM orders o
                    JOIN order_items oi ON o.order_id = oi.order_id
                    WHERE user_id = %(u_id)s
                    ORDER BY o.order_id DESC;
                """,
                {
                    'u_id': user_id,
                }
            )

            orders = cur.fetchall()
    except Exception as e:
        abort(500, description=str(e))

    return jsonify({'orders': orders}), 200