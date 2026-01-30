from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from models import db, User, PatientProfile, Visit, LabTest, Prescription
from auth.decorators import role_required
from datetime import datetime
from utils.medical_history import get_patient_timeline, get_patient_summary
from utils.ai_helper import get_ai_guidance, get_symptom_summary

patient_bp = Blueprint('patient', __name__, template_folder='../../frontend/patient')


@patient_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """Render patient dashboard HTML page"""
    # Check authentication manually for UI route
    if 'user_id' not in session or session.get('role') != 'patient':
        return redirect('/login.html')
    
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        return redirect('/login.html')
    
    # Render the dashboard HTML (data will be loaded via JS)
    return render_template('dashboard.html', user=user)


@patient_bp.route('/dashboard/data', methods=['GET'])
@role_required('patient')
def dashboard_data():
    """API endpoint: Get patient dashboard data as JSON"""
    user_id = session.get('user_id')
    
    # Get patient profile
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get recent visits
    recent_visits = Visit.query.filter_by(
        patient_profile_id=patient_profile.id
    ).order_by(Visit.created_at.desc()).limit(5).all()
    
    # Get pending lab tests
    pending_lab_tests = LabTest.query.join(Visit).filter(
        Visit.patient_profile_id == patient_profile.id,
        LabTest.status.in_(['requested', 'approved', 'scheduled'])
    ).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'profile': patient_profile.to_dict(),
            'recent_visits': [visit.to_dict() for visit in recent_visits],
            'pending_lab_tests': [test.to_dict() for test in pending_lab_tests],
            'total_visits': len(patient_profile.visits)
        }
    }), 200


@patient_bp.route('/profile', methods=['GET'])
@role_required('patient')
def get_profile():
    """Get patient profile"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': patient_profile.to_dict()
    }), 200


@patient_bp.route('/profile', methods=['PUT'])
@role_required('patient')
def update_profile():
    """Update patient profile"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    data = request.get_json()
    
    # Update allowed fields
    allowed_fields = ['age', 'gender', 'blood_group', 'address', 'emergency_contact',
                     'allergies', 'chronic_conditions', 'previous_surgeries']
    
    for field in allowed_fields:
        if field in data:
            setattr(patient_profile, field, data[field])
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Profile updated successfully',
            'data': patient_profile.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to update profile: {str(e)}'
        }), 500


@patient_bp.route('/visits', methods=['GET'])
@role_required('patient')
def get_visits():
    """Get all patient visits"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    visits = Visit.query.filter_by(
        patient_profile_id=patient_profile.id
    ).order_by(Visit.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'visits': [visit.to_dict(include_details=True) for visit in visits],
            'total': len(visits)
        }
    }), 200


@patient_bp.route('/visits', methods=['POST'])
@role_required('patient')
def create_visit():
    """Create a new visit with symptoms - creates append-only history entry"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found. Please complete your profile first.'
        }), 404
    
    data = request.get_json()
    
    # Validate symptoms
    if not data.get('symptoms') or not data['symptoms'].strip():
        return jsonify({
            'status': 'error',
            'message': 'Symptoms are required and cannot be empty'
        }), 400
    
    try:
        # Generate AI summary of symptoms (helps doctors quickly understand cases)
        # If this fails, visit is still created without summary
        ai_summary = None
        try:
            ai_summary = get_symptom_summary(data['symptoms'].strip())
        except:
            pass  # Don't fail visit creation if AI summary fails
        
        # Create new visit (append-only - never update existing visits)
        visit = Visit(
            patient_profile_id=patient_profile.id,
            symptoms=data['symptoms'].strip(),
            ai_summary=ai_summary,  # AI-generated summary for doctor
            severity=data.get('severity', 'medium'),  # Default to medium
            status='open',
            visit_date=datetime.utcnow()
        )
        
        db.session.add(visit)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Visit created successfully. A doctor will review your symptoms.',
            'data': visit.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to create visit: {str(e)}'
        }), 500


