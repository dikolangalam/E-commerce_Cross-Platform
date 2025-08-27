from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from database import get_db
import json

staff_class_creation_bp = Blueprint('staff_class_creation', __name__)

def validate_time_format(time_str):
    """Validate that time is in HH:00 format (on the hour) and between 6AM and 6PM"""
    try:
        if not time_str.endswith(':00'):
            return False
        hours, minutes = map(int, time_str.split(':'))
        return 6 <= hours <= 18 and minutes == 0 
    except (ValueError, AttributeError):
        return False

@staff_class_creation_bp.route('/class/create', methods=['GET', 'POST'])
def create_class():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'GET':
        try:
            query = "SELECT course_id, course_title FROM courses WHERE course_status = 'active'"
            cursor.execute(query)
            courses = cursor.fetchall()

            return render_template('staffs/staff_class_creation.html', courses=courses)

        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    elif request.method == 'POST':
        try:
            instructor_id = session.get('user_id')
            if not instructor_id:
                return jsonify({'status': 'error', 'message': 'Instructor not logged in.'}), 401

            data = request.form  

            course_id = data.get('course_id')
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

            # Validate required fields
            required_fields = {
                'course_id': 'Course',
                'class_title': 'Class Title',
                'school_year': 'School Year',
                'schedule': 'Schedule',
                'venue': 'Venue',
                'max_students': 'Maximum Students',
                'start_date': 'Start Date',
                'end_date': 'End Date',
                'days_of_week': 'Days of Week',
                'instructor_name': 'Instructor Name'
            }

            missing_fields = [field for field in required_fields if not data.get(field)]
            if missing_fields:
                return jsonify({
                    'status': 'error',
                    'message': f"Missing required fields: {', '.join([required_fields[field] for field in missing_fields])}"
                }), 400

            # Check if days_of_week is valid JSON and validate times
            try:
                days_of_week_json = json.loads(days_of_week)
                for day, times in days_of_week_json.items():
                    if not validate_time_format(times.get('start')) or not validate_time_format(times.get('end')):
                        return jsonify({
                            'status': 'error',
                            'message': 'Invalid time format. Times must be on the hour (e.g., 7:00, 8:00)'
                        }), 400
            except json.JSONDecodeError:
                return jsonify({'status': 'error', 'message': 'Invalid JSON format for days_of_week.'}), 400

            # Fetch prerequisites from course
            prereq_query = "SELECT prerequisites FROM courses WHERE course_id = %s"
            cursor.execute(prereq_query, (course_id,))
            course = cursor.fetchone()
            if not course:
                return jsonify({'status': 'error', 'message': 'Invalid course selected.'}), 400

            prerequisites = course['prerequisites']
            now = datetime.now()

            insert_query = """
                INSERT INTO classes (
                    course_id, class_title, school_year, batch, schedule, 
                    days_of_week, venue, max_students, instructor_id, instructor_name,
                    start_date, end_date, prerequisites, status, date_created
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            """

            cursor.execute(insert_query, (
                course_id, class_title, school_year, batch, schedule, 
                json.dumps(days_of_week_json), venue, max_students, instructor_id, instructor_name,
                start_date, end_date, prerequisites, now
            ))
            db.commit()

            return jsonify({
                'status': 'success', 
                'message': 'Class created and pending admin approval.'
            })

        except Exception as e:
            db.rollback()
            return jsonify({'status': 'error', 'message': str(e)}), 500