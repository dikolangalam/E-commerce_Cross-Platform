from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import get_db

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier'] 
        password = request.form['password']
        
        db = get_db()
        cursor = db.cursor(dictionary=True)
        
        try:
           
            cursor.execute("""
                SELECT * FROM login 
                WHERE (username = %s OR email = %s) 
                AND password = %s
            """, (identifier, identifier, password))
            
            user = cursor.fetchone()
            
            if user:
               
                if user['account_status'] == 'pending':
                    flash('Your account is still pending approval. Please wait for administrator approval.', 'login_pending_message')
                    return redirect(url_for('login.login'))
                
                if user['account_status'] == 'inactive':
                    flash('Your account is inactive. Please contact support.', 'login_inactive_message')
                    return redirect(url_for('login.login'))
                
                session['user_id'] = user['user_id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['logged_in'] = True
                
                cursor.execute("""
                    SELECT first_name, last_name FROM personal_information 
                    WHERE user_id = %s
                """, (user['user_id'],))
                personal_info = cursor.fetchone()
                
                if personal_info:
                    session['full_name'] = f"{personal_info['first_name']} {personal_info['last_name']}"
                
                if user['role'] == 'admin':
                    flash('Login successful!', 'login_success_message')
                    return redirect(url_for('admin_homepage'))
                
                elif user['role'] == 'staff':
                    flash('Login successful!', 'login_success_message')
                    return redirect(url_for('staff_homepage'))
                
                elif user['role'] == 'student':
                    flash('Login successful!', 'login_success_message')
                    return redirect(url_for('student_homepage'))
                
                else:
                    flash('Invalid user role.', 'login_role_error')
                    return redirect(url_for('login.login'))
            
            else:
                flash('Invalid username/email or password', 'login_credentials_error')
                return redirect(url_for('login.login'))
        
        except Exception as e:
            db.rollback()
            flash('An error occurred during login. Please try again.', 'login_system_error')
            return redirect(url_for('login.login'))
        
        finally:
            cursor.close()
    
    return render_template("all/login.html")

@login_bp.route('/logout')
def logout():
   
    session.clear()
    flash('You have been logged out.', 'logout_message')
    return redirect(url_for('login.login'))