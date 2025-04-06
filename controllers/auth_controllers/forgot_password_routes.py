import datetime

import jwt
from bson import ObjectId
from flask import jsonify, request, render_template, flash, redirect
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash

from controllers.auth_controllers import auth
from controllers.constant.PathConstant import FORGOT_PASSWORD, RESET_PASSWORD
from utils.config import mongo
from utils.email_utils import send_email

s = URLSafeTimedSerializer("SECRET_KEY")


@auth.route(FORGOT_PASSWORD, methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')

        # Check if email exists
        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"error": "Email not found"}), 404

        reset_token = s.dumps(email, salt='password-reset-salt')

        # Send reset email
        reset_link = f"http://127.0.0.1:5000/auth/reset-password/{reset_token}"
        send_email("Password Reset Request", email, reset_link)

        return jsonify({"message": "Password reset link sent to your email"}), 200
    elif request.method == 'GET':
        return render_template('auth_templates/forgot_password_templates.html')


@auth.route(RESET_PASSWORD + '/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=600)  # Token expires in 30 minutes
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect('/auth/forgot-password')

    if request.method == 'POST':
        new_password = request.form.get('password')
        # Hash the password before storing
        hashed_password = generate_password_hash(new_password)  # Implement password hashing
        # Update the user's password in the database
        mongo.db.users.update_one(
            {'email': email},
            {
                '$set': {
                    'password': hashed_password,
                }
            }
        )
        flash('Your password has been updated.', 'success')
        return redirect('/')

    return render_template('auth_templates/reset_password_templates.html')
