import datetime
import jwt
from flask import jsonify, request, render_template, flash, redirect, url_for
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

from controllers.auth_controllers import auth
from controllers.constant.adminPathConstant import FORGOT_PASSWORD, RESET_PASSWORD
from models.userModel import User
from utils.config import db  # Using SQLAlchemy for MySQL database
from utils.email_utils import send_email

# Secret key for token generation
s = URLSafeTimedSerializer("SECRET_KEY")

# Forgot Password Route
@auth.route(FORGOT_PASSWORD, methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')

        # Check if email exists in the database
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "Email not found"}), 404

        # Generate the reset token
        reset_token = s.dumps(email, salt='password-reset-salt')

        # Send reset email with the link
        reset_link = f"http://127.0.0.1:5000/auth/reset-password/{reset_token}"
        send_email("Password Reset Request", email, reset_link)

        return jsonify({"message": "Password reset link sent to your email"}), 200

    elif request.method == 'GET':
        return render_template('auth_templates/forgot_password_templates.html')

# Reset Password Route
@auth.route(RESET_PASSWORD + '/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        # Validate the token and get the email
        email = s.loads(token, salt='password-reset-salt', max_age=600)  # Token expires in 10 minutes
    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect('/auth/forgot-password')

    if request.method == 'POST':
        new_password = request.form.get('password')

        # Hash the new password before storing
        hashed_password = generate_password_hash(new_password)

        # Update the user's password in the database
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = hashed_password
            db.session.commit()  # Commit changes to the database
            flash('Your password has been updated.', 'success')
            return redirect('/')

        flash('Failed to update password. Please try again.', 'danger')
        return redirect('/auth/forgot-password')

    return render_template('auth_templates/reset_password_templates.html')
