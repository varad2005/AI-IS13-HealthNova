from flask import Blueprint, request, jsonify, session
from models import db, User, PatientProfile
from auth.decorators import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['phone_number', 'password', 'role', 'full_name']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    phone_number = data['phone_number']
    password = data['password']
    role = data['role'].lower()
    full_name = data['full_name']
    email = data.get('email')
    
    # Validate role
    if role not in ['patient', 'doctor', 'lab']:
        return jsonify({
            'status': 'error',
            'message': 'Invalid role. Must be patient, doctor, or lab'
        }), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(phone_number=phone_number).first()
    if existing_user:
        return jsonify({
            'status': 'error',
            'message': 'Phone number already registered'
        }), 409
    
    # Check if email already exists (if provided)
    if email:
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 409
    
    try:
        # Create new user
        user = User(
            phone_number=phone_number,
            role=role,
            full_name=full_name,
            email=email
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.flush()  # Get user ID before commit
        
        # Create patient profile if role is patient
        if role == 'patient':
            patient_profile = PatientProfile(user_id=user.id)
            db.session.add(patient_profile)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'data': {
                'user_id': user.id,
                'role': user.role
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Registration failed: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user with phone number and password"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get('phone_number') or not data.get('password'):
        return jsonify({
            'status': 'error',
            'message': 'Phone number and password are required'
        }), 400
    
    phone_number = data['phone_number']
    password = data['password']
    
    # Find user
    user = User.query.filter_by(phone_number=phone_number).first()
    
    # Verify user exists and password is correct
    if not user or not user.check_password(password):
        return jsonify({
            'status': 'error',
            'message': 'Invalid phone number or password'
        }), 401
    
    # Check if user is active
    if not user.is_active:
        return jsonify({
            'status': 'error',
            'message': 'Account is inactive. Please contact support'
        }), 403
    
    # ========================================================================
    # SESSION-BASED AUTHENTICATION
    # ========================================================================
    # Set session data for authentication
    # - session['user_id']: User ID for identifying the logged-in user
    # - session['role']: User role ('doctor', 'patient', 'lab') for RBAC
    # - session['full_name']: Display name for UI
    #
    # Session cookies are automatically sent by browser on subsequent requests
    # to the same origin (domain + port), enabling server-side validation
    # via @login_required and @role_required decorators.
    #
    # SECURITY: Sessions are server-side, stored in Flask session (secure cookie)
    # ========================================================================
    session.permanent = True
    session['user_id'] = user.id
    session['role'] = user.role
    session['full_name'] = user.full_name
    
    # Determine redirect URL based on role
    # Use Flask routes for pages that need session context
    redirect_urls = {
        'patient': '/patient/dashboard.html',
        'doctor': '/doctor/dashboard-page',  # Use Flask route instead of direct HTML
        'lab': '/lab/dashboard.html'
    }
    
    return jsonify({
        'status': 'success',
        'message': 'Login successful',
        'data': {
            'user': user.to_dict(),
            'redirect_url': redirect_urls.get(user.role, '/')
        }
    }), 200
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user by clearing session"""
    user_id = session.get('user_id')
    session.clear()
    
    return jsonify({
        'status': 'success',
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current logged-in user information"""
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.clear()
        return jsonify({
            'status': 'error',
            'message': 'User not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': user.to_dict()
    }), 200


@auth_bp.route('/check-session', methods=['GET'])
def check_session():
    """Check if user has active session"""
    if 'user_id' in session:
        return jsonify({
            'status': 'success',
            'authenticated': True,
            'data': {
                'user_id': session.get('user_id'),
                'role': session.get('role'),
                'full_name': session.get('full_name')
            }
        }), 200
    else:
        return jsonify({
            'status': 'success',
            'authenticated': False
        }), 200
