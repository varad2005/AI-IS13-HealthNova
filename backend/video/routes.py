"""
Video Consultation Routes

CRITICAL SECURITY FEATURES:
1. Role-based access: Only doctors can start/end meetings
2. Ownership verification: Users can only access their own appointments
3. Status validation: Meetings must be in correct state for transitions
4. No manual room IDs: appointment_id IS the room identifier

WHY THIS DESIGN:
- Patients never see meeting links or IDs
- Doctor controls when consultation starts/ends
- Patient can only join when doctor is ready
- Prevents unauthorized access to video rooms

REAL-TIME NOTIFICATIONS:
- When doctor starts meeting, patient gets instant notification via Socket.IO
- No polling required - patient UI auto-updates
"""

from flask import jsonify, request, session
from datetime import datetime, timedelta
from models import db, Appointment, User
from auth.decorators import login_required, role_required
from . import video_bp
from video_consultation import notify_patient_meeting_started, notify_patient_meeting_ended


@video_bp.route('/create-instant-appointment', methods=['POST'])
@role_required('doctor')
def create_instant_appointment():
    """
    Create an instant appointment for immediate video consultation
    
    USE CASE: Doctor wants to start a meeting with a patient from the registry
    without a pre-scheduled appointment
    
    WORKFLOW:
    1. Create appointment with current timestamp
    2. Set status to 'scheduled' (will be immediately started)
    3. Return appointment_id for use in start-meeting endpoint
    """
    try:
        doctor_id = session.get('user_id')
        data = request.get_json()
        
        patient_id = data.get('patient_id')
        reason = data.get('reason', 'Instant consultation')
        
        if not patient_id:
            return jsonify({
                'success': False,
                'error': 'Patient ID is required'
            }), 400
        
        # Verify patient exists
        patient = User.query.filter_by(id=patient_id, role='patient').first()
        if not patient:
            return jsonify({
                'success': False,
                'error': 'Patient not found'
            }), 404
        
        # Check if there's already a live meeting with this patient
        existing_live = Appointment.query.filter_by(
            doctor_id=doctor_id,
            patient_id=patient_id,
            meeting_status='live'
        ).first()
        
        if existing_live:
            return jsonify({
                'success': True,
                'appointment_id': existing_live.id,
                'message': 'Using existing live meeting'
            }), 200
        
        # Create instant appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=datetime.utcnow(),
            duration_minutes=30,
            reason=reason,
            status='scheduled',
            meeting_status='not_started'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'appointment_id': appointment.id,
            'message': 'Instant appointment created'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating instant appointment: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/start-meeting/<int:appointment_id>', methods=['POST'])
