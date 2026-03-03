from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
import psycopg
from ..db import *
review_bp = Blueprint('review', __name__)

# Get all reviews for a specific product
@review_bp.route('/review/product/<int:productID>', methods=['GET'])
def get_reviews_by_product_id(productID):
    db = get_db()
    cur = db.cursor()

    try:
        with db.cursor() as cur:
            # Get all reviews for a product
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
                        """, {'id': productID}
                        )
            res = cur.fetchone()

            average_grading = float(res['average_grade'] or 0.0)

        return jsonify({
            "average_grading": average_grading,
            "reviews": reviews}), 200

    except Exception as e:
        abort(500, description=str(e))

# Get all reviews by a certain user
@review_bp.route('/review/user/<int:userID>', methods=['GET'])
def get_reviews_by_user_id(userID):
    db = get_db()
    cur = db.cursor()

    try:
        with db.cursor() as cur:
            # Get all reviews for a user
            cur.execute("""
                SELECT 
                    u.name,
                    u.user_id,
                    r.review_id,
                    r.review_text,
                    r.grade,
                    r.verified_customer,
                    r.date,
                    r.product_id
                FROM 
                    review r 
                JOIN
                    users u ON r.user_id = u.user_id  
                WHERE 
                    u.user_id = %(id)s; 
                """, {'id': userID}
            )

            reviews = cur.fetchall()

            if reviews is None:
                abort(404, description="No reviews for provided user id found")

        return jsonify({
            "reviews": reviews}), 200

    except Exception as e:
        abort(500, description=str(e))

# Post a review on a product
@review_bp.route('/review/<int:productID>', methods=['POST'])
@jwt_required()
def write_review(productID):
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
                        WHERE o.user_id = %(u_id)s AND oi.product_id = %(p_id)s
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
        return jsonify({'error': 'User already has review för that product.'}), 409
    except Exception as e:
        abort(500, description=str(e))

    return jsonify({'message': 'Review created successfully'}), 200

# Delete review (creator of review and admin can do this)
@review_bp.route('/review/<int:reviewID>', methods=['DELETE'])
@jwt_required()
def del_review(reviewID):
    db = get_db()
    user_id = get_jwt_identity()
    claims = get_jwt()

    try:
        with db.cursor() as cur:

            cur.execute(""" 
                    DELETE FROM review
                    WHERE review_id = %(review_id)s
                        AND (
                            user_id = %(user_id)s
                            OR %(is_admin)s = TRUE
                        )
                    RETURNING review_id;
                """,
                        {
                            'review_id': reviewID,
                            'user_id': user_id,
                            'is_admin': claims["is_administrator"]
                        }
                        )

            deleted = cur.fetchone()

            if not deleted:
                abort(
                    403, description="Review does not exsist or you are not permited to delete")

            db.commit()

        return jsonify({'message': 'Review deleted successfully'}), 200

    except Exception as e:
        abort(500, description=str(e))

# Edit review (only creator of review)
@review_bp.route('/review/<int:reviewID>', methods=['PATCH'])
@jwt_required()
def edit_review(reviewID):
    db = get_db()
    user_id = get_jwt_identity()

    text = request.json.get('text')
    grade = request.json.get('grade')

    if grade is not None:
        if grade < 1 or grade > 5:
            return jsonify({'error': 'Grade needs to be in range 1-5'}), 409

    try:
        with db.cursor() as cur:

            cur.execute(""" 
                    UPDATE review
                    SET
                        review_text = COALESCE(%(text)s,review_text),
                        grade = COALESCE(%(grade)s,grade),
                        date = CURRENT_DATE
                    
                    WHERE review_id = %(review_id)s
                        AND (
                            user_id = %(user_id)s
                        );
                """,
                        {
                            'review_id': reviewID,
                            'grade': grade,
                            'text': text,
                            'user_id': user_id,
                        }
                        )

            db.commit()
            if (cur.rowcount == 0):
                abort(
                    403, description="Review does not exsist or you are not permited to delete")

        return jsonify({'message': 'Review updated successfully'}), 200

    except Exception as e:
        abort(500, description=str(e))
