import datetime

import jwt
from bson import ObjectId
from flask import jsonify
from werkzeug.security import generate_password_hash

from api.auth_routes import auth
from config import mongo
from email_utils import send_email


@auth.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')

    # Check if email exists
    user = mongo.db.patients.find_one({"email": email})
    if not user:
        return jsonify({"error": "Email not found"}), 404

    # Generate a reset token
    reset_token = jwt.encode(
        {"user_id": str(user['_id']), "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
        "your_secret_key",  # Replace with your secret key
        algorithm="HS256"
    )

    # Send reset email
    reset_link = f"http://localhost:5000/auth/reset-password/{reset_token}"
    send_email("Password Reset Request", email, reset_link)

    return jsonify({"message": "Password reset link sent to your email"}), 200


@auth.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    try:
        # Decode token
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        user_id = payload['user_id']
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Reset token has expired"}), 400
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid reset token"}), 400

    # Get new password
    data = request.json
    new_password = data.get('password')
    if not new_password:
        return jsonify({"error": "Password is required"}), 400

    # Hash new password
    hashed_password = generate_password_hash(new_password)

    # Update password in the database
    mongo.db.patients.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})

    return jsonify({"message": "Password updated successfully"}), 200
