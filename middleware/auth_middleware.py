from flask import request, jsonify, redirect, url_for
from functools import wraps
import jwt

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        # Fetch the token from cookies
        token = request.cookies.get('token')

        if not token:
            # Redirect if no token is found
            return redirect("/")  # Redirect to login page

        try:
            # Decode the token and extract the user data
            data = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
            current_user = data.get('user_id')

            if not current_user:
                return redirect("/")  # Redirect if user_id is not in token

        except jwt.ExpiredSignatureError:
            return redirect("/")  # Redirect on expired token
        except jwt.InvalidTokenError:
            return redirect("/")  # Redirect on invalid token

        # Pass the current_user to the wrapped function
        return f(current_user, *args, **kwargs)

    return decorator

def chat_token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        # Fetch the token from cookies
        token = request.cookies.get('token')

        if not token:
            # Redirect if no token is found
            return redirect("/")  # Redirect to login page

        try:
            # Decode the token and extract the user data
            data = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
            current_user = data.get("user")

            if not current_user:
                return redirect("/")  # Redirect if user_id is not in token

        except jwt.ExpiredSignatureError:
            return redirect("/")  # Redirect on expired token
        except jwt.InvalidTokenError:
            return redirect("/")  # Redirect on invalid token

        # Pass the current_user to the wrapped function
        return f(current_user, *args, **kwargs)

    return decorator

