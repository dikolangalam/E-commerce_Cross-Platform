from flask import Blueprint, request, jsonify, session, render_template
from datetime import datetime
from database import get_db
import json
import re

student_view_class_bp = Blueprint('student_view_class', __name__)

@student_view_class_bp.route('/student/view_classes', methods=['GET'])
def view_enrolled_classes():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        student_id = session.get('user_id')
        if not student_id:
            return render_template('error.html', message="You must be logged in to view your classes"), 401

        query = """
            SELECT 
                cl.class_id,
                cl.class_title,
                cl.schedule,
                cl.venue,
                cl.start_date,
                cl.end_date,
                cl.status,
                cl.days_of_week,
                cl.max_students,
                cl.instructor_name,
                co.course_code,
                co.course_title,
                co.course_description
            FROM enrollment e
            JOIN classes cl ON e.class_id = cl.class_id
            JOIN courses co ON cl.course_id = co.course_id
            WHERE e.user_id = %s AND e.status = 'enrolled' AND cl.status = 'active'
            ORDER BY cl.start_date DESC
        """
        cursor.execute(query, (student_id,))
        enrolled_classes = cursor.fetchall()

        # Process days_of_week from JSON string to list
        for cls in enrolled_classes:
            cls['start_date'] = cls['start_date'].isoformat() if cls['start_date'] else None
            cls['end_date'] = cls['end_date'].isoformat() if cls['end_date'] else None
            if cls.get('days_of_week'):
                try:
                    cls['days_of_week'] = json.loads(cls['days_of_week'])
                except (json.JSONDecodeError, TypeError):
                    cls['days_of_week'] = {}

        return render_template('students/student_view_class.html', classes=enrolled_classes)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@student_view_class_bp.route('/schedule', methods=['GET'])
def view_schedule():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        student_id = session.get('user_id')
        if not student_id:
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

        query = """
            SELECT 
                cl.class_id,
                cl.class_title,
                cl.schedule,
                cl.venue,
                cl.days_of_week,
                cl.start_date,
                cl.end_date,
                co.course_code,
                co.course_title,
                cl.instructor_name
            FROM enrollment e
            JOIN classes cl ON e.class_id = cl.class_id
            JOIN courses co ON cl.course_id = co.course_id
            WHERE e.user_id = %s AND e.status = 'enrolled' AND cl.status = 'active'
        """
        cursor.execute(query, (student_id,))
        classes = cursor.fetchall()

        # Process days_of_week and extract time information
        for cls in classes:
            if cls.get('days_of_week'):
                try:
                    days_data = json.loads(cls['days_of_week'])
                    cls['days_of_week'] = days_data
                    
                    # Create a list of days with their times for easier template processing
                    cls['day_schedules'] = []
                    for day, times in days_data.items():
                        start_time = times.get('start', '00:00')
                        end_time = times.get('end', '00:00')
                        
                        # Convert to 12-hour format for display
                        start_hour = int(start_time.split(':')[0])
                        start_min = start_time.split(':')[1]
                        end_hour = int(end_time.split(':')[0])
                        end_min = end_time.split(':')[1]
                        
                        start_period = 'AM' if start_hour < 12 else 'PM'
                        end_period = 'AM' if end_hour < 12 else 'PM'
                        
                        # Convert to 12-hour format
                        display_start_hour = start_hour if start_hour <= 12 else start_hour - 12
                        display_end_hour = end_hour if end_hour <= 12 else end_hour - 12
                        
                        display_start = f"{display_start_hour}:{start_min} {start_period}"
                        display_end = f"{display_end_hour}:{end_min} {end_period}"
                        
                        cls['day_schedules'].append({
                            'day': day,
                            'start': start_time,
                            'end': end_time,
                            'display_start': display_start,
                            'display_end': display_end,
                            'start_hour': start_hour,
                            'end_hour': end_hour
                        })
                except (json.JSONDecodeError, TypeError, AttributeError) as e:
                    cls['days_of_week'] = {}
                    cls['day_schedules'] = []
            else:
                cls['days_of_week'] = {}
                cls['day_schedules'] = []

        return render_template('students/student_homepage.html', classes=classes)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500