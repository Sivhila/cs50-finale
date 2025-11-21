import requests

from flask import redirect, render_template, session
from functools import wraps

def firebase_login_require(f):
    """
    Decorate routes to require login.

    https://flask.palletsproject.com/en/latest/patterns/viewdecorators
    
    """
    
    @wraps(f) 
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login") 
        return f(*args, **kwargs)
    
    return decorated_function


@app.route('/login', methods=['POST']) 
def login():
    id_token = request.json.get('idToken') 

    if not id_token:
        return jsonify({'error': 'Missing ID token'}), 400

    try:
        decoded_token = auth.verify_id_token(id_token) 
        uid = decoded_token['uid'] 

        session['user'] = decoded_token['uid'] 


        return jsonify({'message': f'User {uid} authenticated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 401

