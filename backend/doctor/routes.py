from flask import Blueprint, request, jsonify, session
from models import db, User, PatientProfile, Visit, LabTest, Prescription
from auth.decorators import role_required
from datetime import datetime
from utils.medical_history import (
    get_patient_timeline, 
    get_patient_summary, 
    add_doctor_notes,
    validate_doctor_access,
    create_visit_entry
)

doctor_bp = Blueprint('doctor', __name__)


@doctor_bp.route('/dashboard', methods=['GET'])
@role_required('doctor')
def dashboard():
    """Get doctor dashboard overview"""
    doctor_id = session.get('user_id')
    
    # Get assigned patients (through visits)
    assigned_visits = Visit.query.filter_by(doctor_id=doctor_id).all()
    patient_ids = list(set([v.patient_profile_id for v in assigned_visits]))
    
    # Get pending visits
    pending_visits = Visit.query.filter_by(
        doctor_id=doctor_id,
        status='pending'
    ).order_by(Visit.created_at.desc()).all()
    
    # Get in-progress visits
    in_progress_visits = Visit.query.filter_by(
        doctor_id=doctor_id,
        status='in_progress'
    ).order_by(Visit.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'total_patients': len(patient_ids),
            'pending_visits': [visit.to_dict() for visit in pending_visits],
            'in_progress_visits': [visit.to_dict() for visit in in_progress_visits],
            'total_visits': len(assigned_visits)
        }
    }), 200


@doctor_bp.route('/patients', methods=['GET'])
@role_required('doctor')
def get_patients():
    """Get all assigned patients"""
    doctor_id = session.get('user_id')
    
    # Get unique patient profiles from assigned visits
    visits = Visit.query.filter_by(doctor_id=doctor_id).all()
    patient_profile_ids = list(set([v.patient_profile_id for v in visits]))
    
    patients = []
    for profile_id in patient_profile_ids:
        profile = PatientProfile.query.get(profile_id)
        if profile:
            patient_data = profile.to_dict()
            patient_data['user'] = profile.user.to_dict()
            patient_data['total_visits'] = Visit.query.filter_by(
                patient_profile_id=profile_id,
                doctor_id=doctor_id
            ).count()
            patients.append(patient_data)
    
    return jsonify({
        'status': 'success',
        'data': {
            'patients': patients,
            'total': len(patients)
        }
    }), 200


@doctor_bp.route('/patients/<int:patient_profile_id>', methods=['GET'])
@role_required('doctor')
def get_patient_details(patient_profile_id):
    """Get full patient profile and complete medical history - Digital Patient History
    This endpoint replaces physical patient files with structured digital records.
    Doctor can see entire medical timeline on one screen.
    """
    doctor_id = session.get('user_id')
    
    # Verify doctor has access to this patient (must have at least one assigned visit)
    has_access = Visit.query.filter_by(
        doctor_id=doctor_id,
        patient_profile_id=patient_profile_id
    ).first()
    
    if not has_access:
        return jsonify({
            'status': 'error',
            'message': 'Access denied. Patient not assigned to you'
        }), 403
    
    # Get patient profile
    patient_profile = PatientProfile.query.get(patient_profile_id)
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get ALL visits for this patient ordered by date (latest first)
    # This provides complete medical history timeline
    visits = Visit.query.filter_by(
        patient_profile_id=patient_profile_id
    ).order_by(Visit.visit_date.desc()).all()
    
    # Build comprehensive history with all details
    history = []
    for visit in visits:
        visit_data = visit.to_dict()
        visit_data['doctor_name'] = visit.doctor.full_name if visit.doctor else 'Not assigned'
        visit_data['is_my_visit'] = visit.doctor_id == doctor_id
        visit_data['lab_tests'] = [test.to_dict(include_reports=True) for test in visit.lab_tests]
        visit_data['prescriptions'] = [rx.to_dict() for rx in visit.prescriptions]
        history.append(visit_data)
    
    patient_data = patient_profile.to_dict()
    patient_data['user'] = patient_profile.user.to_dict()
    patient_data['complete_history'] = history  # Entire medical timeline
    patient_data['total_visits'] = len(visits)
    patient_data['my_visits_count'] = len([v for v in visits if v.doctor_id == doctor_id])
    
    return jsonify({
        'status': 'success',
        'data': patient_data
    }), 200


