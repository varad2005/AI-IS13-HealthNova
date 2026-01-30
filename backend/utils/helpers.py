from flask import session
from models import User


def get_current_user():
    """Get current logged-in user from session"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)


def format_response(status, message, data=None, status_code=200):
    """Helper to format consistent JSON responses"""
    response = {
        'status': status,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return response, status_code


def validate_required_fields(data, required_fields):
    """Validate that all required fields are present in request data"""
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    return missing_fields


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions
