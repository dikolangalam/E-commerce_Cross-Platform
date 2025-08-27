from flask import Blueprint, render_template, request, jsonify
from database import get_db

admin_courses_avail_bp = Blueprint('admin_courses_avail', __name__)

@admin_courses_avail_bp.route('/courses/available', methods=['GET'])
def view_available_courses():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT 
                c.course_id, c.course_code, c.course_title, c.course_status,
                l.user_id, l.role,
                p.first_name, p.last_name,
                c.course_description, c.course_category, c.target_audience,
                c.prerequisites, c.learning_outcomes, c.duration_hours,
                c.course_fee, c.max_students, c.published, c.prerequisites,
                c.created_by, c.approved_by, c.date_created, c.learning_outcomes,
                c.date_updated, c.date_published, c.date_modified
            FROM courses c
            JOIN login l ON c.created_by = l.user_id
            JOIN personal_information p ON l.user_id = p.user_id
            WHERE c.course_status = 'active' AND l.role = 'staff'
        """
        cursor.execute(query)
        courses = cursor.fetchall()

        return render_template('/admin/admin_courses_avail.html', courses=courses)
    except Exception as e:
        return str(e), 500

@admin_courses_avail_bp.route('/course/available/details/<int:course_id>', methods=['GET'])
def get_available_course_details(course_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT 
                c.course_id, c.course_code, c.course_title, c.course_status,
                l.user_id, l.role,
                p.first_name, p.last_name,
                c.course_description, c.course_category, c.target_audience,
                c.prerequisites, c.learning_outcomes, c.duration_hours,
                c.course_fee, c.max_students, c.published,
                c.created_by, c.approved_by, c.date_created,
                c.date_updated, c.date_published, c.date_modified
            FROM courses c
            JOIN login l ON c.created_by = l.user_id
            JOIN personal_information p ON l.user_id = p.user_id
            WHERE c.course_id = %s
        """
        cursor.execute(query, (course_id,))
        course = cursor.fetchone()

        if course:
            return jsonify({
                'status': 'success',
                'course': {
                    'course_id': course['course_id'],
                    'course_code': course['course_code'],
                    'course_title': course['course_title'],
                    'course_description': course['course_description'],
                    'course_category': course['course_category'],
                    'target_audience': course['target_audience'],
                    'prerequisites': course['prerequisites'],
                    'learning_outcomes': course['learning_outcomes'],
                    'duration_hours': course['duration_hours'],
                    'course_fee': course['course_fee'],
                    'max_students': course['max_students'],
                    'course_status': course['course_status'],
                    'user_id': course['user_id'],
                    'role': course['role'],
                    'first_name': course['first_name'],
                    'last_name': course['last_name']
                }
            })
        else:
            return jsonify({'status': 'error', 'message': 'Course not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500