@role_required('doctor')
def start_meeting(appointment_id):
    """
    Doctor starts a video consultation meeting - INSTANT START, NO INTERMEDIATE STEPS
    
    AUTHORIZATION:
    - Only doctors (role='doctor') can start meetings
    - Doctor must be the assigned doctor for this appointment
    
    WORKFLOW:
    1. Verify appointment exists and belongs to this doctor
    2. Update meeting_status from 'not_started' to 'live'
    3. Record meeting_started_at timestamp
    4. Send real-time notification to patient via Socket.IO
    5. Return room_id for immediate redirect to video call
    
    SECURITY: appointment_id becomes the WebRTC room ID
    """
    try:
        doctor_id = session.get('user_id')
        doctor_name = session.get('full_name', 'Doctor')
        
        # Find appointment and verify ownership
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Appointment not found'
            }), 404
        
        if appointment.doctor_id != doctor_id:
            return jsonify({
                'success': False,
                'error': 'You can only start your own appointments'
            }), 403
        
        # Verify appointment is scheduled (not cancelled/completed)
        if appointment.status in ['cancelled', 'completed']:
            return jsonify({
                'success': False,
                'error': f'Cannot start {appointment.status} appointment'
            }), 400
        
        # Check meeting hasn't already started
        if appointment.meeting_status == 'live':
            # Already live - just return the room info
            return jsonify({
                'success': True,
                'message': 'Meeting already in progress',
                'room_id': str(appointment_id),
                'appointment': appointment.to_dict(include_participants=True)
            }), 200
        
        # Start the meeting
        appointment.meeting_status = 'live'
        appointment.meeting_started_at = datetime.utcnow()
        
        db.session.commit()
        
        # Get appointment data for notification
        appointment_data = appointment.to_dict(include_participants=True)
        appointment_data['doctor_name'] = doctor_name
        
        # REAL-TIME: Notify patient immediately via Socket.IO
        notify_patient_meeting_started(appointment.patient_id, appointment_data)
        
        return jsonify({
            'success': True,
            'message': 'Meeting started successfully',
            'room_id': str(appointment_id),
            'appointment': appointment_data
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error starting meeting: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/end-meeting/<int:appointment_id>', methods=['POST'])
@role_required('doctor')
def end_meeting(appointment_id):
    """
    Doctor ends a video consultation meeting
    
    WORKFLOW:
    1. Verify appointment belongs to this doctor
    2. Update meeting_status to 'ended'
    3. Notify patient in real-time to disconnect gracefully
    """
    try:
        doctor_id = session.get('user_id')
        
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Appointment not found'
            }), 404
        
        if appointment.doctor_id != doctor_id:
            return jsonify({
                'success': False,
                'error': 'You can only end your own appointments'
            }), 403
        
        if appointment.meeting_status != 'live':
            return jsonify({
                'success': False,
                'error': 'Meeting is not currently live'
            }), 400
        
        # End the meeting
        appointment.meeting_status = 'ended'
        appointment.meeting_ended_at = datetime.utcnow()
        appointment.status = 'completed'
        
        db.session.commit()
        
        # REAL-TIME: Notify patient to disconnect gracefully
        notify_patient_meeting_ended(appointment.patient_id, appointment_id)
        
        return jsonify({
            'success': True,
            'message': 'Meeting ended successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/meeting-status/<int:appointment_id>', methods=['GET'])
@login_required
def get_meeting_status(appointment_id):
    """
    Check if a meeting is live (patient or doctor can call this)
    
    AUTHORIZATION:
    - User must be either the patient or doctor for this appointment
    
    USE CASES:
    - Enables "Join Consultation" button when status='live'
    - Shows appropriate status messages to patient
    
    RESPONSE:
    - meeting_status: 'not_started' | 'live' | 'ended'
    - can_join: boolean (true if user can join the meeting now)
    - message: User-friendly status message
    """
    try:
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Appointment not found'
            }), 404
        
        # Verify user is part of this appointment
        is_participant = (
            appointment.patient_id == user_id or 
            appointment.doctor_id == user_id
        )
        
        if not is_participant:
            return jsonify({
                'success': False,
                'error': 'You are not authorized to access this appointment'
            }), 403
        
        # Determine if user can join
        is_doctor = user_role == 'doctor'
        is_patient = user_role == 'patient'
        
        can_join = False
        message = ''
        
        if appointment.meeting_status == 'not_started':
            if is_doctor:
                message = 'Click Start Consultation to begin'
                can_join = True  # Doctor can join anytime (triggers start)
            else:
                message = 'Waiting for doctor to start consultation...'
                can_join = False  # Patient must wait
        
        elif appointment.meeting_status == 'live':
            message = 'Consultation is live - Click to join'
            can_join = True  # Both can join
        
        elif appointment.meeting_status == 'ended':
            message = 'Consultation has ended'
            can_join = False  # No one can join
        
        return jsonify({
            'success': True,
            'meeting_status': appointment.meeting_status,
            'can_join': can_join,
            'message': message,
            'appointment': appointment.to_dict(include_participants=True),
            'room_id': str(appointment_id)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/my-appointments', methods=['GET'])
@login_required
def get_my_appointments():
    """
    Get all appointments for current user (doctor or patient)
    
    FILTERS:
    - status: 'scheduled', 'completed', 'cancelled' (optional)
    - upcoming: boolean - only future appointments (optional)
    - meeting_status: 'not_started', 'live', 'ended' (optional)
    
    USE CASES:
    - Doctor dashboard: Show upcoming appointments with Start buttons
    - Patient dashboard: Show appointments with conditional Join buttons
    """
    try:
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        # Base query based on user role
        if user_role == 'doctor':
            query = Appointment.query.filter_by(doctor_id=user_id)
        elif user_role == 'patient':
            query = Appointment.query.filter_by(patient_id=user_id)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid user role'
            }), 400
        
        # Apply filters from query parameters
        status_filter = request.args.get('status')
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        meeting_status_filter = request.args.get('meeting_status')
        if meeting_status_filter:
            query = query.filter_by(meeting_status=meeting_status_filter)
        
        upcoming = request.args.get('upcoming', '').lower() == 'true'
        if upcoming:
            query = query.filter(Appointment.appointment_date >= datetime.utcnow())
        
        # Order by appointment date
        appointments = query.order_by(Appointment.appointment_date.desc()).all()
        
        return jsonify({
            'success': True,
            'appointments': [apt.to_dict(include_participants=True) for apt in appointments],
            'count': len(appointments)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/create-appointment', methods=['POST'])
@login_required
def create_appointment():
    """
    Create a new appointment (can be called by patient or admin)
    
    REQUIRED FIELDS:
    - doctor_id: ID of the doctor
    - appointment_date: ISO format datetime
    - reason: Reason for consultation (optional)
    
    DEFAULT VALUES:
    - status: 'scheduled'
    - meeting_status: 'not_started'
    - duration_minutes: 30
    """
    try:
        user_id = session.get('user_id')
        user_role = session.get('role')
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('doctor_id') or not data.get('appointment_date'):
            return jsonify({
                'success': False,
                'error': 'doctor_id and appointment_date are required'
            }), 400
        
        # If current user is patient, use their ID
        # If admin/doctor, use provided patient_id
        if user_role == 'patient':
            patient_id = user_id
        else:
            patient_id = data.get('patient_id')
            if not patient_id:
                return jsonify({
                    'success': False,
                    'error': 'patient_id is required'
                }), 400
        
        # Parse appointment date
        try:
            appointment_date = datetime.fromisoformat(data['appointment_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid appointment_date format. Use ISO format'
            }), 400
        
        # Create appointment
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=data['doctor_id'],
            appointment_date=appointment_date,
            duration_minutes=data.get('duration_minutes', 30),
            reason=data.get('reason'),
            status='scheduled',
            meeting_status='not_started'
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Appointment created successfully',
            'appointment': appointment.to_dict(include_participants=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