@doctor_bp.route('/visits', methods=['GET'])
@role_required('doctor')
def get_visits():
    """Get all visits assigned to doctor"""
    doctor_id = session.get('user_id')
    
    # Optional status filter
    status = request.args.get('status')
    
    query = Visit.query.filter_by(doctor_id=doctor_id)
    
    if status:
        query = query.filter_by(status=status)
    
    visits = query.order_by(Visit.created_at.desc()).all()
    
    return jsonify({
        'status': 'success',
        'data': {
            'visits': [visit.to_dict(include_details=True) for visit in visits],
            'total': len(visits)
        }
    }), 200


@doctor_bp.route('/visits/<int:visit_id>', methods=['GET'])
@role_required('doctor')
def get_visit(visit_id):
    """Get specific visit details"""
    doctor_id = session.get('user_id')
    
    # Get visit and verify doctor has access
    visit = Visit.query.filter_by(id=visit_id, doctor_id=doctor_id).first()
    
    if not visit:
        return jsonify({
            'status': 'error',
            'message': 'Visit not found or access denied'
        }), 404
    
    return jsonify({
        'status': 'success',
        'data': visit.to_dict(include_details=True)
    }), 200


@doctor_bp.route('/visits/<int:visit_id>/diagnose', methods=['PUT'])
@role_required('doctor')
def diagnose_visit(visit_id):
    """Add diagnosis, notes, and prescriptions to a visit - Append-only
    Doctor can ADD data to an existing visit, but cannot edit past visits.
    This maintains integrity of medical history.
    """
    doctor_id = session.get('user_id')
    
    # Get visit and verify doctor has access
    visit = Visit.query.filter_by(id=visit_id, doctor_id=doctor_id).first()
    
    if not visit:
        return jsonify({
            'status': 'error',
            'message': 'Visit not found or access denied'
        }), 404
    
    # Prevent editing completed visits (append-only principle)
    if visit.status == 'completed':
        return jsonify({
            'status': 'error',
            'message': 'Cannot modify completed visit. Medical history is append-only.'
        }), 403
    
    data = request.get_json()
    
    try:
        # Add diagnosis and notes (only if not already set)
        if 'diagnosis' in data and data['diagnosis']:
            if not visit.diagnosis:  # Only set if empty
                visit.diagnosis = data['diagnosis']
            else:
                # Append to existing diagnosis with timestamp
                visit.diagnosis += f"\n\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {data['diagnosis']}"
        
        if 'notes' in data and data['notes']:
            if not visit.notes:
                visit.notes = data['notes']
            else:
                # Append to existing notes
                visit.notes += f"\n\n[{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}] {data['notes']}"
        
        if 'severity' in data and data['severity'] in ['low', 'medium', 'high', 'critical']:
            visit.severity = data['severity']
        
        # Update status if provided
        if 'status' in data and data['status'] in ['open', 'in_progress', 'completed']:
            visit.status = data['status']
            
            # Set completion timestamp if marking as completed
            if data['status'] == 'completed':
                visit.completed_at = datetime.utcnow()
        
        # Add prescriptions if provided (append-only)
        if 'prescriptions' in data and isinstance(data['prescriptions'], list):
            for rx_data in data['prescriptions']:
                # Validate required prescription fields
                required_fields = ['medication_name', 'dosage', 'frequency', 'duration']
                if all(field in rx_data for field in required_fields):
                    prescription = Prescription(
                        visit_id=visit_id,
                        medication_name=rx_data['medication_name'],
                        dosage=rx_data['dosage'],
                        frequency=rx_data['frequency'],
                        duration=rx_data['duration'],
                        instructions=rx_data.get('instructions')
                    )
                    db.session.add(prescription)
        
        # Add lab test requests if provided
        if 'lab_tests' in data and isinstance(data['lab_tests'], list):
            for test_data in data['lab_tests']:
                if 'test_name' in test_data:
                    lab_test = LabTest(
                        visit_id=visit_id,
                        test_name=test_data['test_name'],
                        test_type=test_data.get('test_type'),
                        instructions=test_data.get('instructions'),
                        status='requested'
                    )
                    db.session.add(lab_test)
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Diagnosis and treatment added successfully',
            'data': visit.to_dict(include_details=True)
        }), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to update diagnosis: {str(e)}'
        }), 500


