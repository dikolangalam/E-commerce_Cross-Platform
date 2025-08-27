from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from database import get_db
import json

staff_class_edit_req_bp = Blueprint('staff_class_edit_req', __name__)
    
def validate_time_format(time_str):
    """Validate that time is in HH:00 format (on the hour) and between 6AM and 6PM"""
    try:
        if not time_str.endswith(':00'):
            return False
        hours, minutes = map(int, time_str.split(':'))
        return 6 <= hours <= 18 and minutes == 0 
    except (ValueError, AttributeError):
        return False

@staff_class_edit_req_bp.route('/staff_class_edit_req', methods=['GET'])
def view_active_classes():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Get the instructor_id from session
        instructor_id = session.get('user_id')
        if not instructor_id:
            return render_template('error.html', message="You must be logged in to view classes"), 401

        query = """
            SELECT 
                cl.class_id, cl.class_title, cl.schedule, cl.venue, cl.max_students,
                cl.start_date, cl.end_date, cl.status, cl.date_created,
                cl.school_year, cl.batch, cl.days_of_week, cl.instructor_name,
                co.course_title
            FROM classes cl
            JOIN courses co ON cl.course_id = co.course_id
            WHERE cl.status = 'active' AND cl.instructor_id = %s
            ORDER BY cl.date_created DESC
        """
        cursor.execute(query, (instructor_id,))
        active_classes = cursor.fetchall()

        # Convert date objects to strings and parse days_of_week JSON
        for cls in active_classes:
            cls['start_date'] = cls['start_date'].isoformat() if cls['start_date'] else None
            cls['end_date'] = cls['end_date'].isoformat() if cls['end_date'] else None
            if cls['days_of_week']:
                cls['days_of_week'] = json.loads(cls['days_of_week'])

        return render_template('staffs/staff_class_edit_req.html', classes=active_classes)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@staff_class_edit_req_bp.route('/update_class', methods=['POST'])
def update_class_details():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        instructor_id = session.get('user_id')
        if not instructor_id:
            return jsonify({'status': 'error', 'message': 'You must be logged in to update classes'}), 401

        data = request.get_json()
        class_id = data.get('class_id')
        class_title = data.get('class_title')
        school_year = data.get('school_year')
        batch = data.get('batch')
        schedule = data.get('schedule')
        venue = data.get('venue')
        max_students = data.get('max_students')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        days_of_week = data.get('days_of_week')
        instructor_name = data.get('instructor_name')
        reason = data.get('reason')

        # Verify the instructor owns this class
        verify_query = "SELECT instructor_id FROM classes WHERE class_id = %s"
        cursor.execute(verify_query, (class_id,))
        result = cursor.fetchone()

        if not result or result['instructor_id'] != instructor_id:
            return jsonify({'status': 'error', 'message': 'You can only edit your own classes'}), 403

        # Validate time formats in days_of_week
        if days_of_week:
            for day, times in days_of_week.items():
                if not validate_time_format(times.get('start')) or not validate_time_format(times.get('end')):
                    return jsonify({
                        'status': 'error',
                        'message': 'Invalid time format. Times must be on the hour (e.g., 7:00, 8:00)'
                    }), 400

        update_query = """
            UPDATE classes
            SET class_title = %s, school_year = %s, batch = %s,
                schedule = %s, venue = %s, max_students = %s,
                start_date = %s, end_date = %s, days_of_week = %s,
                instructor_name = %s, edit_reason = %s, 
                status = 'edited', date_updated = %s
            WHERE class_id = %s
        """
        now = datetime.now()
        cursor.execute(update_query, (
            class_title, school_year, batch, schedule, venue, 
            max_students, start_date, end_date, json.dumps(days_of_week),
            instructor_name, reason, now, class_id
        ))
        db.commit()

        return jsonify({
            'status': 'success',
            'message': 'Class update request submitted with reason. Waiting for admin approval.'
        })

    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500