from flask import request, jsonify, redirect, url_for
from functools import wraps
import jwt


def token_required(f):
    def decorator(*args, **kwargs):
        token = request.cookies.get('token')  # Fetch the token from cookies
        if not token:
            return redirect('/')

        try:
            data = jwt.decode(token, 'your_secret_key', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return redirect('/')
        except jwt.InvalidTokenError:
            return redirect('/')
        # print(data)
        current_user = data.get('user_id')
        # print(current_user)
        return f(current_user, *args, **kwargs)

    return decorator
