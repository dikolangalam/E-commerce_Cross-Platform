from flask import Flask, render_template, request, redirect, flash, session, jsonify
import os
import hashlib  
from datetime import datetime, timedelta

from flask import Flask, render_template
from flask_cors import CORS
from flask_mail import Mail
from database import close_connection

#General BP
from register import register
from login import login_bp
from forgot_password import forgot_password_bp

#Blockchain BP
from cert_generator import create_certificate, get_certificate_hash
from blockchain import register_certificate, verify_certificate
from database import save_certificate, search_certificates_by_name
from database import get_db


#Admin BP
from admin_homepage import admin_homepage_bp
from admin_user_management import admin_user_management_bp
from admin_user_update import admin_user_update_bp
from admin_user_deletion import admin_user_deletion_bp
from admin_user_archive import admin_user_archive_bp
from admin_profile import admin_profile_bp
from admin_courses_approval import admin_courses_approval_bp
from admin_courses_avail import admin_courses_avail_bp
from admin_courses_edit_req import admin_courses_edit_req_bp
from admin_class_management import admin_class_management_bp
from admin_class_approval import admin_class_approval_bp
from admin_class_edit_req import admin_class_edit_req_bp

#Staff BP
from staff_profile import staff_profile_bp
from staff_courses_creation import staff_courses_creation_bp
from staff_courses_edit_req import staff_courses_edit_req_bp
from staff_courses_view import staff_courses_view_bp
from staff_class_management import staff_class_management_bp
from staff_class_creation import staff_class_creation_bp
from staff_class_edit_req import staff_class_edit_req_bp
from staff_class_student_management import staff_class_student_management_bp
from staff_enrollment_acceptance import staff_enrollment_acceptance_bp
from staff_class_certificates import staff_class_certificates_bp

#Student BP
from student_profile import student_profile_bp
from student_enrollment import student_enrollment_bp
from student_view_class import student_view_class_bp
from student_view_certificates import student_view_certificates_bp
from student_view_grades import student_view_grades_bp
from student_homepage import student_homepage_bp

app = Flask(__name__)
app.secret_key = 'your-secret-key' 
CORS(app)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'marwindalin01@gmail.com'
app.config['MAIL_PASSWORD'] = 'xctm qtyg trwc cjxq'

mail = Mail(app)

#General BP
app.register_blueprint(register)
app.register_blueprint(login_bp)
app.register_blueprint(forgot_password_bp)

#Admin BP
app.register_blueprint(admin_homepage_bp)
app.register_blueprint(admin_user_management_bp, url_prefix='/admin/user-management')
app.register_blueprint(admin_user_update_bp)
app.register_blueprint(admin_user_deletion_bp)
app.register_blueprint(admin_user_archive_bp)
app.register_blueprint(admin_profile_bp, url_prefix='/admin')
app.register_blueprint(admin_courses_approval_bp)
app.register_blueprint(admin_courses_avail_bp)
app.register_blueprint(admin_courses_edit_req_bp)
app.register_blueprint(admin_class_management_bp)
app.register_blueprint(admin_class_approval_bp)
app.register_blueprint(admin_class_edit_req_bp)

#Staff BP
app.register_blueprint(staff_profile_bp, url_prefix='/staff')
app.register_blueprint(staff_courses_creation_bp)
app.register_blueprint(staff_courses_edit_req_bp)
app.register_blueprint(staff_courses_view_bp)
app.register_blueprint(staff_class_management_bp)
app.register_blueprint(staff_class_creation_bp)
app.register_blueprint(staff_class_edit_req_bp)
app.register_blueprint(staff_class_student_management_bp)
app.register_blueprint(staff_enrollment_acceptance_bp)
app.register_blueprint(staff_class_certificates_bp)

#Student BP
app.register_blueprint(student_profile_bp, url_prefix='/student')
app.register_blueprint(student_enrollment_bp)
app.register_blueprint(student_view_class_bp)
app.register_blueprint(student_view_certificates_bp)
app.register_blueprint(student_view_grades_bp)
app.register_blueprint(student_homepage_bp)

