from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
import psycopg
from ..db import *
review_bp = Blueprint('review', __name__)

# Perhaps change so it can take product_id or user_id
@review_bp.route('/review/<int:productID>', methods=['GET'])
def get_reviews_by_id(productID):
    db = get_db()
    cur = db.cursor()

    # Get all reviews
    cur.execute("""
        SELECT 
            u.name,
            u.user_id,
            r.review_id,
            r.review_text,
            r.grade,
            r.verified_customer,
            r.date
        FROM 
            review r 
        JOIN
            users u ON r.user_id = u.user_id  
        WHERE 
            r.product_id = %(id)s; 
        """, {'id': productID}
    )

    reviews = cur.fetchall()

    if reviews is None:
        abort(404, description="No reviews for provided product id found")

    # Get average grade
    cur.execute("""
                SELECT 
                    AVG(grade) AS average_grade
                FROM review 
                WHERE product_id = %(id)s; 
                """,{'id': productID}
            )
    res = cur.fetchone()
    
    average_grading = float(res['average_grade'] or 0.0) 

    return jsonify({
        "average_grading": average_grading,
        "reviews":reviews}),200


@review_bp.route('/review/<int:productID>', methods=['POST'])
@jwt_required() 
def register(productID):
    text = request.json.get('text')
    grade = request.json.get('grade')
    user_id = get_jwt_identity()

    db = get_db()

    if grade is None:
        return jsonify({'error': 'Grade is required.'}), 409
    if grade < 1 or grade > 5:
        return jsonify({'error': 'Grade needs to be in range 1-5'}), 409

    try:
        with db.cursor() as cur:

            cur.execute(
                """INSERT INTO review 
                    (product_id, review_text, grade, user_id, verified_customer) 
                VALUES (
                    %(p_id)s, 
                    %(r_text)s,
                    %(grade)s, 
                    %(u_id)s, 
                    (SELECT EXISTS (
                        SELECT 1 FROM orders o
                        JOIN order_items oi ON o.order_id = oi.order_id
                        WHERE o.user_id = %(u_id)s 
                            AND oi.product_id = %(p_id)s
                    ))
                )""",
                {
                    'p_id': productID,
                    'u_id': user_id,
                    'r_text': text,
                    'grade': grade
                }
            )

            db.commit()
 
    except psycopg.errors.UniqueViolation:
        return jsonify({'error': 'User already has review.'}), 409
    except Exception as e:
        abort(500, description=str(e))

    return jsonify({'message': 'Review created successfully'}), 200
