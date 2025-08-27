import mysql.connector
from flask import g, current_app
import os

def get_db():
    if 'db' not in g:
        try:
            g.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="lsef_tesda"
            )
        except mysql.connector.Error as err:
            current_app.logger.error(f"Database connection failed: {err}")
            raise
    return g.db

def close_connection(exception):
    db = g.pop('db', None)
    if db is not None and db.is_connected():
        db.close()

def save_certificate(enrollment_id, name, course, date, cert_hash, tx_hash, file_path):
    conn = get_db() 
    cursor = conn.cursor()
    query = """
        INSERT INTO certificates (enrollment_id, name, course, date, cert_hash, tx_hash, file_path)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (enrollment_id, name, course, date, cert_hash, tx_hash, file_path))
    conn.commit()
    cursor.close()
    conn.close()

def search_certificates_by_name(name):
    conn = get_db() 
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM certificates WHERE name LIKE %s ORDER BY created_at DESC"
    cursor.execute(query, (f"%{name}%",))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
