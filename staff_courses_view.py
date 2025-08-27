from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from database import get_db

staff_courses_view_bp = Blueprint('staff_courses_view', __name__)

# Fetch active courses for the logged-in staff
@staff_courses_view_bp.route('/courses/view', methods=['GET'])
def view_staff_active_courses():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        staff_user_id = session.get('user_id')  # Get user_id from session

        if not staff_user_id:
            return jsonify({'status': 'error', 'message': 'Staff not logged in.'}), 401

        # Query to fetch active courses created by this staff
        query = """
            SELECT 
                c.course_id, c.course_code, c.course_title, c.course_status,
                c.course_description, c.course_category, c.target_audience,
                c.prerequisites, c.learning_outcomes, c.duration_hours,
                c.course_fee, c.max_students, c.published,
                c.date_created, c.date_updated, c.date_published, c.date_modified
            FROM courses c
            JOIN login l ON c.created_by = l.user_id
            WHERE c.course_status = 'active' AND l.role = 'staff' AND c.created_by = %s
        """
        cursor.execute(query, (staff_user_id,))
        courses = cursor.fetchall()

        return render_template('/staffs/staff_courses_view.html', courses=courses)

    except Exception as e:
        return str(e), 500
