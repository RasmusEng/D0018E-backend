from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from psycopg.errors import ForeignKeyViolation
from ..db import *
orders_bp = Blueprint('orders', __name__)
    
@orders_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_users_orders():
    user_id = get_jwt_identity()
    claims = get_jwt()

    db = get_db()

    try:
        with db.cursor() as cur:

            cur.execute(
                """SELECT 
                        o.order_id,
                        o.order_state,
                        o.order_date,
                        o.shipped_date,
                        json_agg(json_build_object(
                            'product_name', oi.product_name, 
                            'quantity',  oi.quantity,
                            'list_price', oi.list_price,
                            'item_total', (oi.quantity * oi.list_price)
                        )) AS items
                    FROM orders o
                    JOIN order_items oi ON o.order_id = oi.order_id
                    WHERE (%(is_admin)s OR user_id = %(u_id)s)
                    GROUP BY o.order_id
                    ORDER BY o.order_id DESC;
                """,
                {
                    'u_id': user_id,
                    'is_admin': claims["is_administrator"]
                }
            )

            orders = cur.fetchall()
    except Exception as e:
        abort(500, description=str(e))

    return jsonify({'orders': orders}), 200