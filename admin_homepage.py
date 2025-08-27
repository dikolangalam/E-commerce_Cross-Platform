from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from database import get_db

admin_homepage_bp = Blueprint('admin_homepage', __name__)

@admin_homepage_bp.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('You need to login as admin first', 'error')
        return redirect(url_for('login.login_page'))
    return render_template('admin/dashboard.html')

@admin_homepage_bp.route('/admin/dashboard/data')
def dashboard_data():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    try:
       
        cursor.execute("""
            SELECT 
                role,
                COUNT(*) as count
            FROM 
                login
            WHERE 
                account_status = 'active'
                AND role != 'admin'
            GROUP BY 
                role
        """)
        role_counts = cursor.fetchall()
        
        role_stats = {role: count for role, count in role_counts}
        total_staff = role_stats.get('staff', 0)
        total_students = role_stats.get('student', 0)
        total_non_admin = total_staff + total_students
        
        cursor.execute("""
            SELECT 
                p.gender,
                COUNT(*) as count
            FROM 
                personal_information p
            JOIN 
                login l ON p.user_id = l.user_id
            WHERE 
                l.account_status = 'active'
                AND l.role != 'admin'
            GROUP BY 
                p.gender
        """)
        gender_counts = cursor.fetchall()
        
        gender_stats = {gender: count for gender, count in gender_counts}
        male_count = gender_stats.get('male', 0)
        female_count = gender_stats.get('female', 0)
        other_count = gender_stats.get('other', 0)
        
        cursor.execute("SELECT COUNT(*) FROM login WHERE account_status = 'pending'")
        pending_count = cursor.fetchone()[0]
        
        return jsonify({
            'total_staff': total_staff,
            'total_students': total_students,
            'total_non_admin': total_non_admin,
            'male_count': male_count,
            'female_count': female_count,
            'other_count': other_count,
            'pending_count': pending_count
        })
    
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()