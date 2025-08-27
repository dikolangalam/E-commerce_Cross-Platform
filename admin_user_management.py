from flask import Blueprint, render_template, request, jsonify, current_app
from flask_mail import Message
from database import get_db

admin_user_management_bp = Blueprint('admin_user_management', __name__)

def send_approval_email(email, username):
    try:
        mail = current_app.extensions.get('mail')
        if not mail:
            current_app.logger.error("Mail extension not found")
            return False
            
        msg = Message(
            subject="LSEF TESDA - Account Approval Notification",
            sender=("LSEF TESDA", current_app.config['MAIL_USERNAME']), 
            recipients=[email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0056b3; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">LSEF TESDA</h1>
                </div>
                
                <div style="padding: 20px;">
                    <h2 style="color: #0056b3;">Account Approval Confirmation</h2>
                    <p>Dear {username},</p>
                    
                    <p>We are pleased to inform you that your account registration with <strong>LSEF TESDA</strong> has been successfully approved by our administration team.</p>
                    
                    <p>You may now access your account using your registered credentials to explore all the features and services available to you.</p>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #0056b3; margin: 15px 0;">
                        <p style="margin: 0;">Should you encounter any issues or have questions, please don't hesitate to contact our support team.</p>
                    </div>
                    
                    <p>Thank you for choosing LSEF TESDA. We look forward to serving you!</p>
                    
                    <p>Best regards,</p>
                    <p><strong>LSEF TESDA Administration Team</strong></p>
                </div>
                
                <div style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 12px;">
                    <p>This is an automated message. Please do not reply directly to this email.</p>
                </div>
            </div>
            """
        )
        mail.send(msg)
        current_app.logger.info(f"Approval email sent successfully to {email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending approval email to {email}: {str(e)}")
        return False

def send_rejection_email(email, username):
    try:
        mail = current_app.extensions.get('mail')
        if not mail:
            current_app.logger.error("Mail extension not found")
            return False
            
        msg = Message(
            subject="LSEF TESDA - Account Registration Update",
            sender=("LSEF TESDA", current_app.config['MAIL_USERNAME']),  
            recipients=[email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0056b3; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">LSEF TESDA</h1>
                </div>
                
                <div style="padding: 20px;">
                    <h2 style="color: #0056b3;">Account Registration Update</h2>
                    <p>Dear {username},</p>
                    
                    <p>We regret to inform you that after careful consideration, your account registration with <strong>LSEF TESDA</strong> has not been approved at this time.</p>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #0056b3; margin: 15px 0;">
                        <p style="margin: 0;">If you believe this decision was made in error or would like more information, please contact our support team for further assistance.</p>
                    </div>
                    
                    <p>Thank you for your interest in LSEF TESDA.</p>
                    
                    <p>Sincerely,</p>
                    <p><strong>LSEF TESDA Administration Team</strong></p>
                </div>
                
                <div style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 12px;">
                    <p>This is an automated message. Please do not reply directly to this email.</p>
                </div>
            </div>
            """
        )
        mail.send(msg)
        current_app.logger.info(f"Rejection email sent successfully to {email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending rejection email to {email}: {str(e)}")
        return False
    
@admin_user_management_bp.route('/user_management')
def user_management():
    return render_template('admin/user_management.html')

@admin_user_management_bp.route('/get_pending_users', methods=['GET'])
def get_pending_users():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                l.user_id, 
                l.username, 
                l.email, 
                l.role, 
                p.first_name, 
                COALESCE(p.middle_name, '') AS middle_name,
                p.last_name,
                p.province,
                p.municipality,
                p.baranggay,
                p.contact_number,
                p.date_of_birth,
                p.gender,
                p.date_registered
            FROM login l
            INNER JOIN personal_information p ON l.user_id = p.user_id
            WHERE l.account_status = 'pending'
            ORDER BY p.date_registered DESC
        """)
        pending_users = cursor.fetchall()
        
        for user in pending_users:
            user['date_registered'] = user['date_registered'].strftime('%Y-%m-%d %H:%M:%S')
            if user['date_of_birth']:
                user['date_of_birth'] = user['date_of_birth'].strftime('%Y-%m-%d')
            else:
                user['date_of_birth'] = 'Not specified'
            user['full_address'] = f"{user['baranggay']}, {user['municipality']}, {user['province']}"
            user['full_name'] = f"{user['first_name']} {user['middle_name'] + ' ' if user['middle_name'] else ''}{user['last_name']}"
        
        return jsonify({
            'success': True,
            'users': pending_users
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error fetching pending users: {str(e)}"
        }), 500
        
    finally:
        cursor.close()

@admin_user_management_bp.route('/update_user_status', methods=['POST'])
def update_user_status():
    data = request.get_json()
    user_id = data.get('user_id')
    new_status = data.get('status')
    
    if not user_id or not new_status:
        return jsonify({
            'success': False,
            'message': 'Missing user_id or status'
        }), 400
    
    if new_status not in ['active', 'inactive', 'pending']:
        return jsonify({
            'success': False,
            'message': 'Invalid status value'
        }), 400
    
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
       
        db.start_transaction()
        
        cursor.execute("""
            SELECT l.username, l.email, l.account_status
            FROM login l
            JOIN personal_information p ON l.user_id = p.user_id
            WHERE l.user_id = %s
            FOR UPDATE
        """, (user_id,))
        
        user_info = cursor.fetchone()
        if not user_info:
            db.rollback()
            return jsonify({
                'success': False,
                'message': 'User not found or missing personal information'
            }), 404

        if new_status == 'active':
            email_sent = send_approval_email(user_info['email'], user_info['username'])
            if not email_sent:
                db.rollback()
                current_app.logger.error(f"Failed to send approval email for user {user_id}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to send approval email. Account not approved.',
                    'email_sent': False
                }), 500

            cursor.execute("""
                UPDATE login 
                SET account_status = %s 
                WHERE user_id = %s
            """, (new_status, user_id))
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'User approved successfully and notification email sent',
                'email_sent': True
            })
        
        elif new_status == 'inactive':
            email_sent = send_rejection_email(user_info['email'], user_info['username'])
            if not email_sent:
                db.rollback()
                current_app.logger.error(f"Failed to send rejection email for user {user_id}")
                return jsonify({
                    'success': False,
                    'message': 'Failed to send rejection email. Account status not updated.',
                    'email_sent': False
                }), 500

            cursor.execute("""
                UPDATE login 
                SET account_status = %s 
                WHERE user_id = %s
            """, (new_status, user_id))
            db.commit()
            
            return jsonify({
                'success': True,
                'message': 'User rejected successfully and notification email sent',
                'email_sent': True
            })
        
        else:
            cursor.execute("""
                UPDATE login 
                SET account_status = %s 
                WHERE user_id = %s
            """, (new_status, user_id))
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'User status updated to {new_status} successfully',
                'email_sent': None
            })
        
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Error in update_user_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error updating user status: {str(e)}"
        }), 500
        
    finally:
        cursor.close()

@admin_user_management_bp.route('/get_user_details/<int:user_id>', methods=['GET'])
def get_user_details(user_id):
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
                p.middle_name,
                p.last_name,
                p.province,
                p.municipality,
                p.baranggay,
                p.contact_number,
                p.date_of_birth,
                p.gender,
                p.profile_picture,
                p.terms_accepted,
                p.date_registered
            FROM login l
            INNER JOIN personal_information p ON l.user_id = p.user_id
            WHERE l.user_id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        if user['date_of_birth']:
            user['date_of_birth'] = user['date_of_birth'].strftime('%Y-%m-%d')
        user['date_registered'] = user['date_registered'].strftime('%Y-%m-%d %H:%M:%S')
        
        user['full_address'] = f"{user['baranggay']}, {user['municipality']}, {user['province']}"
        
        return jsonify({
            'success': True,
            'user': user
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error fetching user details: {str(e)}"
        }), 500
        
    finally:
        cursor.close()

@admin_user_management_bp.route('/search_users', methods=['GET'])
def search_users():
    search_term = request.args.get('query', '').strip()
    role_filter = request.args.get('role', 'all')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    try:
        sql = """
            SELECT 
                l.user_id, l.username, l.email, l.role, 
                p.first_name, COALESCE(p.middle_name, '') AS middle_name, p.last_name,
                p.province, p.municipality, p.baranggay, p.contact_number,
                p.date_of_birth, p.gender, p.date_registered
            FROM login l
            INNER JOIN personal_information p ON l.user_id = p.user_id
            WHERE l.account_status = 'pending'
        """

        params = []

        if role_filter.lower() in ['staff', 'student']:
            sql += " AND l.role = %s"
            params.append(role_filter.lower())

        if search_term:
            sql += """
                AND (
                    l.username LIKE %s OR
                    l.email LIKE %s OR
                    p.first_name LIKE %s OR
                    p.middle_name LIKE %s OR
                    p.last_name LIKE %s
                )
            """
            like_term = f"%{search_term}%"
            params += [like_term] * 5

        sql += " ORDER BY p.date_registered DESC"
        cursor.execute(sql, tuple(params))
        results = cursor.fetchall()

        for user in results:
            user['date_registered'] = user['date_registered'].strftime('%Y-%m-%d %H:%M:%S')
            user['date_of_birth'] = user['date_of_birth'].strftime('%Y-%m-%d') if user['date_of_birth'] else 'Not specified'
            user['full_address'] = f"{user['baranggay']}, {user['municipality']}, {user['province']}"
            user['full_name'] = f"{user['first_name']} {user['middle_name']} {user['last_name']}".strip()

        return jsonify({'success': True, 'users': results})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()




