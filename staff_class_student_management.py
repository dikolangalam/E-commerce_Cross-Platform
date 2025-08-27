from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from database import get_db

staff_class_student_management_bp = Blueprint('staff_class_student_management', __name__)

@staff_class_student_management_bp.route('/staff_class/<int:class_id>/students', methods=['GET'])
def view_class_students(class_id):
    if 'user_id' not in session or session.get('role') != 'staff':
        return jsonify({'error': 'Unauthorized access'}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT 
            pi.first_name, 
            pi.last_name, 
            l.email, 
            l.user_id AS user_id, 
            sg.prelim_grade, 
            sg.midterm_grade, 
            sg.final_grade, 
            sg.remarks,
            e.enrollment_id,
            (
                SELECT 
                    ROUND(SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2)
                FROM student_attendance sa
                WHERE sa.enrollment_id = e.enrollment_id
            ) AS attendance_percentage
        FROM enrollment e
        JOIN login l ON e.user_id = l.user_id
        JOIN personal_information pi ON l.user_id = pi.user_id
        LEFT JOIN student_grades sg ON e.enrollment_id = sg.enrollment_id
        WHERE e.class_id = %s AND e.status = 'enrolled'
    """
    cursor.execute(query, (class_id,))
    students = cursor.fetchall()

    print(students)  

    return render_template('staffs/staff_class_student_management.html', students=students, class_id=class_id)

@staff_class_student_management_bp.route('/staff_student/edit_grade', methods=['POST'])
def edit_student_grade():
    if 'user_id' not in session or session.get('role') != 'staff':
        return jsonify({'error': 'Unauthorized access'}), 403

    data = request.json
    enrollment_id = data.get('enrollment_id')
    prelim = data.get('prelim_grade')
    midterm = data.get('midterm_grade')
    final = data.get('final_grade')
    remarks = data.get('remarks')
    attendance_updates = data.get('attendance_updates', [])

    db = get_db()
    cursor = db.cursor()

    # Check if grade exists
    cursor.execute("SELECT * FROM student_grades WHERE enrollment_id = %s", (enrollment_id,))
    grade = cursor.fetchone()

    if grade:
        # Update student_grades
        cursor.execute("""
            UPDATE student_grades
            SET prelim_grade=%s, midterm_grade=%s, final_grade=%s, remarks=%s, date_recorded=NOW()
            WHERE enrollment_id=%s
        """, (prelim, midterm, final, remarks, enrollment_id))
    else:
        # Insert new grade record
        cursor.execute("""
            INSERT INTO student_grades (enrollment_id, prelim_grade, midterm_grade, final_grade, remarks)
            VALUES (%s, %s, %s, %s, %s)
        """, (enrollment_id, prelim, midterm, final, remarks))

    # Handle attendance updates
    for attendance in attendance_updates:
        attendance_id = attendance.get('attendance_id')
        attendance_date = attendance.get('attendance_date')
        status = attendance.get('status')

        if attendance_id == 'new':
            cursor.execute("""
                INSERT INTO student_attendance (enrollment_id, attendance_date, status)
                VALUES (%s, %s, %s)
            """, (enrollment_id, attendance_date, status))
        else:
            cursor.execute("""
                UPDATE student_attendance
                SET attendance_date=%s, status=%s
                WHERE attendance_id=%s AND enrollment_id=%s
            """, (attendance_date, status, attendance_id, enrollment_id))

    db.commit()

    return jsonify({'message': 'Grade, remarks, and attendance updated successfully'})


@staff_class_student_management_bp.route('/staff_student_profile/<int:user_id>', methods=['GET'])
def get_student_profile(user_id):
    if 'user_id' not in session or session.get('role') != 'staff':
        return jsonify({'error': 'Unauthorized access'}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            pi.first_name, pi.middle_name, pi.last_name,
            pi.date_of_birth, pi.gender, pi.province, pi.municipality,
            pi.baranggay, pi.contact_number, pi.profile_picture,
            l.email
        FROM personal_information pi
        JOIN login l ON pi.user_id = l.user_id
        WHERE pi.user_id = %s
    """, (user_id,))
    profile = cursor.fetchone()

    if not profile:
        return jsonify({'error': 'Student profile not found'}), 404

    return jsonify(profile)

@staff_class_student_management_bp.route('/staff_student/get_attendance/<int:enrollment_id>', methods=['GET'])
def get_attendance(enrollment_id):
    if 'user_id' not in session or session.get('role') != 'staff':
        return jsonify({'error': 'Unauthorized access'}), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT attendance_id, attendance_date, status
        FROM student_attendance
        WHERE enrollment_id = %s
    """, (enrollment_id,))
    attendance = cursor.fetchall()

    return jsonify({'attendance': attendance})

