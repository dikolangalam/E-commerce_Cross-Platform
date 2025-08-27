from flask import Blueprint, render_template, request, jsonify, session
from database import get_db
from datetime import datetime
import traceback

admin_courses_edit_req_bp = Blueprint('admin_courses_edit_req', __name__)

@admin_courses_edit_req_bp.route('/courses/edit-requests', methods=['GET'])
def view_edit_requests():
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
                c.date_updated, c.date_published, c.date_modified, c.edit_reason
            FROM courses c
            JOIN login l ON c.created_by = l.user_id
            JOIN personal_information p ON l.user_id = p.user_id
            WHERE c.course_status = 'edited' AND l.role = 'staff'
        """
        cursor.execute(query)
        courses = cursor.fetchall()

        return render_template('admin/admin_courses_edit_req.html', courses=courses)
    except Exception as e:
        return str(e), 500

@admin_courses_edit_req_bp.route('/courses/edit-details/<int:course_id>', methods=['GET'])
def get_edit_details(course_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)  # This is valid for mysql.connector

        query = """
            SELECT 
                c.course_id, c.course_code, c.course_title, c.course_status,
                l.user_id, l.role,
                p.first_name, p.last_name,
                c.course_description, c.course_category, c.target_audience,
                c.prerequisites, c.learning_outcomes, c.duration_hours,
                c.course_fee, c.max_students, c.published,
                c.created_by, c.approved_by, c.date_created,
                c.date_updated, c.date_published, c.date_modified, c.edit_reason
            FROM courses c
            JOIN login l ON c.created_by = l.user_id
            JOIN personal_information p ON l.user_id = p.user_id
            WHERE c.course_id = %s
        """
        cursor.execute(query, (course_id,))
        edited_course = cursor.fetchone()

        if not edited_course:
            return jsonify({'status': 'error', 'message': 'Course not found.'}), 404

        return jsonify({
            'status': 'success',
            'edited_course': edited_course
        })
    except Exception as e:
        traceback.print_exc()  # Will print detailed error in server logs
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_courses_edit_req_bp.route('/approve-edit/<int:course_id>', methods=['POST'])
def approve_edit(course_id):
    try:
        db = get_db()
        cursor = db.cursor()

        admin_user_id = session.get('user_id')
        if not admin_user_id:
            return jsonify({'status': 'error', 'message': 'Admin not logged in.'}), 401

        now = datetime.now()

        # Approve the edit and set the course status to 'active'
        query = """
            UPDATE courses 
            SET course_status = 'active',
                approved_by = %s,
                date_modified = %s,
                edit_reason = NULL
            WHERE course_id = %s
        """
        cursor.execute(query, (admin_user_id, now, course_id))
        db.commit()

        return jsonify({'status': 'success', 'message': 'Course edit approved successfully.'})
    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@admin_courses_edit_req_bp.route('/reject-edit/<int:course_id>', methods=['POST'])
def reject_edit(course_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        admin_user_id = session.get('user_id')
        if not admin_user_id:
            return jsonify({'status': 'error', 'message': 'Admin not logged in.'}), 401

        # Fetch the latest original course version from course_history
        history_query = """
            SELECT * FROM course_history 
            WHERE course_id = %s 
            ORDER BY history_date DESC 
            LIMIT 1
        """
        cursor.execute(history_query, (course_id,))
        original_course = cursor.fetchone()

        if not original_course:
            return jsonify({'status': 'error', 'message': 'Original course version not found.'}), 404

        now = datetime.now()

        # Restore original values to courses table
        restore_query = """
            UPDATE courses 
            SET 
                course_code = %s,
                course_title = %s,
                course_description = %s,
                course_category = %s,
                target_audience = %s,
                prerequisites = %s,
                learning_outcomes = %s,
                duration_hours = %s,
                course_fee = %s,
                max_students = %s,
                course_status = 'active',
                approved_by = %s,
                date_modified = %s,
                edit_reason = NULL
            WHERE course_id = %s
        """
        cursor.execute(restore_query, (
            original_course['course_code'],
            original_course['course_title'],
            original_course['course_description'],
            original_course['course_category'],
            original_course['target_audience'],
            original_course['prerequisites'],
            original_course['learning_outcomes'],
            original_course['duration_hours'],
            original_course['course_fee'],
            original_course['max_students'],
            admin_user_id,
            now,
            course_id
        ))
        db.commit()

        return jsonify({'status': 'success', 'message': 'Course edit rejected and original version restored.'})
    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
