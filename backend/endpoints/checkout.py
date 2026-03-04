from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from psycopg.errors import ForeignKeyViolation
from ..db import *
checkout_bp = Blueprint('checkout', __name__)


class NotEnoughStockException(Exception):
    def __init__(self, items):
        self.items = items

@checkout_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    db = get_db()
    user_id = get_jwt_identity()

    try:
        with db.cursor() as cur:
            # Get cart id
            cur.execute("""
                SELECT 
                    cart_id
                FROM cart
                WHERE user_id = %(user_id)s
            """, {'user_id': user_id, })

            res = cur.fetchone()

            if (res):
                cart_id = res['cart_id']
            else:
                raise ValueError("No cart for user")

            # Verify stock (MBY add some lock so we cant order twice and have to cancel orders)
            cur.execute("""
                SELECT 
                    ci.product_id
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %(cart_id)s AND ci.quantity > p.stock
            """, {'cart_id': cart_id, })

            out_of_stock = cur.fetchall()

            if out_of_stock:
                raise (NotEnoughStockException(out_of_stock))

            # Create order
            cur.execute("""
                INSERT INTO orders (
                    user_id, 
                    order_complete, 
                    order_date
                ) 
                VALUES(
                    %(user_id)s, 
                    FALSE, 
                    CURRENT_DATE
                )
                RETURNING order_id
                """, {'user_id': user_id, }
            )
            order_id = cur.fetchone()['order_id']

            # Cart items to order_items
            cur.execute("""
                INSERT INTO order_items (
                    order_id,
                    product_id,
                    quantity,
                    list_price,
                    product_name      
                ) SELECT 
                    %(order_id)s, 
                    ci.product_id, 
                    ci.quantity, 
                    p.price,
                    p.product_name
                FROM cart_items ci
                JOIN products p ON ci.product_id = p.product_id
                WHERE ci.cart_id = %(cart_id)s
            """, {
                    'cart_id': cart_id,
                    'order_id': order_id,
                })

            # Update stock and sold amount
            cur.execute(""" 
                UPDATE products p
                SET
                    stock = p.stock - ci.quantity,
                    amount_sold = p.amount_sold + ci.quantity
                FROM cart_items ci
                WHERE ci.cart_id = %(cart_id)s
                    AND ci.product_id = p.product_id                 
            """, {'cart_id': cart_id, }
            )

            # Empty cart
            cur.execute(""" 
                DELETE FROM cart_items
                WHERE cart_id = %(cart_id)s
            """, {'cart_id': cart_id, }
            )

            # Delete cart
            cur.execute(""" 
                DELETE FROM cart
                WHERE cart_id = %(cart_id)s
            """, {'cart_id': cart_id, }
            )


        db.commit()

        return jsonify({'message': 'Checkout completed successfully', 'order_id': order_id}), 200
        
    except NotEnoughStockException as e:
        return jsonify({
            'error': 'items out of stock',
            'items': e.items
        }), 409
    except ValueError as e:
        return jsonify({'error': 'User has no cart'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
