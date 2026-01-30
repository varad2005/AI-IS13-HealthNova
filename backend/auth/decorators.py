from functools import wraps
from flask import session, jsonify

def login_required(f):
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            
            user_role = session.get('role')
            if user_role != required_role:
                return jsonify({
                    'status': 'error',
                    'message': f'Access denied. {required_role.capitalize()} role required'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def roles_required(*required_roles):
    """Decorator to check if user has one of the required roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            
            user_role = session.get('role')
            if user_role not in required_roles:
                return jsonify({
                    'status': 'error',
                    'message': f'Access denied. Required roles: {", ".join(required_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
