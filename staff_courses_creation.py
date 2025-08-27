from flask import Blueprint, request, jsonify
from database import get_db
from datetime import datetime

staff_courses_creation_bp = Blueprint('staff_courses_creation', __name__)

@staff_courses_creation_bp.route('/staff/create_course', methods=['POST'])
def create_course():
    data = request.get_json()

    # Required fields
    required_fields = [
        'course_code', 'course_title', 'course_description', 'course_category',
        'target_audience', 'duration_hours', 'created_by'
    ]

    # Check for missing required fields
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == '':
            return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400

    # Optional fields
    prerequisites = data.get('prerequisites', None)
    learning_outcomes = data.get('learning_outcomes', None)
    max_students = data.get('max_students', None)
    course_fee = data.get('course_fee', 0.00)
    published = data.get('published', 0)  # Default to draft (0)

    # Status and timestamps
    course_status = 'pending'  # Always pending until admin approves
    date_created = datetime.now()
    date_published = None  # Explicitly set to None (NULL in DB) for pending

    try:
        db = get_db()
        cursor = db.cursor()

        query = """
            INSERT INTO courses (
                course_code, course_title, course_description, course_category,
                target_audience, prerequisites, learning_outcomes, duration_hours,
                course_fee, max_students, course_status, published, created_by, 
                date_created, date_published
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            data['course_code'],
            data['course_title'],
            data['course_description'],
            data['course_category'],
            data['target_audience'],
            prerequisites,
            learning_outcomes,
            data['duration_hours'],
            course_fee,
            max_students,
            course_status,
            published,
            data['created_by'],
            date_created,
            date_published  # This will remain NULL until admin approval
        )

        cursor.execute(query, values)
        db.commit()

        return jsonify({'status': 'success', 'message': 'Course created successfully. Pending admin approval.'}), 201

    except Exception as e:
        db.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