@patient_bp.route('/visits/<int:visit_id>', methods=['GET'])
@role_required('patient')
def get_visit(visit_id):
    """Get specific visit details with full information"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get visit and verify ownership
    visit = Visit.query.filter_by(
        id=visit_id,
        patient_profile_id=patient_profile.id
    ).first()
    
    if not visit:
        return jsonify({
            'status': 'error',
            'message': 'Visit not found or access denied'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': visit.to_dict(include_details=True)
    }), 200


@patient_bp.route('/history', methods=['GET'])
@role_required('patient')
def get_patient_history():
    """Get complete patient medical history - timeline view (latest first)
    This is the core endpoint for Digital Patient History feature.
    Returns structured, visit-based history that replaces physical files.
    """
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get all visits ordered by date (latest first)
    visits = Visit.query.filter_by(
        patient_profile_id=patient_profile.id
    ).order_by(Visit.visit_date.desc()).all()
    
    # Build comprehensive history
    history = []
    for visit in visits:
        visit_data = visit.to_dict()
        visit_data['doctor_name'] = visit.doctor.full_name if visit.doctor else 'Not assigned'
        visit_data['lab_tests_count'] = len(visit.lab_tests)
        visit_data['prescriptions_count'] = len(visit.prescriptions)
        visit_data['has_diagnosis'] = visit.diagnosis is not None and visit.diagnosis.strip() != ''
        
        # Include full details for each visit
        visit_data['lab_tests'] = [test.to_dict() for test in visit.lab_tests]
        visit_data['prescriptions'] = [rx.to_dict() for rx in visit.prescriptions]
        
        history.append(visit_data)
    
    # Summary statistics
    total_visits = len(visits)
    completed_visits = len([v for v in visits if v.status == 'completed'])
    open_visits = len([v for v in visits if v.status == 'open'])
    in_progress_visits = len([v for v in visits if v.status == 'in_progress'])
    
    return jsonify({
        'status': 'success',
        'data': {
            'patient_info': {
                'name': patient_profile.user.full_name,
                'age': patient_profile.age,
                'gender': patient_profile.gender,
                'blood_group': patient_profile.blood_group,
                'allergies': patient_profile.allergies,
                'chronic_conditions': patient_profile.chronic_conditions
            },
            'summary': {
                'total_visits': total_visits,
                'completed_visits': completed_visits,
                'open_visits': open_visits,
                'in_progress_visits': in_progress_visits
            },
            'history': history  # Complete timeline, latest first
        }
    }), 200


@patient_bp.route('/lab-tests', methods=['GET'])
@role_required('patient')
def get_lab_tests():
    """Get all lab tests for patient"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get all lab tests through visits
    lab_tests = LabTest.query.join(Visit).filter(
        Visit.patient_profile_id == patient_profile.id
    ).order_by(LabTest.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'lab_tests': [test.to_dict(include_reports=True) for test in lab_tests],
            'total': len(lab_tests)
        }
    }), 200


@patient_bp.route('/prescriptions', methods=['GET'])
@role_required('patient')
def get_prescriptions():
    """Get all prescriptions for patient"""
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get all prescriptions through visits
    prescriptions = Prescription.query.join(Visit).filter(
        Visit.patient_profile_id == patient_profile.id
    ).order_by(Prescription.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'prescriptions': [rx.to_dict() for rx in prescriptions],
            'total': len(prescriptions)
        }
    }), 200


# ===== MEDICAL HISTORY TIMELINE ENDPOINTS =====

@patient_bp.route('/history/timeline', methods=['GET'])
@role_required('patient')
def get_medical_timeline():
    """
    Get complete medical history timeline for logged-in patient
    Digital medical record - replaces physical files
    
    Query params:
        limit: Number of visits to return (default: all)
    
    Returns:
        Complete chronological medical history ordered by date (newest first)
    """
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get limit from query params
    limit = request.args.get('limit', type=int)
    
    # Get patient summary and complete timeline
    patient_summary = get_patient_summary(patient_profile)
    timeline = get_patient_timeline(patient_profile.id, limit=limit)
    
    return jsonify({
        'status': 'success',
        'data': {
            'patient': patient_summary,
            'timeline': timeline,
            'total_visits': len(timeline) if not limit else patient_summary['total_visits']
        }
    }), 200


@patient_bp.route('/history/summary', methods=['GET'])
@role_required('patient')
def get_medical_summary():
    """
    Get patient medical summary without full timeline
    Lighter endpoint for dashboard overview
    """
    user_id = session.get('user_id')
    patient_profile = PatientProfile.query.filter_by(user_id=user_id).first()
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    patient_summary = get_patient_summary(patient_profile)
    
    # Get only recent 5 visits for quick overview
    recent_timeline = get_patient_timeline(patient_profile.id, limit=5)
    
    return jsonify({
        'status': 'success',
        'data': {
            'summary': patient_summary,
            'recent_visits': recent_timeline
        }
    }), 200