#Blockchain
CERT_DIR = os.path.join("static", "certs")
os.makedirs(CERT_DIR, exist_ok=True)

@app.teardown_appcontext
def teardown_db(exception):
    close_connection(exception)

#General Route
@app.route("/")
def landing():
    return render_template("all/landing_page.html")

@app.route("/register")
def register():
    return render_template("all/register.html")

@app.route("/login")
def login():
    return render_template("all/login.html")

@app.route("/forgot_password")
def forgot_password():
    return render_template("all/forgot_password.html")

@app.route("/program")
def program():
    return render_template("all/program.html")

#Admin
@app.route("/admin_homepage")
def admin_homepage():
    return render_template("admin/admin_homepage.html")

@app.route("/admin_user_management")
def admin_user_management():
    return render_template("admin/admin_user_management.html")

@app.route("/admin_user_update")
def admin_user_update():
    return render_template("admin/admin_user_update.html")

@app.route("/admin_user_deletion")
def admin_user_deletion():
    return render_template("admin/admin_user_deletion.html")

@app.route("/admin_user_archive")
def admin_user_archive():
    return render_template("admin/admin_user_archive.html")

@app.route("/admin_courses_approval")
def admin_courses_approval():
    return render_template("admin/admin_courses_approval.html")

@app.route("/admin_courses_avail")
def admin_courses_avail():
    return render_template("admin/admin_courses_avail.html")

@app.route("/admin_courses_edit_req")
def admin_courses_edit_req():
    return render_template("admin/admin_courses_edit_req.html")

@app.route("/admin_profile")
def admin_profile():
    return render_template("admin/admin_profile.html")

@app.route("/admin_class_management")
def admin_class_management():
    return render_template("admin/admin_class_management.html")

@app.route("/admin_class_approval")
def admin_class_approval():
    return render_template("admin/admin_class_approval.html")

@app.route("/admin_class_edit_req")
def admin_class_edit_req():
    return render_template("admin/admin_class_edit_req.html")

#Staffs
@app.route("/staff_homepage")
def staff_homepage():
    return render_template("staffs/staff_homepage.html")

@app.route("/staff_profile")
def staff_profile():
    return render_template("staffs/staff_profile.html")

@app.route("/staff_courses_creation")
def staff_courses_creation():
    return render_template("staffs/staff_courses_creation.html")

@app.route("/staff_courses_edit_req")
def staff_courses_edit_req():
    return render_template("staffs/staff_courses_edit_req.html")

@app.route("/staff_courses_view")
def staff_courses_view():
    return render_template("staffs/staff_courses_view.html")

@app.route("/staff_class_management")
def staff_class_management():
    return render_template("staffs/staff_class_management.html")

@app.route("/staff_class_creation")
def staff_class_creation():
    return render_template("staffs/staff_class_creation.html")

@app.route("/staff_class_edit_req")
def staff_class_edit_req():
    return render_template("staffs/staff_class_edit_req.html")

@app.route("/staff_class_student_management")
def staff_class_student_management():
    return render_template("staffs/staff_class_student_management.html")

@app.route("/staff_enrollment_acceptance")
def staff_enrollment_acceptance():
    return render_template("staffs/staff_enrollment_acceptance.html")

# @app.route('/class_certificates')
# def staff_class_certificates():
#     return render_template('staffs/staff_class_certificates.html')

#Students
@app.route("/student_homepage")
def student_homepage():
    return render_template("students/student_homepage.html")

@app.route("/student_profile")
def student_profile():
    return render_template("students/student_profile.html")

@app.route("/student_enrollment")
def student_enrollment():
    return render_template("students/student_enrollment.html")

@app.route("/student_view_class")
def student_view_class():
    return render_template("students/student_view_class.html")

@app.route("/student_view_certificates")
def student_view_certificates():
    return render_template("students/student_view_certificates.html")

