from functools import wraps

import jwt
from flask import request, redirect, abort


def token_required(allowed_roles=None):
    def decorator(f):
        @wraps(f)  # This is important to preserve the name of the original view function
        def wrapper(*args, **kwargs):
            token = request.cookies.get('token')

            if not token:
                return redirect("/")  # No token, redirect to login

            try:
                data = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
                current_user = data.get('user_id')
                user_role = data.get('role')

                if not current_user or not user_role:
                    return redirect("/")  # Missing info

                if allowed_roles and user_role not in allowed_roles:
                    return abort(403), 403  # Unauthorized role

            except jwt.ExpiredSignatureError:
                return redirect("/")  # Expired token
            except jwt.InvalidTokenError:
                return redirect("/")  # Invalid token

            return f(current_user, *args, **kwargs)

        return wrapper
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

