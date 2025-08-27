from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from database import get_db

staff_class_certificates_bp = Blueprint('staff_class_certificates', __name__)