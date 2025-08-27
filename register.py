from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
import re
from database import get_db

register = Blueprint('register', __name__)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

@register.route('/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
      
        form_data = {
            'username': request.form['username'],
            'email': request.form['email'],
            'role': request.form.get('role', 'student'),
            'first_name': request.form['first_name'],
            'middle_name': request.form.get('middle_name', ''),
            'last_name': request.form['last_name'],
            'date_of_birth': request.form['date_of_birth'],
            'gender': request.form['gender'],
            'province': request.form['province'],
            'municipality': request.form['municipal'],
            'baranggay': request.form['barangay'],
            'contact_number': request.form['contact_number'],
            'terms_accepted': 'terms' in request.form
        }
        
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        errors = []
        
        password_validation = {
            'min_length': len(password) >= 8,
            'has_upper': any(c.isupper() for c in password),
            'has_lower': any(c.islower() for c in password),
            'has_number': any(c.isdigit() for c in password),
            'has_special': any(not c.isalnum() for c in password)
        }
        
        if not all(password_validation.values()):
            errors.append("Password must contain: 8+ characters, uppercase, lowercase, number, and special character")
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if not EMAIL_REGEX.match(form_data['email']):
            errors.append("Invalid email format")
        
        if not form_data['terms_accepted']:
            errors.append("You must accept the terms and conditions")
        
        try:
            dob = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date()
            if dob >= date.today():
                errors.append("Date of birth must be in the past")
        except ValueError:
            errors.append("Invalid date format (YYYY-MM-DD)")
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('all/register.html', 
                                 datetime=datetime, 
                                 date=date,
                                 form_data=form_data,
                                 password_errors=password_validation)
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            
            cursor.execute("SELECT * FROM login WHERE username = %s OR email = %s", 
                          (form_data['username'], form_data['email']))
            if cursor.fetchone():
                flash("Username or email already exists", 'danger')
                return render_template('all/register.html', 
                                     datetime=datetime, 
                                     date=date,
                                     form_data=form_data)
            
            cursor.execute(
                "INSERT INTO login (username, password, email, role, account_status) VALUES (%s, %s, %s, %s, %s)",
                (form_data['username'], password, form_data['email'], form_data['role'], 'pending')
            )
            user_id = cursor.lastrowid
            
            cursor.execute(
                """INSERT INTO personal_information 
                (user_id, province, municipality, baranggay, contact_number, 
                 first_name, middle_name, last_name, date_of_birth, gender, terms_accepted) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, form_data['province'], form_data['municipality'], form_data['baranggay'], 
                 form_data['contact_number'], form_data['first_name'], form_data['middle_name'], 
                 form_data['last_name'], form_data['date_of_birth'], form_data['gender'], 
                 int(form_data['terms_accepted']))
            )
            
            db.commit()
            flash("Registration successful! Your account is pending approval.", 'success')
            return render_template('all/register.html', 
                                 datetime=datetime, 
                                 date=date,
                                 form_data={},
                                 registration_success=True)
            
        except Exception as e:
            db.rollback()
            flash(f"Registration failed: {str(e)}", 'danger')
            return render_template('all/register.html', 
                                 datetime=datetime, 
                                 date=date,
                                 form_data=form_data)
            
        finally:
            cursor.close()
    
    return render_template('all/register.html', 
                         datetime=datetime, 
                         date=date,
                         form_data={})

@register.route('/check_username', methods=['POST'])
def check_username():
    username = request.json.get('username')
    if not username:
        return jsonify({'available': False, 'message': 'Username is required'})
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM login WHERE username = %s", (username,))
    exists = cursor.fetchone() is not None
    cursor.close()
    
    return jsonify({
        'available': not exists, 
        'message': 'Username already taken' if exists else 'Username available'
    })

@register.route('/check_email', methods=['POST'])
def check_email():
    email = request.json.get('email')
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    if not EMAIL_REGEX.match(email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM login WHERE email = %s", (email,))
    exists = cursor.fetchone() is not None
    cursor.close()
    
    return jsonify({
        'available': not exists, 
        'message': 'Email already registered' if exists else 'Email available'
    })