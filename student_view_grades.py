from flask import Blueprint, render_template, request, jsonify, session
from database import get_db

student_view_grades_bp = Blueprint('student_view_grades', __name__)

@student_view_grades_bp.route('/student/view_grades', methods=['GET'])
def view_grades():
    # Ensure student is logged in
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized access'}), 403

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT 
            co.course_code,
            co.course_title,
            sg.prelim_grade,
            sg.midterm_grade,
            sg.final_grade,
            sg.remarks
        FROM enrollment e
        JOIN classes c ON e.class_id = c.class_id
        JOIN courses co ON c.course_id = co.course_id
        LEFT JOIN student_grades sg ON e.enrollment_id = sg.enrollment_id
        WHERE e.user_id = %s AND e.status = 'enrolled'
    """

    cursor.execute(query, (user_id,))
    grades = cursor.fetchall()

    if not grades:
        return render_template('students/student_view_grades.html', grades=None, message="No grades available yet.")

    return render_template('students/student_view_grades.html', grades=grades)
