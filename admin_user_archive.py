from flask import Blueprint, render_template, request, jsonify, current_app
from database import get_db
from datetime import datetime

admin_user_archive_bp = Blueprint('admin_user_archive', __name__)

@admin_user_archive_bp.route('/admin_user_archive')
def show_archive_page():
    """Render the archived user page"""
    return render_template('admin/admin_user_archive.html')


@admin_user_archive_bp.route('/get_archived_users')
def get_archived_users():
    """Fetch archived users for display"""
    db = None
    cursor = None
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT 
                archive_id, original_user_id, username,
                CONCAT(first_name, ' ', COALESCE(middle_name, ''), ' ', last_name) AS full_name,
                email, contact_number, 
                date_registered,
                date_archived,
                role, account_status
            FROM user_archived
            ORDER BY date_archived DESC
        """

        cursor.execute(query)
        users = cursor.fetchall()

        # Format dates to match the deletion code format
        for user in users:
            if user['date_registered']:
                if isinstance(user['date_registered'], datetime):
                    user['date_registered'] = user['date_registered'].strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(user['date_registered'], str):
                    try:
                        dt = datetime.strptime(user['date_registered'], '%Y-%m-%d %H:%M:%S')
                        user['date_registered'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        user['date_registered'] = user['date_registered']  # leave as-is if can't parse
            
            if user['date_archived']:
                if isinstance(user['date_archived'], datetime):
                    user['date_archived'] = user['date_archived'].strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(user['date_archived'], str):
                    try:
                        dt = datetime.strptime(user['date_archived'], '%Y-%m-%d %H:%M:%S')
                        user['date_archived'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        user['date_archived'] = user['date_archived']  # leave as-is if can't parse

        return jsonify({'success': True, 'users': users})

    except Exception as e:
        current_app.logger.error(f"Error fetching archived users: {str(e)}")
        return jsonify({'success': False, 'message': 'Error fetching archived users'}), 500

    finally:
        if cursor: cursor.close()
        if db: db.close()

@admin_user_archive_bp.route('/restore_user', methods=['POST'])
def restore_user():
    """Restore an archived user back to the login and personal_information tables"""
    db = None
    cursor = None

    try:
        data = request.get_json()
        archive_id = data.get('archive_id')

        if not archive_id:
            return jsonify({'success': False, 'message': 'Missing archive_id'}), 400

        db = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM user_archived WHERE archive_id = %s", (archive_id,))
        archived_user = cursor.fetchone()

        if not archived_user:
            return jsonify({'success': False, 'message': 'Archived user not found'}), 404

        # Handle date_registered formatting
        date_registered = archived_user['date_registered']
        if isinstance(date_registered, str):
            try:
                date_registered = datetime.strptime(date_registered, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                date_registered = datetime.now()  # fallback to current time if parsing fails

        cursor.execute("START TRANSACTION")

        cursor.execute("""
            INSERT INTO login (user_id, username, password, email, role, account_status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            archived_user['original_user_id'], archived_user['username'],
            archived_user['password'], archived_user['email'],
            archived_user['role'], archived_user['account_status']
        ))

        cursor.execute("""
            INSERT INTO personal_information (
                user_id, province, municipality, baranggay, contact_number,
                first_name, middle_name, last_name, date_of_birth, gender,
                profile_picture, terms_accepted, date_registered
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            archived_user['original_user_id'], archived_user['province'],
            archived_user['municipality'], archived_user['baranggay'], archived_user['contact_number'],
            archived_user['first_name'], archived_user['middle_name'], archived_user['last_name'],
            archived_user['date_of_birth'], archived_user['gender'],
            archived_user['profile_picture'], archived_user['terms_accepted'],
            date_registered
        ))
        
        cursor.execute("DELETE FROM user_archived WHERE archive_id = %s", (archive_id,))

        db.commit()

        return jsonify({
            'success': True, 
            'message': 'User restored successfully',
            'restored_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        if db:
            db.rollback()
        current_app.logger.error(f"Error restoring user: {str(e)}")
        return jsonify({'success': False, 'message': 'Restore failed', 'error': str(e)}), 500

    finally:
        if cursor: cursor.close()
        if db: db.close()

@admin_user_archive_bp.route('/permanent_delete_user', methods=['POST'])
def permanent_delete_user():
    """Permanently delete an archived user"""
    db = None
    cursor = None
    try:
        data = request.get_json()
        archive_id = data.get('archive_id')

        if not archive_id:
            return jsonify({'success': False, 'message': 'Missing archive_id'}), 400

        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM user_archived WHERE archive_id = %s", (archive_id,))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'No user deleted — archive_id not found'}), 404

        db.commit()
        return jsonify({
            'success': True, 
            'message': 'Archived user permanently deleted',
            'deleted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    except Exception as e:
        if db:
            db.rollback()
        current_app.logger.error(f"Error permanently deleting user: {str(e)}")
        return jsonify({'success': False, 'message': 'Permanent delete failed', 'error': str(e)}), 500

    finally:
        if cursor: cursor.close()
        if db: db.close()