@patient_bp.route('/ai-guidance', methods=['POST'])
@role_required('patient')
def ai_health_guidance():
    """
    Get general health awareness from Google Gemini.
    Does NOT diagnose or prescribe - only provides awareness.
    """
    data = request.get_json()
    
    # Validate input
    if not data or not data.get('symptoms'):
        return jsonify({
            'status': 'error',
            'message': 'Please provide your health concern or symptoms'
        }), 400
    
    user_symptoms = data['symptoms'].strip()
    
    # Validate input length (10-1000 characters)
    # Minimum 10: ensures enough context for meaningful guidance
    # Maximum 1000: prevents API cost abuse and keeps responses focused
    if len(user_symptoms) < 10:
        return jsonify({
            'status': 'error',
            'message': 'Please provide more details about your health concern (at least 10 characters)'
        }), 400
    
    if len(user_symptoms) > 1000:
        return jsonify({
            'status': 'error',
            'message': 'Please keep your health concern under 1000 characters'
        }), 400
    
    try:
        # Get AI guidance from Gemini
        ai_response = get_ai_guidance(user_symptoms)
        
        # Important disclaimer
        disclaimer = (
            "⚠️ IMPORTANT: This is general health awareness information only. "
            "It is NOT a medical diagnosis or prescription. "
            "Please consult a certified doctor for proper medical advice and treatment."
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'guidance': ai_response,
                'disclaimer': disclaimer
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Unable to provide guidance at this moment. Please consult a doctor directly.'
        }), 500


@patient_bp.route('/ai-chat', methods=['POST'])
@role_required('patient')
def ai_chat():
    """API endpoint: Get AI response for patient queries using Gemini"""
    try:
        from utils.gemini_helper import get_ai_response
        
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': 'Message is required'
            }), 400
        
        # Get AI response from Gemini
        response = get_ai_response(user_message)
        
        return jsonify({
            'status': 'success' if response['success'] else 'fallback',
            'message': response['message']
        }), 200
    
    except Exception as e:
        print(f"AI Chat Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to process your request. Please try again later.'
        }), 500


# ===== APPOINTMENT BOOKING ENDPOINTS =====

@patient_bp.route('/doctors', methods=['GET'])
@role_required('patient')
def get_doctors():
    """Get all available doctors for booking appointments"""
    try:
        # Get all doctors from database
        doctors = User.query.filter_by(role='doctor', is_active=True).all()
        
        doctors_list = [{
            'id': doctor.id,
            'name': doctor.full_name,
            'phone': doctor.phone_number,
            'email': doctor.email
        } for doctor in doctors]
        
        return jsonify({
            'status': 'success',
            'data': doctors_list
        }), 200
    
    except Exception as e:
        print(f"Error fetching doctors: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to fetch doctors list'
        }), 500


@patient_bp.route('/appointments', methods=['GET'])
@role_required('patient')
def get_appointments():
    """Get all appointments for logged-in patient"""
    from models import Appointment
    
    user_id = session.get('user_id')
    
    try:
        # Get all appointments for this patient
        appointments = Appointment.query.filter_by(
            patient_id=user_id
        ).order_by(Appointment.appointment_date.desc()).all()
        
        return jsonify({
            'status': 'success',
            'data': [apt.to_dict(include_participants=True) for apt in appointments]
        }), 200
    
    except Exception as e:
        print(f"Error fetching appointments: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to fetch appointments'
        }), 500


@patient_bp.route('/appointments', methods=['POST'])
@role_required('patient')
def create_appointment():
    """Create a new appointment with a doctor"""
    from models import Appointment
    
    user_id = session.get('user_id')
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['doctor_id', 'appointment_date', 'reason']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'status': 'error',
                'message': f'{field} is required'
            }), 400
    
    try:
        # Parse appointment date
        appointment_date = datetime.fromisoformat(data['appointment_date'])
        
        # Verify doctor exists
        doctor = User.query.filter_by(id=data['doctor_id'], role='doctor', is_active=True).first()
        if not doctor:
            return jsonify({
                'status': 'error',
                'message': 'Doctor not found'
            }), 404
        
        # Create appointment
        appointment = Appointment(
            patient_id=user_id,
            doctor_id=data['doctor_id'],
            appointment_date=appointment_date,
            duration_minutes=data.get('duration_minutes', 30),
            reason=data['reason'],
            status='scheduled',
            meeting_status='not_started'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Appointment booked successfully',
            'data': appointment.to_dict(include_participants=True)
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Error creating appointment: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Failed to create appointment: {str(e)}'
        }), 500
