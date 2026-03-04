from flask import Blueprint, jsonify, request
from .decorators import admin_required
from ..db import get_db

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin/inventory', methods=['GET'])
@admin_required()
def get_inventory():
    db = get_db()
    try:
        with db.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM products 
                ORDER BY product_id ASC
            """)
            product = cur.fetchall()

            return jsonify(product), 200

    except Exception as e:
        print(f"[MAINFRAME ERROR - INVENTORY]: {e}")
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/admin/orders', methods=['GET'])
@admin_required()
def get_orders():
    try:
        db = get_db()

        with db.cursor() as cur:
            cur.execute("SELECT * FROM orders")
            orders = cur.fetchall()

        return jsonify(orders), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/admin/change-product-status/<int:product_id>', methods=['POST'])
@admin_required()
def change_product_status(product_id):
    try:
        # 1. Grab the JSON data sent from the frontend
        data = request.get_json()

        # 2. Check if 'published' was actually sent in the request
        if data is None or 'published' not in data:
            return jsonify({"error": "Missing 'published' status"}), 400

        # 3. Extract the exact True or False value
        target_status = bool(data['published'])

        db = get_db()
        with db.cursor() as cur:
            # 4. Set the column to the exact boolean value provided
            cur.execute(
                "UPDATE products SET published = %s WHERE product_id = %s RETURNING *",
                (target_status, product_id)
            )
            product = cur.fetchone()

        if not product:
            return jsonify({"error": "Specimen not found"}), 404

        # 5. Save the change
        db.commit()

        return jsonify({"message": f"Status updated to {target_status}"}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/admin/change-product-stock/<int:product_id>', methods=['POST'])
@admin_required()
def change_product_stock(product_id):
    try:
        data = request.get_json()

        # 1. Look for 'adjustment' (e.g., 5 or -2)
        if data is None or 'adjustment' not in data:
            return jsonify({"error": "Missing stock adjustment value"}), 400

        try:
            adjustment = int(data['adjustment'])
        except ValueError:
            return jsonify({"error": "Adjustment must be a whole number"}), 400

        db = get_db()
        with db.cursor() as cur:
            # 2. Use RETURNING * so fetchone() actually has something to grab
            cur.execute(
                """
                UPDATE products 
                SET stock = stock + %s 
                WHERE product_id = %s 
                RETURNING stock
                """,
                (adjustment, product_id)
            )
            result = cur.fetchone()

        # 3. If result is None, the ID didn't exist
        if not result:
            return jsonify({"error": "Product not found"}), 404

        db.commit()

        return jsonify({
            "message": "Stock updated",
            "new_stock": result['stock']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route('/admin/change-product-price/<int:product_id>', methods=['POST'])
@admin_required()
def change_product_price(product_id):
    try:
        data = request.get_json()

        if data is None or 'price' not in data:
            return jsonify({"error": "Missing 'price' value"}), 400

        try:
            new_price = float(data['price'])
        except ValueError:
            return jsonify({"error": "Price must be a valid number"}), 400

        if new_price < 0:
            return jsonify({"error": "Price cannot be negative"}), 400

        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                """
                UPDATE products 
                SET price = %s 
                WHERE product_id = %s 
                RETURNING price
                """,
                (new_price, product_id)
            )
            result = cur.fetchone()

        if not result:
            return jsonify({"error": "Product not found"}), 404

        db.commit()
        return jsonify({
            "message": "Price calibrated successfully",
            "new_price": result['price']
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@admin_bp.route('/admin/change-order-status/<int:order_id>', methods=['POST'])
@admin_required()
def change_order_status(order_id):
    try:
        data = request.get_json()

        if data is None or 'status' not in data:
            return jsonify({"error": "Missing 'status' value"}), 400

        try:
            new_status = bool(data['status'])
        except ValueError:
            return jsonify({"error": "Status must be a boolean"}), 400

        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                """
                UPDATE orders 
                SET order_complete = %s 
                WHERE order_id = %s 
                RETURNING order_complete
                """,
                (new_status, order_id)
            )
            result = cur.fetchone()

        if not result:
            return jsonify({"error": "Order not found"}), 404

        db.commit()
        return jsonify({
            "message": "Order status updated",
            "new_status": result['order_complete']
        }), 200    

    except Exception as e:
        return jsonify({"error": str(e)}), 500