from flask import Blueprint, render_template, request, jsonify, session, url_for, redirect
from database import get_db
import json
from datetime import datetime
import mysql.connector

student_homepage_bp = Blueprint('student_homepage', __name__)

@student_homepage_bp.route('/student_homepage')
def student_home():
    """Serve the student homepage with user_id from session"""
    # Get user_id from session (default to None if not found)
    user_id = session.get('user_id')
    
    if not user_id:
        # Handle case where user is not logged in
        return redirect(url_for('login.login'))  # Adjust to your login route
    
    return render_template('students/student_homepage.html', user_id=user_id)

@student_homepage_bp.route('/schedule')
def student_schedule():
    """Serve the schedule section with user_id from session"""
    user_id = session.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'User not authenticated'}), 401
        
    return render_template('students/student_homepage.html', user_id=user_id, active_tab='schedule')

@student_homepage_bp.route('/api/schedule/<int:user_id>', methods=['GET'])
def get_user_schedule(user_id):
    """Get the schedule for a specific student"""
    connection = get_db()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = connection.cursor(dictionary=True)
        
        # Verify user exists and is a student
        cursor.execute("""
            SELECT role FROM login 
            WHERE user_id = %s AND role = 'student' AND account_status = 'active'
        """, (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'User not found or not an active student'}), 404

        # Get all active classes the user is enrolled in
        cursor.execute("""
            SELECT c.class_id, c.class_title, c.course_id, c.schedule, 
                   c.days_of_week, c.venue, c.start_date, c.end_date,
                   co.course_title, co.course_code
            FROM enrollment e
            JOIN classes c ON e.class_id = c.class_id
            JOIN courses co ON c.course_id = co.course_id
            WHERE e.user_id = %s 
            AND c.status = 'active'
            AND e.status = 'enrolled'
        """, (user_id,))
        
        enrolled_classes = cursor.fetchall()

        # Process the schedule data
        schedule = []
        today = datetime.now().date()
        
        for cls in enrolled_classes:
            days_schedule = {}
            if cls['days_of_week']:
                try:
                    days_schedule = json.loads(cls['days_of_week'])
                except json.JSONDecodeError:
                    days_schedule = {}

            class_info = {
                'class_id': cls['class_id'],
                'title': f"{cls['course_code']} - {cls['class_title']}",
                'course': cls['course_title'],
                'venue': cls['venue'],
                'start_date': cls['start_date'].isoformat() if cls['start_date'] else None,
                'end_date': cls['end_date'].isoformat() if cls['end_date'] else None,
                'schedule': cls['schedule'],
                'days': [{
                    'day': day,
                    'start_time': times.get('start', ''),
                    'end_time': times.get('end', '')
                } for day, times in days_schedule.items()]
            }
            schedule.append(class_info)

        return jsonify({
            'user_id': user_id,
            'schedule': schedule,
            'current_date': today.isoformat()
        })

    except mysql.connector.Error as e:
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()