@app.route("/student_view_grades")
def student_view_grades():
    return render_template("students/student_view_grades.html")

#=============== blockchain =================
@app.route('/generate', methods=['POST'])
def generate():
    if 'user_id' not in session or 'role' not in session:
        return redirect('/login')

    if session['role'] != 'staff':
        flash("Unauthorized access. Only staff can generate certificates.", "error")
        return redirect('/unauthorized')

    try:
        # Get form data
        enrollment_id = request.form['enrollment_id']
        organization_name = request.form['name']  # Using 'name' from form as organization_name
        competency = request.form['course']      # Using 'course' from form as competency
        date_accredited = request.form['date']   # Using 'date' from form as date_accredited
        
        # Set default values for TESDA-specific fields
        organization_address = "229 A.MABINI ST. POBLACION II STA. CRUZ, LAGUNA"
        accreditation_no = f"AC-{hashlib.md5(f'{organization_name}{competency}'.encode()).hexdigest()[:16].upper()}"
        expiration_date = (datetime.strptime(date_accredited, '%Y-%m-%d') + timedelta(days=730)).strftime('%Y-%m-%d')

        # Sanitize filename
        sanitized_org = organization_name.replace(' ', '_')
        sanitized_comp = competency.replace(' ', '_')
        cert_filename = f"TESDA_Accreditation_{sanitized_org}_{sanitized_comp}.pdf"
        cert_path = os.path.join(CERT_DIR, cert_filename)

        # Create TESDA certificate
        create_certificate(
            organization_name=organization_name,
            organization_address=organization_address,
            competency=competency,
            accreditation_no=accreditation_no,
            date_accredited=date_accredited,
            expiration_date=expiration_date,
            filename=cert_path
        )

        # Generate hash and register on blockchain
        cert_hash = get_certificate_hash(cert_path)
        tx_hash = register_certificate(organization_name, competency, cert_hash)

        if tx_hash:
            file_path = os.path.join("certs", cert_filename).replace('\\', '/')
            save_certificate(
                enrollment_id=enrollment_id,
                name=organization_name,
                course=competency,
                date=date_accredited,
                cert_hash=cert_hash,
                tx_hash=tx_hash,
                file_path=file_path
            )
            flash(f"TESDA Accreditation Certificate created and recorded on blockchain! TX: {tx_hash}")
        else:
            flash("Failed to record certificate on blockchain. See logs for details.", "error")

    except Exception as e:
        flash(f"Error generating certificate: {str(e)}", "error")
        return redirect('/class_certificates')

    return redirect('/class_certificates')

@app.route('/class_certificates')
def staff_class_certificates():
    db = get_db()
    cursor = db.cursor(dictionary=True)

    query = """
        SELECT e.enrollment_id, c.class_title, 
               CONCAT(pi.first_name, ' ', pi.last_name) AS user_fullname
        FROM enrollment e
        JOIN classes c ON e.class_id = c.class_id
        JOIN personal_information pi ON e.user_id = pi.user_id
        JOIN student_grades sg ON e.enrollment_id = sg.enrollment_id
        WHERE sg.remarks = 'Completed'
    """
    cursor.execute(query)
    enrollments = cursor.fetchall()

    return render_template('staffs/staff_class_certificates.html', enrollments=enrollments)

# --- Verify Certificate ---
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'user_id' not in session:
        return redirect('/login')

    result = None
    if request.method == 'POST':
        cert_file = request.files['cert_file']
        file_path = os.path.join(CERT_DIR, cert_file.filename)
        cert_file.save(file_path)
        cert_hash = get_certificate_hash(file_path)
        result = verify_certificate(cert_hash)
    return render_template("staffs/verify.html", result=result)

# --- Search Certificates ---
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'user_id' not in session:
        return redirect('/login')

    results = None
    if request.method == 'POST':
        name = request.form['name']
        results = search_certificates_by_name(name)
    return render_template("staffs/search.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)