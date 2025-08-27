from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
from database import get_db

staff_enrollment_acceptance_bp = Blueprint('staff_enrollment_acceptance', __name__, url_prefix='/staff')

@staff_enrollment_acceptance_bp.route('/enrollment_acceptance', methods=['GET']) 
def view_enrollment_requests():
    if 'user_id' not in session or session.get('role') != 'staff':
        flash("Unauthorized access. Please log in as staff.")
        return redirect(url_for('login.login_page'))

    staff_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Get the courses created by this staff
    cursor.execute("""
        SELECT course_id FROM courses WHERE created_by = %s
    """, (staff_id,))
    course_ids = [row['course_id'] for row in cursor.fetchall()]

    if not course_ids:
        flash("You are not handling any courses.")
        return render_template('staffs/staff_enrollment_acceptance.html', enrollments=[])

    # Fetch all pending enrollments for classes under these courses
    format_strings = ','.join(['%s'] * len(course_ids))
    cursor.execute(f"""
        SELECT e.enrollment_id, e.user_id, e.class_id, e.status,
               pi.first_name, pi.middle_name, pi.last_name,
               l.email,
               cl.class_title, cl.schedule, cl.venue, cl.max_students, cl.start_date, cl.end_date,
               co.course_title, co.course_description, co.course_category,
               co.learning_outcomes, co.course_fee, co.prerequisites AS course_prerequisites
        FROM enrollment e
        JOIN personal_information pi ON e.user_id = pi.user_id
        JOIN login l ON e.user_id = l.user_id
        JOIN classes cl ON e.class_id = cl.class_id
        JOIN courses co ON cl.course_id = co.course_id
        WHERE e.status = 'pending' AND cl.course_id IN ({format_strings})
    """, tuple(course_ids))

    enrollments = cursor.fetchall()

    return render_template('staffs/staff_enrollment_acceptance.html', enrollments=enrollments)

@staff_enrollment_acceptance_bp.route('/enrollment_acceptance/action', methods=['POST'])
def handle_enrollment_action():
    if 'user_id' not in session or session.get('role') != 'staff':
        flash("Unauthorized action.")
        return redirect(url_for('login.login_page'))

    enrollment_id = request.form.get('enrollment_id')
    action = request.form.get('action') 

    if not enrollment_id or action not in ['accept', 'reject']:
        flash("Invalid request.")
        return redirect(url_for('staff_enrollment_acceptance.view_enrollment_requests'))

    new_status = 'enrolled' if action == 'accept' else 'rejected'

    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        UPDATE enrollment SET status = %s WHERE enrollment_id = %s
    """, (new_status, enrollment_id))
    db.commit()

    flash(f"Enrollment request has been {new_status}.")
    return redirect(url_for('staff_enrollment_acceptance.view_enrollment_requests'))
