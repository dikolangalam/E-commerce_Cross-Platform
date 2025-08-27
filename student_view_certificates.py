from flask import Blueprint, render_template, request, redirect, url_for, session, send_from_directory
from database import get_db
import os

student_view_certificates_bp = Blueprint('student_view_certificates', __name__)

# Folder where generated certificates are stored
CERT_DIR = os.path.join('static', 'certs')

@student_view_certificates_bp.route('/student/certificates')
def student_view_certificates():
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect('/login')

    user_id = session['user_id']

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Fetch certificates only for this student where remarks is 'Completed'
    query = """
        SELECT c.course AS class_title, c.date, c.file_path
        FROM certificates c
        JOIN enrollment e ON c.enrollment_id = e.enrollment_id
        JOIN student_grades sg ON e.enrollment_id = sg.enrollment_id
        WHERE e.user_id = %s AND sg.remarks = 'Completed'
    """
    cursor.execute(query, (user_id,))
    certificates = cursor.fetchall()

    return render_template('students/student_view_certificates.html', certificates=certificates)

@student_view_certificates_bp.route('/download_certificate/<path:filename>')
def download_certificate(filename):
    if 'user_id' not in session or session.get('role') != 'student':
        return redirect('/login')
    
    return send_from_directory(CERT_DIR, filename, as_attachment=True)