@doctor_bp.route('/visits/<int:visit_id>/prescriptions', methods=['POST'])
@role_required('doctor')
def add_prescription(visit_id):
    """Add prescription to a visit"""
    doctor_id = session.get('user_id')
    
    # Get visit and verify doctor has access
    visit = Visit.query.filter_by(id=visit_id, doctor_id=doctor_id).first()
    
    if not visit:
        return jsonify({
            'status': 'error',
            'message': 'Visit not found or access denied'
        }), 404
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['medication_name', 'dosage', 'frequency', 'duration']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({
                'status': 'error',
                'message': f'Missing required field: {field}'
            }), 400
    
    try:
        prescription = Prescription(
            visit_id=visit_id,
            medication_name=data['medication_name'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            duration=data['duration'],
            instructions=data.get('instructions')
        )
        
        db.session.add(prescription)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Prescription added successfully',
            'data': prescription.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to add prescription: {str(e)}'
        }), 500


@doctor_bp.route('/visits/<int:visit_id>/lab-tests', methods=['POST'])
@role_required('doctor')
def request_lab_test(visit_id):
    """Request a lab test for a visit"""
    doctor_id = session.get('user_id')
    
    # Get visit and verify doctor has access
    visit = Visit.query.filter_by(id=visit_id, doctor_id=doctor_id).first()
    
    if not visit:
        return jsonify({
            'status': 'error',
            'message': 'Visit not found or access denied'
        }), 404
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('test_name'):
        return jsonify({
            'status': 'error',
            'message': 'Test name is required'
        }), 400
    
    try:
        lab_test = LabTest(
            visit_id=visit_id,
            test_name=data['test_name'],
            test_type=data.get('test_type'),
            instructions=data.get('instructions'),
            status='requested'
        )
        
        db.session.add(lab_test)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Lab test requested successfully',
            'data': lab_test.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to request lab test: {str(e)}'
        }), 500


@doctor_bp.route('/visits/<int:visit_id>/complete', methods=['POST'])
@role_required('doctor')
def complete_visit(visit_id):
    """Mark visit as completed"""
    doctor_id = session.get('user_id')
    
    # Get visit and verify doctor has access
    visit = Visit.query.filter_by(id=visit_id, doctor_id=doctor_id).first()
    
    if not visit:
        return jsonify({
            'status': 'error',
            'message': 'Visit not found or access denied'
        }), 404
    
    # Mark as completed
    visit.status = 'completed'
    visit.completed_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Visit marked as completed',
            'data': visit.to_dict(include_details=True)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to complete visit: {str(e)}'
        }), 500


# ===== MEDICAL HISTORY TIMELINE ENDPOINTS =====

@doctor_bp.route('/patients/<int:patient_profile_id>/timeline', methods=['GET'])
@role_required('doctor')
def get_patient_medical_timeline(patient_profile_id):
    """
    Get complete medical history timeline for a patient
    Digital replacement for physical patient files
    
    Query params:
        limit: Number of visits to return (default: all)
    
    Returns:
        Complete chronological medical history ordered by date (newest first)
    """
    doctor_id = session.get('user_id')
    
    # Verify doctor has access to this patient
    if not validate_doctor_access(doctor_id, patient_profile_id):
        return jsonify({
            'status': 'error',
            'message': 'Access denied. You must have at least one visit with this patient.'
        }), 403
    
    # Get patient profile
    patient_profile = PatientProfile.query.get(patient_profile_id)
    
    if not patient_profile:
        return jsonify({
            'status': 'error',
            'message': 'Patient profile not found'
        }), 404
    
    # Get limit from query params
    limit = request.args.get('limit', type=int)
    
    # Get patient summary and complete timeline
    patient_summary = get_patient_summary(patient_profile)
    timeline = get_patient_timeline(patient_profile_id, limit=limit)
    
    return jsonify({
        'status': 'success',
        'data': {
            'patient': patient_summary,
            'timeline': timeline,
            'total_visits': len(timeline) if not limit else patient_summary['total_visits']
        }
    }), 200


