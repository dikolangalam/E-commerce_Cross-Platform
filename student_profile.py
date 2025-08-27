from flask import Blueprint, request, jsonify, session, current_app, url_for
from database import get_db
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import traceback

student_profile_bp = Blueprint('student_profile', __name__, url_prefix='/student')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@student_profile_bp.route('/profile', methods=['GET'])
def student_profile():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized access'}), 401

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        query = """
            SELECT l.user_id, l.username, l.email, l.role, l.account_status,
                   pi.info_id, pi.first_name, pi.middle_name, pi.last_name,
                   pi.province, pi.municipality, pi.baranggay,
                   pi.contact_number, pi.date_of_birth, pi.gender,
                   pi.profile_picture, pi.date_registered
            FROM login l
            JOIN personal_information pi ON l.user_id = pi.user_id
            WHERE l.user_id = %s
        """
        cursor.execute(query, (user_id,))
        student_data = cursor.fetchone()

        if not student_data:
            return jsonify({'error': 'Student profile not found'}), 404

        # Format date fields to string (if they exist)
        student_data['date_of_birth'] = student_data['date_of_birth'].strftime('%Y-%m-%d') if student_data['date_of_birth'] else None
        student_data['date_registered'] = student_data['date_registered'].strftime('%Y-%m-%d %H:%M:%S') if student_data['date_registered'] else None

        # Construct profile picture URL
        student_data['profile_picture_url'] = url_for(
            'static',
            filename=f"uploads/profile_pictures/{student_data['profile_picture']}",
            _external=True
        ) if student_data['profile_picture'] else None

        return jsonify({'success': True, 'student': student_data})

    except Exception as e:
        current_app.logger.error(f"Error fetching student profile: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to fetch profile data'}), 500
    finally:
        cursor.close()

@student_profile_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session or session.get('role') != 'student':
        return jsonify({'error': 'Unauthorized access'}), 401

    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        data = request.form.to_dict() if request.form else {}
        files = request.files

        if not data:
            return jsonify({'error': 'No form data received'}), 400

        username = data.get('username')
        email = data.get('email')
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        first_name = data.get('first_name')
        middle_name = data.get('middle_name')
        last_name = data.get('last_name')
        contact_number = data.get('contact_number')
        province = data.get('province')
        municipality = data.get('municipality')
        baranggay = data.get('baranggay')
        date_of_birth = data.get('date_of_birth')
        gender = data.get('gender')

        cursor.execute("SELECT password, username, email FROM login WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        if username and username != user['username']:
            cursor.execute("SELECT user_id FROM login WHERE username = %s AND user_id != %s", (username, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'Username already taken'}), 400

        if email and email != user['email']:
            cursor.execute("SELECT user_id FROM login WHERE email = %s AND user_id != %s", (email, user_id))
            if cursor.fetchone():
                return jsonify({'error': 'Email already in use'}), 400

        profile_picture = None
        if 'profile_picture' in files:
            file = files['profile_picture']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{user_id}_{uuid.uuid4().hex}.{ext}"

                upload_dir = os.path.join(current_app.static_folder, 'uploads', 'profile_pictures')
                os.makedirs(upload_dir, exist_ok=True)

                file.save(os.path.join(upload_dir, secure_filename(filename)))
                profile_picture = filename

                cursor.execute("SELECT profile_picture FROM personal_information WHERE user_id = %s", (user_id,))
                old_picture = cursor.fetchone()
                if old_picture and old_picture['profile_picture']:
                    old_filepath = os.path.join(upload_dir, old_picture['profile_picture'])
                    if os.path.exists(old_filepath):
                        try:
                            os.remove(old_filepath)
                        except Exception as e:
                            current_app.logger.error(f"Error deleting old profile picture: {str(e)}")

        password_update = ""
        password_params = ()
        if current_password and new_password and confirm_password:
            if current_password != user['password']:
                return jsonify({'error': 'Current password is incorrect'}), 400

            if new_password != confirm_password:
                return jsonify({'error': 'New passwords do not match'}), 400

            if len(new_password) < 4:
                return jsonify({'error': 'Password must be at least 4 characters'}), 400

            password_update = ", password = %s"
            password_params = (new_password,)

        update_login_query = f"""
            UPDATE login 
            SET username = %s, email = %s {password_update}
            WHERE user_id = %s
        """
        cursor.execute(
            update_login_query,
            (username or user['username'],
             email or user['email']) + password_params + (user_id,)
        )

        update_fields = {
            'first_name': first_name or '',
            'middle_name': middle_name or '',
            'last_name': last_name or '',
            'contact_number': contact_number or '',
            'province': province or '',
            'municipality': municipality or '',
            'baranggay': baranggay or '',
            'gender': gender or '',
            'user_id': user_id
        }

        try:
            update_fields['date_of_birth'] = datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        if profile_picture:
            update_fields['profile_picture'] = profile_picture

        update_personal_query = """
            UPDATE personal_information 
            SET 
                first_name = %(first_name)s,
                middle_name = %(middle_name)s,
                last_name = %(last_name)s,
                contact_number = %(contact_number)s,
                province = %(province)s,
                municipality = %(municipality)s,
                baranggay = %(baranggay)s,
                date_of_birth = %(date_of_birth)s,
                gender = %(gender)s
                {profile_picture_update}
            WHERE user_id = %(user_id)s
        """.format(
            profile_picture_update=", profile_picture = %(profile_picture)s" if profile_picture else ""
        )

        cursor.execute(update_personal_query, update_fields)
        db.commit()

        cursor.execute("""
            SELECT l.username, l.email, l.role, l.account_status,
                   pi.first_name, pi.middle_name, pi.last_name,
                   pi.province, pi.municipality, pi.baranggay,
                   pi.contact_number, pi.date_of_birth, pi.gender,
                   pi.profile_picture, pi.date_registered
            FROM login l
            JOIN personal_information pi ON l.user_id = pi.user_id
            WHERE l.user_id = %s
        """, (user_id,))
        updated_profile = cursor.fetchone()

        if not updated_profile:
            return jsonify({'error': 'Failed to fetch updated profile'}), 500

        updated_profile['date_of_birth'] = updated_profile['date_of_birth'].strftime('%Y-%m-%d') if updated_profile['date_of_birth'] else None
        updated_profile['date_registered'] = updated_profile['date_registered'].strftime('%Y-%m-%d %H:%M:%S') if updated_profile['date_registered'] else None

        updated_profile['profile_picture_url'] = url_for(
            'static',
            filename=f"uploads/profile_pictures/{updated_profile['profile_picture']}",
            _external=True
        ) if updated_profile['profile_picture'] else None

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'updated_profile': updated_profile
        })

    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Error updating student profile: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to update profile'}), 500
    finally:
        cursor.close()