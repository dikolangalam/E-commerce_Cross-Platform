from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from database import get_db

staff_courses_edit_req_bp = Blueprint('staff_courses_edit_req', __name__)

# Fetch active courses for the logged-in staff
@staff_courses_edit_req_bp.route('/courses/active', methods=['GET'])
def view_active_courses():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        staff_user_id = session.get('user_id')  # Must be set at login

        if not staff_user_id:
            return jsonify({'status': 'error', 'message': 'Staff not logged in.'}), 401

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

        return render_template('/staffs/staff_courses_edit_req.html', courses=courses)
    except Exception as e:
        return str(e), 500

# Fetch single course details for editing
@staff_courses_edit_req_bp.route('/course/edit/<int:course_id>', methods=['GET'])
def get_course_for_edit(course_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        staff_user_id = session.get('user_id')

        if not staff_user_id:
            return jsonify({'status': 'error', 'message': 'Staff not logged in.'}), 401

        query = """
            SELECT 
                course_id, course_code, course_title, course_description,
                course_category, target_audience, prerequisites, learning_outcomes,
                duration_hours, course_fee, max_students
            FROM courses
            WHERE course_id = %s AND created_by = %s
        """
        cursor.execute(query, (course_id, staff_user_id))
        course = cursor.fetchone()

        if course:
            return jsonify({'status': 'success', 'course': course})
        else:
            return jsonify({'status': 'error', 'message': 'Course not found or not authorized.'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@staff_courses_edit_req_bp.route('/course/update/<int:course_id>', methods=['POST'])
def update_course(course_id):
    try:
        db = get_db()
        cursor = db.cursor()

        staff_user_id = session.get('user_id')

        if not staff_user_id:
            return jsonify({'status': 'error', 'message': 'Staff not logged in.'}), 401

        data = request.get_json()

        # Extract updated fields
        course_code = data.get('course_code')
        course_title = data.get('course_title')
        course_description = data.get('course_description')
        course_category = data.get('course_category')
        target_audience = data.get('target_audience')
        prerequisites = data.get('prerequisites')
        learning_outcomes = data.get('learning_outcomes')
        duration_hours = data.get('duration_hours')
        course_fee = data.get('course_fee')
        max_students = data.get('max_students')
        edit_reason = data.get('edit_reason') 

        if not edit_reason or edit_reason.strip() == '':
            return jsonify({'status': 'error', 'message': 'Edit reason is required.'}), 400
            
        now = datetime.now()

        query = """
            UPDATE courses
            SET course_code = %s,
                course_title = %s,
                course_description = %s,
                course_category = %s,
                target_audience = %s,
                prerequisites = %s,
                learning_outcomes = %s,
                duration_hours = %s,
                course_fee = %s,
                max_students = %s,
                course_status = 'edited',
                approved_by = NULL,
                date_modified = %s,
                edit_reason = %s
            WHERE course_id = %s AND created_by = %s
        """

        cursor.execute(query, (
            course_code, course_title, course_description, course_category,
            target_audience, prerequisites, learning_outcomes, duration_hours,
            course_fee, max_students, now, edit_reason, course_id, staff_user_id
        ))

        db.commit()

        return jsonify({'status': 'success', 'message': 'Course updated with reason and marked as pending for approval.'})
    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

