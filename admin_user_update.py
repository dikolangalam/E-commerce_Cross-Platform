from flask import Blueprint, render_template, request, jsonify, current_app
from flask_mail import Message
from database import get_db

admin_user_update_bp = Blueprint('admin_user_update', __name__)

@admin_user_update_bp.route('/get_active_users', methods=['GET'])
def get_active_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                l.user_id, 
                l.username, 
                l.email, 
                l.role, 
                l.account_status,
                p.first_name, 
                COALESCE(p.middle_name, '') AS middle_name,
                p.last_name,
                p.province,
                p.municipality,
                p.baranggay,
                p.contact_number,
                p.date_of_birth,
                p.gender,
                p.date_registered,
                p.terms_accepted
            FROM login l
            INNER JOIN personal_information p ON l.user_id = p.user_id
            WHERE l.account_status != 'pending'
              AND l.role != 'admin'
            ORDER BY p.date_registered DESC
        """)
        active_users = cursor.fetchall()
        
        for user in active_users:
            user['date_registered'] = user['date_registered'].strftime('%Y-%m-%d %H:%M:%S')
            user['date_of_birth'] = user['date_of_birth'].strftime('%Y-%m-%d') if user['date_of_birth'] else 'Not specified'
            user['full_name'] = f"{user['first_name']} {user['middle_name'] + ' ' if user['middle_name'] else ''}{user['last_name']}"
        
        return jsonify({'success': True, 'users': active_users})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error fetching active users: {str(e)}"}), 500
        
    finally:
        cursor.close()

@admin_user_update_bp.route('/update_user', methods=['POST'])
def update_user():
    data = request.get_json()
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'message': 'Missing user_id'}), 400
    
    required_fields = ['first_name', 'last_name', 'email']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        db.start_transaction()
        
        cursor.execute("""
            SELECT 
                l.user_id, 
                l.role, 
                l.account_status,
                p.terms_accepted
            FROM login l
            JOIN personal_information p ON l.user_id = p.user_id 
            WHERE l.user_id = %s FOR UPDATE
        """, (user_id,))
        
        user_record = cursor.fetchone()
        
        if not user_record:
            db.rollback()
            return jsonify({'success': False, 'message': 'User not found'}), 404

        original_role = user_record['role']
        original_status = user_record['account_status']
        original_terms = user_record['terms_accepted']

        if 'password' in data and data['password']:
            cursor.execute("""
                UPDATE login 
                SET 
                    email = %s,
                    password = %s
                WHERE user_id = %s
            """, (
                data['email'],
                data['password'],
                user_id
            ))
        else:
            cursor.execute("""
                UPDATE login 
                SET 
                    email = %s
                WHERE user_id = %s
            """, (
                data['email'],
                user_id
            ))
        
        cursor.execute("""
            UPDATE personal_information 
            SET 
                first_name = %s,
                middle_name = %s,
                last_name = %s,
                contact_number = %s,
                date_of_birth = %s,
                gender = %s,
                province = %s,
                municipality = %s,
                baranggay = %s
            WHERE user_id = %s
        """, (
            data['first_name'],
            data['middle_name'] if data['middle_name'] else None,
            data['last_name'],
            data['contact_number'] if data['contact_number'] else None,
            data['date_of_birth'] if data['date_of_birth'] else None,
            data['gender'] if data['gender'] else None,
            data['province'],
            data['municipality'],
            data['baranggay'],
            user_id
        ))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'protected_fields': {
                'role': original_role,
                'account_status': original_status,
                'terms_accepted': original_terms
            }
        })
        
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Error in update_user: {str(e)}")
        return jsonify({'success': False, 'message': f"Error updating user: {str(e)}"}), 500
        
    finally:
        cursor.close()

@admin_user_update_bp.route('/search_users', methods=['GET'])
def search_users():
    query = request.args.get('q', '').strip()
    role_filter = request.args.get('role', 'all').lower()
    db = None
    cursor = None

    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        sql = """
            SELECT 
                l.user_id, 
                l.username, 
                l.email, 
                l.role, 
                l.account_status,
                p.first_name, 
                COALESCE(p.middle_name, '') AS middle_name,
                p.last_name,
                p.province,
                p.municipality,
                p.baranggay,
                p.contact_number,
                p.date_of_birth,
                p.gender,
                p.date_registered,
                p.terms_accepted
            FROM login l
            INNER JOIN personal_information p ON l.user_id = p.user_id
            WHERE l.account_status != 'pending'
              AND l.role != 'admin'
              AND (
                  l.username LIKE %s OR
                  l.email LIKE %s OR
                  p.first_name LIKE %s OR
                  p.middle_name LIKE %s OR
                  p.last_name LIKE %s
              )
        """

        params = ['%' + query + '%'] * 5

        if role_filter in ['staff', 'student']:
            sql += " AND l.role = %s"
            params.append(role_filter)

        cursor.execute(sql, params)
        users = cursor.fetchall()

        for user in users:
            user['date_registered'] = user['date_registered'].strftime('%Y-%m-%d %H:%M:%S')
            user['date_of_birth'] = user['date_of_birth'].strftime('%Y-%m-%d') if user['date_of_birth'] else 'Not specified'
            user['full_name'] = f"{user['first_name']} {user['middle_name'] + ' ' if user['middle_name'] else ''}{user['last_name']}"

        return jsonify({'success': True, 'users': users})

    except Exception as e:
        current_app.logger.error(f"Error searching users: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching search results'}), 500

    finally:
        if cursor: cursor.close()
        if db: db.close()
