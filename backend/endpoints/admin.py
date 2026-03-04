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