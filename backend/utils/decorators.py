"""
Centralized Authentication & Authorization Decorators
======================================================

SECURITY PHILOSOPHY: Zero Trust RBAC
-------------------------------------
Why: Role-checking logic scattered in routes creates maintenance nightmares 
     and security gaps. One decorator = One Source of Truth.

Pattern: Defense in Depth
- Layer 1: Authentication check (is user logged in?)
- Layer 2: Authorization check (does user have required role?)
- Layer 3: Session validation (is session data intact?)

This ensures NO business logic pollutes route handlers.
"""

from functools import wraps
from flask import session, jsonify, request
from typing import List, Callable, Any
import logging

logger = logging.getLogger(__name__)


def login_required(f: Callable) -> Callable:
    """
    Validates that a user is authenticated via session.
    
    Security Rationale:
    - Fail-fast: Reject unauthenticated requests at entry point
    - No business logic proceeds without valid authentication
    - Returns 401 per RFC 7235 (WWW-Authenticate header implicit)
    
    Usage:
        @login_required
        def protected_route():
            # user_id guaranteed to be in session here
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Check if user_id exists in session (our auth token equivalent)
        if 'user_id' not in session:
            logger.warning(
                f"Unauthorized access attempt to {request.endpoint} "
                f"from IP {request.remote_addr}"
            )
            return jsonify({
                'status': 'error',
                'message': 'Authentication required. Please log in.',
                'code': 'AUTH_REQUIRED'
            }), 401
        
        # Validate session integrity (basic sanity check)
        if 'role' not in session:
            logger.error(
                f"Corrupted session detected for user_id={session.get('user_id')} "
                f"- missing role field"
            )
            # Clear corrupted session
            session.clear()
            return jsonify({
                'status': 'error',
                'message': 'Session corrupted. Please log in again.',
                'code': 'SESSION_INVALID'
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_role(*allowed_roles: str) -> Callable:
    """
    Zero-Trust RBAC decorator. Validates user role from session.
    
    Security Rationale:
    - Principle of Least Privilege: Only specified roles can access
    - Immutable: Role comes from session (set at login, can't be tampered)
    - Auditable: Logs every authorization failure with context
    
    Why separate from login_required?
    - Single Responsibility: Auth check ≠ Authorization check
    - Composability: Can be stacked for complex policies
    
    Args:
        allowed_roles: Variable number of role strings (e.g., 'patient', 'doctor')
    
    Returns:
        Decorator function
        
    Usage:
        @require_role('doctor', 'lab')
        def doctor_only_route():
            # Only doctors and lab staff can access
            
    Error Codes:
        401: Not authenticated (shouldn't happen if login_required used first)
        403: Authenticated but wrong role (proper authorization failure)
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Defense Layer 1: Ensure authenticated
            # WHY: Can be used standalone without @login_required
            if 'user_id' not in session:
                logger.warning(
                    f"Unauthenticated access attempt to {request.endpoint} "
                    f"requiring roles {allowed_roles}"
                )
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # Defense Layer 2: Validate role
            user_role = session.get('role')
            user_id = session.get('user_id')
            
            # Normalize roles for comparison (lowercase)
            normalized_allowed = [r.lower() for r in allowed_roles]
            
            if user_role.lower() not in normalized_allowed:
                # Log authorization failure for security audit
                logger.warning(
                    f"Authorization failure: user_id={user_id} (role={user_role}) "
                    f"attempted to access {request.endpoint} "
                    f"(requires roles: {allowed_roles}) "
                    f"from IP {request.remote_addr}"
                )
                
                return jsonify({
                    'status': 'error',
                    'message': f'Access denied. Required role(s): {", ".join(allowed_roles)}',
                    'code': 'FORBIDDEN',
                    'user_role': user_role,
                    'required_roles': list(allowed_roles)
                }), 403
            
            # Authorization successful - proceed to business logic
            logger.debug(
                f"Authorization granted: user_id={user_id} (role={user_role}) "
                f"accessing {request.endpoint}"
            )
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Convenience aliases for common role checks
def patient_required(f: Callable) -> Callable:
    """Shorthand for @require_role('patient')"""
    return require_role('patient')(f)


def doctor_required(f: Callable) -> Callable:
    """Shorthand for @require_role('doctor')"""
    return require_role('doctor')(f)


def lab_required(f: Callable) -> Callable:
    """Shorthand for @require_role('lab')"""
    return require_role('lab')(f)


def medical_staff_required(f: Callable) -> Callable:
    """Shorthand for @require_role('doctor', 'lab')"""
    return require_role('doctor', 'lab')(f)
