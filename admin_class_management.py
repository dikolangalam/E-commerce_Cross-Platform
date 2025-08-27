from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from database import get_db

admin_class_management_bp = Blueprint('admin_class_management', __name__)

@admin_class_management_bp.route('/class_management', methods=['GET'])
def view_active_classes():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Fetch all active classes with instructor/staff info
        query = """
            SELECT 
                cl.class_id, cl.class_title, cl.schedule, cl.venue, cl.max_students,
                cl.start_date, cl.end_date, cl.status, cl.date_created,
                co.course_title,
                pi.first_name, pi.last_name
            FROM classes cl
            JOIN courses co ON cl.course_id = co.course_id
            JOIN login l ON cl.instructor_id = l.user_id
            JOIN personal_information pi ON l.user_id = pi.user_id
            WHERE cl.status = 'active'
            ORDER BY cl.date_created DESC
        """
        cursor.execute(query)
        active_classes = cursor.fetchall()

        return render_template('admin/admin_class_management.html', classes=active_classes)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