@doctor_bp.route('/patients/<int:patient_profile_id>/history/add', methods=['POST'])
@role_required('doctor')
def add_medical_history_entry(patient_profile_id):
    """
    Add a new medical history entry for a patient
    Creates a new visit with initial diagnosis and treatment
    
    Request body:
        symptoms: Patient symptoms (required)
        diagnosis: Doctor's diagnosis
        notes: Clinical notes
        severity: low/medium/high/critical (default: medium)
        prescriptions: List of prescriptions
        lab_tests: List of lab tests to order
    
    Returns:
        Created visit with all details
    """
    doctor_id = session.get('user_id')
    
    # Verify doctor has access to this patient
    if not validate_doctor_access(doctor_id, patient_profile_id):
        return jsonify({
            'status': 'error',
            'message': 'Access denied. You must have at least one visit with this patient.'
        }), 403
    
    data = request.get_json()
    
    # Validate required fields
    if not data.get('symptoms'):
        return jsonify({
            'status': 'error',
            'message': 'Symptoms are required'
        }), 400
    
    try:
        # Create new visit entry
        visit = create_visit_entry(
            patient_profile_id=patient_profile_id,
            symptoms=data['symptoms'],
            doctor_id=doctor_id,
            severity=data.get('severity', 'medium')
        )
        
        # Add diagnosis and notes if provided
        if data.get('diagnosis') or data.get('notes'):
            visit = add_doctor_notes(
                visit_id=visit.id,
                doctor_id=doctor_id,
                diagnosis=data.get('diagnosis'),
                notes=data.get('notes')
            )
        
        # Add prescriptions if provided
        if data.get('prescriptions') and isinstance(data['prescriptions'], list):
            for rx_data in data['prescriptions']:
                if all(k in rx_data for k in ['medication_name', 'dosage', 'frequency', 'duration']):
                    prescription = Prescription(
                        visit_id=visit.id,
                        medication_name=rx_data['medication_name'],
                        dosage=rx_data['dosage'],
                        frequency=rx_data['frequency'],
                        duration=rx_data['duration'],
                        instructions=rx_data.get('instructions')
                    )
                    db.session.add(prescription)
        
        # Add lab tests if provided
        if data.get('lab_tests') and isinstance(data['lab_tests'], list):
            for test_data in data['lab_tests']:
                if test_data.get('test_name'):
                    lab_test = LabTest(
                        visit_id=visit.id,
                        test_name=test_data['test_name'],
                        test_type=test_data.get('test_type'),
                        instructions=test_data.get('instructions'),
                        status='requested'
                    )
                    db.session.add(lab_test)
        
        db.session.commit()
        
        # Return complete visit with all relationships
        visit_data = visit.to_dict(include_details=True)
        
        return jsonify({
            'status': 'success',
            'message': 'Medical history entry added successfully',
            'data': visit_data
        }), 201
    
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to add medical history: {str(e)}'
        }), 500


@doctor_bp.route('/visits/<int:visit_id>/notes/append', methods=['POST'])
@role_required('doctor')
def append_visit_notes(visit_id):
    """
    Append additional notes to an existing visit
    Maintains append-only history - never overwrites
    
    Request body:
        diagnosis: Additional diagnosis information
        notes: Additional clinical notes
    
    Returns:
        Updated visit details
    """
    doctor_id = session.get('user_id')
    
    data = request.get_json()
    
    try:
        visit = add_doctor_notes(
            visit_id=visit_id,
            doctor_id=doctor_id,
            diagnosis=data.get('diagnosis'),
            notes=data.get('notes')
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Notes appended successfully',
            'data': visit.to_dict(include_details=True)
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'Failed to append notes: {str(e)}'
        }), 500

