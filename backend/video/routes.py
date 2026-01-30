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
"""

from flask import jsonify, request
from datetime import datetime
from models import db, Appointment, User
from auth.decorators import login_required, role_required
from . import video_bp


@video_bp.route('/start-meeting/<int:appointment_id>', methods=['POST'])
@login_required
def start_meeting(appointment_id):
    """
    Doctor starts a video consultation meeting
    
    AUTHORIZATION:
    - Only doctors (role='doctor') can start meetings
    - Doctor must be the assigned doctor for this appointment
    
    WORKFLOW:
    1. Verify user is a doctor
    2. Verify appointment exists and belongs to this doctor
    3. Update meeting_status from 'not_started' to 'live'
    4. Record meeting_started_at timestamp
    5. Return success (doctor auto-joins, patient can now join)
    
    SECURITY: appointment_id becomes the WebRTC room ID
    - No need to generate or share meeting links
    - Patient dashboard polls this appointment's status
    - When status='live', patient's Join button enables
    """
    try:
        # STEP 1: Verify user is a doctor
        if current_user.role != 'doctor':
            return jsonify({
                'success': False,
                'error': 'Only doctors can start meetings'
            }), 403
        
        # STEP 2: Find appointment and verify ownership
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Appointment not found'
            }), 404
        
        if appointment.doctor_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'You can only start your own appointments'
            }), 403
        
        # STEP 3: Verify appointment is scheduled (not cancelled/completed)
        if appointment.status in ['cancelled', 'completed']:
            return jsonify({
                'success': False,
                'error': f'Cannot start {appointment.status} appointment'
            }), 400
        
        # STEP 4: Check meeting hasn't already started
        if appointment.meeting_status == 'live':
            return jsonify({
                'success': True,
                'message': 'Meeting already in progress',
                'appointment': appointment.to_dict(include_participants=True)
            }), 200
        
        # STEP 5: Start the meeting
        appointment.meeting_status = 'live'
        appointment.meeting_started_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Meeting started successfully',
            'appointment': appointment.to_dict(include_participants=True),
            'room_id': str(appointment_id)  # appointment_id IS the room identifier
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
    - Patient dashboard polls this every 3 seconds
    - Enables "Join Consultation" button when status='live'
    - Shows appropriate status messages to patient
    
    RESPONSE:
    - meeting_status: 'not_started' | 'live' | 'ended'
    - can_join: boolean (true if user can join the meeting now)
    - message: User-friendly status message
    """
    try:
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Appointment not found'
            }), 404
        
        # Verify user is part of this appointment
        is_participant = (
            appointment.patient_id == current_user.id or 
            appointment.doctor_id == current_user.id
        )
        
        if not is_participant:
            return jsonify({
                'success': False,
                'error': 'You are not authorized to access this appointment'
            }), 403
        
        # Determine if user can join
        is_doctor = current_user.role == 'doctor'
        is_patient = current_user.role == 'patient'
        
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


@video_bp.route('/end-meeting/<int:appointment_id>', methods=['POST'])
@login_required
def end_meeting(appointment_id):
    """
    Doctor ends a video consultation meeting
    
    AUTHORIZATION:
    - Only doctors can end meetings
    - Doctor must be the assigned doctor for this appointment
    
    WORKFLOW:
    1. Verify user is a doctor
    2. Verify appointment exists and belongs to this doctor
    3. Update meeting_status to 'ended'
    4. Record meeting_ended_at timestamp
    5. Update appointment status to 'completed'
    """
    try:
        # STEP 1: Verify user is a doctor
        if current_user.role != 'doctor':
            return jsonify({
                'success': False,
                'error': 'Only doctors can end meetings'
            }), 403
        
        # STEP 2: Find appointment and verify ownership
        appointment = Appointment.query.get(appointment_id)
        
        if not appointment:
            return jsonify({
                'success': False,
                'error': 'Appointment not found'
            }), 404
        
        if appointment.doctor_id != current_user.id:
            return jsonify({
                'success': False,
                'error': 'You can only end your own appointments'
            }), 403
        
        # STEP 3: Check meeting is actually live
        if appointment.meeting_status == 'ended':
            return jsonify({
                'success': True,
                'message': 'Meeting already ended',
                'appointment': appointment.to_dict(include_participants=True)
            }), 200
        
        # STEP 4: End the meeting
        appointment.meeting_status = 'ended'
        appointment.meeting_ended_at = datetime.utcnow()
        appointment.status = 'completed'  # Mark appointment as completed
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Meeting ended successfully',
            'appointment': appointment.to_dict(include_participants=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@video_bp.route('/my-appointments', methods=['GET'])
@login_required
def get_my_appointments(current_user):
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
        # Base query based on user role
        if current_user.role == 'doctor':
            query = Appointment.query.filter_by(doctor_id=current_user.id)
        elif current_user.role == 'patient':
            query = Appointment.query.filter_by(patient_id=current_user.id)
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
def create_appointment(current_user):
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
        data = request.get_json()
        
        # Validate required fields
        if not data.get('doctor_id') or not data.get('appointment_date'):
            return jsonify({
                'success': False,
                'error': 'doctor_id and appointment_date are required'
            }), 400
        
        # If current user is patient, use their ID
        # If admin/doctor, use provided patient_id
        if current_user.role == 'patient':
            patient_id = current_user.id
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
