# utils/tokens.py
from flask import current_app
from itsdangerous import URLSafeTimedSerializer


def generate_verification_token(user_id):
    """Generate a secure verification token"""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(user_id, salt='email-verify')


def verify_token(token, expiration=None):
    """Verify and decode the token"""
    if expiration is None:
        expiration = current_app.config.get('VERIFICATION_TOKEN_EXPIRATION', 86400)

    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(
            token,
            salt='email-verify',
            max_age=expiration
        )
        return user_id
    except:
        return None
