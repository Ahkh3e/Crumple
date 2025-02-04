from flask import Blueprint, request, jsonify, render_template
from flask_wtf.csrf import generate_csrf
from flask_login import login_user, logout_user, login_required
from ..models.user import User
from .. import db, limiter

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def login():
    """Login route"""
    if request.method == 'GET':
        return render_template('auth/login.html', csrf_token_value=generate_csrf())
        
    data = request.get_json()
    
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({
            'status': 'error',
            'message': 'Missing username or password'
        }), 400
    
    user = User.query.filter_by(username=data['username']).first()
    if user is None:
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401

    # Debug password verification
    print(f"Stored hash: {user.password_hash}")
    print(f"Verifying password: {data['password']}")
    is_valid = user.verify_password(data['password'])
    print(f"Password valid: {is_valid}")
    
    if not is_valid:
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401
    
    login_user(user)
    return jsonify({
        'status': 'success',
        'message': 'Login successful'
    })

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout route"""
    logout_user()
    return jsonify({
        'status': 'success',
        'message': 'Logout successful'
    })

@bp.route('/check', methods=['GET'])
def check_auth():
    """Check authentication status"""
    from flask_login import current_user
    return jsonify({
        'authenticated': current_user.is_authenticated,
        'username': current_user.username if current_user.is_authenticated else None
    })
