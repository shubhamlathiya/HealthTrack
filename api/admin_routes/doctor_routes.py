import random
from datetime import datetime

from flask import request, jsonify
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
import uuid

from api.admin_routes import admin
from config import mongo


@admin.route('/add-doctor', methods=['POST'])
def add_doctor():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    department = data.get('department')
    specialization = data.get('specialization')
    contact_number = data.get('contact_number')

    if not all([name, email, department, specialization, contact_number]):
        return jsonify({"error": "All fields are required"}), 400

    # Check if the doctor already exists
    existing_doctor = mongo.db.doctors.find_one({'email': email})
    if existing_doctor:
        return jsonify({'error': 'Doctor with this email already exists'}), 400

    hashed_password = generate_password_hash(password)

    # Generate unique doctor ID
    current_date = datetime.utcnow()
    year = current_date.year
    month = f"{current_date.month:02d}"
    day = f"{current_date.day:02d}"

    # Generate random 2-digit number
    random_digits = random.randint(10, 99)
    unique_doctor_id = f"{year}{month}{day}{random_digits}"
    # Create the doctor document
    doctor = {
        'doctor_id': unique_doctor_id,
        'name': name,
        'email': email,
        'password': hashed_password,
        'department': department,
        'specialization': specialization,
        'contact_number': contact_number,
        'appointments': []  # Initially no appointments
    }

    # Insert into the database
    doctor_id = mongo.db.doctors.insert_one(doctor).inserted_id

    return jsonify({'message': 'Doctor added successfully', 'doctor_id': str(doctor_id)}), 201
