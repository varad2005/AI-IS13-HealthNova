from functools import wraps
from flask import session, jsonify
from typing import List, Callable, Any

def login_required(f: Callable) -> Callable:
    """Decorator to check if user is logged in"""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if 'user_id' not in session:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated_function


def role_required(required_role: str) -> Callable:
    """
    Decorator to enforce role-based access control (RBAC)
    
    HOW IT WORKS:
    1. Checks if 'user_id' exists in session (authentication)
    2. Checks if session['role'] matches required_role (authorization)
    3. Returns 401 if not authenticated (no session)
    4. Returns 403 if wrong role (session exists but insufficient permissions)
    5. Allows request to proceed if both checks pass
    
    USAGE:
        @doctor_bp.route('/chatbot')
        @role_required('doctor')
        def doctor_chatbot():
            # This code only runs if user is logged in AS A DOCTOR
            return render_template('doctor-chatbot.html')
    
    SECURITY BENEFITS:
    - Fail-fast: Returns immediately if validation fails
    - Session-based: No tokens to manage or expire
    - Server-side: Cannot be bypassed by client-side manipulation
    - Clear error codes: 401 vs 403 helps debugging
    
    WHY THIS BLOCKS DIRECT HTML ACCESS:
    - Direct file access (file:// or opening HTML directly) has NO session
    - Browser doesn't send session cookies to direct file access
    - Only requests through Flask server include session cookies
    - Therefore, decorator automatically blocks unauthorized access
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Check authentication first
            if 'user_id' not in session:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            
            # Check authorization (role)
            user_role = session.get('role')
            if user_role != required_role:
                return jsonify({
                    'status': 'error',
                    'message': f'Access denied. {required_role.capitalize()} role required'
                }), 403
            
            # Both checks passed - proceed with request
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(*allowed_roles: str) -> Callable:
    """
    TASK 1: Zero Trust RBAC Decorator
    
    Security Rationale:
    - Implements fail-fast authentication and authorization
    - Prevents route-level role checking (separation of concerns)
    - Uses session-based auth (can be extended to JWT)
    - Returns 401 for authentication failures (not logged in)
    - Returns 403 for authorization failures (wrong role)
    
    Usage:
        @require_role('doctor', 'admin')
        def doctor_only_route():
            pass
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # First check: Authentication (401 if not logged in)
            if 'user_id' not in session:
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized: Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Second check: Authorization (403 if wrong role)
            user_role = session.get('role')
            if not user_role:
                # Session corrupted - force re-login
                return jsonify({
                    'status': 'error',
                    'message': 'Unauthorized: Session invalid',
                    'code': 'SESSION_INVALID'
                }), 401
            
            if user_role not in allowed_roles:
                return jsonify({
                    'status': 'error',
                    'message': f'Forbidden: Requires role(s): {", ".join(allowed_roles)}',
                    'code': 'INSUFFICIENT_PERMISSIONS'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def roles_required(*required_roles: str) -> Callable:
    """Decorator to check if user has one of the required roles"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
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
