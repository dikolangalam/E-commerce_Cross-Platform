from flask import Blueprint, request, jsonify, session, current_app
from flask_mail import Message
from database import get_db
import random
import string
from datetime import datetime, timedelta

forgot_password_bp = Blueprint('forgot_password', __name__)

def generate_otp(length=6):
    """Generate a random numeric OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email, otp):
    """Send OTP to the user's email with a nicely formatted message"""
    try:
        mail = current_app.extensions.get('mail')
        if not mail:
            current_app.logger.error("Mail extension not found")
            return False
            
        msg = Message(
            subject="LSEF TESDA - Password Reset OTP",
            sender=("LSEF TESDA", current_app.config['MAIL_USERNAME']),
            recipients=[email],
            html=f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #0056b3; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">LSEF TESDA</h1>
                </div>
                
                <div style="padding: 20px;">
                    <h2 style="color: #0056b3;">Password Reset Request</h2>
                    <p>We received a request to reset your password. Please use the following OTP to verify your identity:</p>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #0056b3; margin: 15px 0; text-align: center;">
                        <h3 style="margin: 0; color: #0056b3;">Your OTP Code:</h3>
                        <p style="font-size: 24px; font-weight: bold; margin: 10px 0;">{otp}</p>
                        <p style="font-size: 12px; color: #666;">This OTP will expire in 10 minutes</p>
                    </div>
                    
                    <p>If you didn't request this password reset, please ignore this email or contact support if you have concerns.</p>
                    
                    <p>Best regards,</p>
                    <p><strong>LSEF TESDA Support Team</strong></p>
                </div>
                
                <div style="background-color: #f0f0f0; padding: 10px; text-align: center; font-size: 12px;">
                    <p>This is an automated message. Please do not reply directly to this email.</p>
                </div>
            </div>
            """
        )
        mail.send(msg)
        current_app.logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending OTP email to {email}: {str(e)}")
        return False

@forgot_password_bp.route('/request_otp', methods=['POST'])
def request_otp():
    """Handle OTP request and send email if email exists in database and account is active"""
    email = request.json.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
       
        cursor.execute("""
            SELECT user_id, email, account_status 
            FROM login 
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False, 
                'message': 'Email not found in our system'
            }), 404
            
        if user['account_status'] != 'active':
            if user['account_status'] == 'pending':
                return jsonify({
                    'success': False,
                    'message': 'Your account is still pending approval. Please wait for admin approval.'
                }), 403
            elif user['account_status'] == 'inactive':
                return jsonify({
                    'success': False,
                    'message': 'Your account is inactive. Please contact support.'
                }), 403
            else:
                return jsonify({
                    'success': False,
                    'message': 'Your account is not eligible for password reset.'
                }), 403

        otp = generate_otp()
        session['password_reset_otp'] = otp
        session['password_reset_email'] = email
        session['otp_expiration'] = (datetime.now() + timedelta(minutes=10)).timestamp()
        
        if not send_otp_email(email, otp):
            return jsonify({
                'success': False,
                'message': 'Failed to send OTP email. Please try again later.'
            }), 500

        return jsonify({
            'success': True,
            'message': 'OTP sent successfully. Please check your email.',
            'email': email 
        })

    except Exception as e:
        current_app.logger.error(f"Error in request_otp: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while processing your request'
        }), 500
        
    finally:
        cursor.close()

@forgot_password_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    """Verify the OTP entered by the user"""
    email = request.json.get('email')
    user_otp = request.json.get('otp')
    
    if not email or not user_otp:
        return jsonify({
            'success': False,
            'message': 'Email and OTP are required'
        }), 400

    if ('password_reset_otp' not in session or 
        'password_reset_email' not in session or
        'otp_expiration' not in session):
        return jsonify({
            'success': False,
            'message': 'OTP not requested or session expired'
        }), 400

    if session['password_reset_email'] != email:
        return jsonify({
            'success': False,
            'message': 'Email does not match OTP request'
        }), 400

    if datetime.now().timestamp() > session['otp_expiration']:
        return jsonify({
            'success': False,
            'message': 'OTP has expired. Please request a new one.'
        }), 400

    if session['password_reset_otp'] != user_otp:
        return jsonify({
            'success': False,
            'message': 'Invalid OTP. Please try again.'
        }), 400

    session['otp_verified'] = True
    return jsonify({
        'success': True,
        'message': 'OTP verified successfully'
    })

@forgot_password_bp.route('/reset_password', methods=['POST'])
def reset_password():
    """Handle password reset after OTP verification"""
    email = request.json.get('email')
    new_password = request.json.get('new_password')
    confirm_password = request.json.get('confirm_password')
    
    if not email or not new_password or not confirm_password:
        return jsonify({
            'success': False,
            'message': 'All fields are required'
        }), 400

    if new_password != confirm_password:
        return jsonify({
            'success': False,
            'message': 'Passwords do not match'
        }), 400

    if len(new_password) < 8:
        return jsonify({
            'success': False,
            'message': 'Password must be at least 8 characters long'
        }), 400

    if not session.get('otp_verified') or session.get('password_reset_email') != email:
        return jsonify({
            'success': False,
            'message': 'OTP verification required before password reset'
        }), 403

    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
      
        cursor.execute("""
            SELECT password, account_status 
            FROM login 
            WHERE email = %s
        """, (email,))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404
            
        if user['account_status'] != 'active':
            return jsonify({
                'success': False,
                'message': 'Account is no longer active. Password reset not allowed.'
            }), 403

        if user['password'] == new_password:
            return jsonify({
                'success': False,
                'message': 'New password cannot be the same as your current password'
            }), 400

        cursor.execute(
            "UPDATE login SET password = %s WHERE email = %s",
            (new_password, email)
        )
        db.commit()
        
        session.pop('password_reset_otp', None)
        session.pop('password_reset_email', None)
        session.pop('otp_expiration', None)
        session.pop('otp_verified', None)
        
        return jsonify({
            'success': True,
            'message': 'Password updated successfully'
        })

    except Exception as e:
        db.rollback()
        current_app.logger.error(f"Error in reset_password: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'An error occurred while resetting your password'
        }), 500
        
    finally:
        cursor.close()