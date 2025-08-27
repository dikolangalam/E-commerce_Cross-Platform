from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from database import get_db

student_enrollment_bp = Blueprint('student_enrollment', __name__, url_prefix='/student')

@student_enrollment_bp.route('/enrollment', methods=['GET'])
def enrollment_page():
    if 'user_id' not in session or session.get('role') != 'student':
        flash("Unauthorized access. Please log in as a student.")
        return redirect(url_for('login.login_page'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Fetch available classes with course details
    query = """
        SELECT cl.class_id, cl.class_title, cl.schedule, cl.venue, cl.max_students,
               cl.start_date, cl.end_date, 
               co.course_title, co.course_description, co.course_category, 
               co.learning_outcomes, co.course_fee, co.prerequisites AS course_prerequisites
        FROM classes cl
        JOIN courses co ON cl.course_id = co.course_id
        WHERE cl.status = 'active'
    """
    cursor.execute(query)
    classes = cursor.fetchall()

    user_id = session['user_id']
    
    # Fetch already enrolled or pending class IDs for this user
    cursor.execute("""
        SELECT class_id FROM enrollment 
        WHERE user_id = %s AND status IN ('pending', 'enrolled')
    """, (user_id,))
    enrolled_classes = [row['class_id'] for row in cursor.fetchall()]
    
    # Check if student is currently enrolled in any course
    cursor.execute("""
        SELECT COUNT(*) as current_enrollments 
        FROM enrollment 
        WHERE user_id = %s AND status = 'enrolled'
    """, (user_id,))
    has_current_enrollment = cursor.fetchone()['current_enrollments'] > 0

    return render_template('students/student_enrollment.html', 
                         classes=classes, 
                         enrolled_classes=enrolled_classes,
                         has_current_enrollment=has_current_enrollment)

@student_enrollment_bp.route('/enroll', methods=['POST'])
def enroll():
    if 'user_id' not in session or session.get('role') != 'student':
        flash("Unauthorized action.")
        return redirect(url_for('login.login_page'))
    
    class_id = request.form.get('class_id')
    user_id = session['user_id']
    
    if not class_id:
        flash("Please select a class.")
        return redirect(url_for('student_enrollment.enrollment_page'))
    
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check if the student is currently enrolled in any course
    cursor.execute("""
        SELECT COUNT(*) as current_enrollments 
        FROM enrollment 
        WHERE user_id = %s AND status = 'enrolled'
    """, (user_id,))
    if cursor.fetchone()['current_enrollments'] > 0:
        flash("You are currently enrolled in another course. Please complete it before enrolling in a new one.")
        return redirect(url_for('student_enrollment.enrollment_page'))

    # Check if the student is already enrolled or has pending enrollment for this class
    cursor.execute("""
        SELECT * FROM enrollment
        WHERE user_id = %s AND class_id = %s AND status IN ('pending', 'enrolled')
    """, (user_id, class_id))
    existing = cursor.fetchone()
    
    if existing:
        flash("You already have a pending or active enrollment for this class.")
        return redirect(url_for('student_enrollment.enrollment_page'))

    # Insert new enrollment request with 'pending' status
    cursor.execute("""
        INSERT INTO enrollment (user_id, class_id, enrollment_date, status)
        VALUES (%s, %s, %s, %s)
    """, (user_id, class_id, datetime.now(), 'pending'))
    
    db.commit()
    flash("Enrollment request submitted and is now pending for approval.")
    return redirect(url_for('student_enrollment.enrollment_page'))