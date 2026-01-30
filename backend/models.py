from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model for authentication - supports patient, doctor, lab roles"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(15), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'patient', 'doctor', 'lab'
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    patient_profile = db.relationship('PatientProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and store password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary (exclude password)"""
        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'role': self.role,
            'full_name': self.full_name,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class PatientProfile(db.Model):
    """One profile per patient - contains demographic and medical history"""
    __tablename__ = 'patient_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Demographic information
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(15), nullable=True)
    
    # Medical history
    allergies = db.Column(db.Text, nullable=True)  # Comma-separated or JSON
    chronic_conditions = db.Column(db.Text, nullable=True)  # Comma-separated or JSON
    previous_surgeries = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    visits = db.relationship('Visit', backref='patient_profile', cascade='all, delete-orphan', order_by='Visit.created_at.desc()')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'age': self.age,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'address': self.address,
            'emergency_contact': self.emergency_contact,
            'allergies': self.allergies,
            'chronic_conditions': self.chronic_conditions,
            'previous_surgeries': self.previous_surgeries,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Visit(db.Model):
    """Each health issue creates a new visit - append-only history"""
    __tablename__ = 'visits'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_profile_id = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Assigned doctor
    
    # Visit details
    symptoms = db.Column(db.Text, nullable=False)  # Patient's initial complaint
    ai_summary = db.Column(db.Text, nullable=True)  # AI-generated summary of symptoms
    diagnosis = db.Column(db.Text, nullable=True)  # Doctor's diagnosis
    notes = db.Column(db.Text, nullable=True)  # Doctor's notes
    severity = db.Column(db.String(20), nullable=True)  # 'low', 'medium', 'high', 'critical'
    status = db.Column(db.String(20), default='open')  # 'open', 'in_progress', 'completed'
    visit_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    doctor = db.relationship('User', foreign_keys=[doctor_id])
    lab_tests = db.relationship('LabTest', backref='visit', cascade='all, delete-orphan')
    prescriptions = db.relationship('Prescription', backref='visit', cascade='all, delete-orphan')
    messages = db.relationship('Message', backref='visit', cascade='all, delete-orphan', order_by='Message.created_at')
    
    def to_dict(self, include_details=False):
        data = {
            'id': self.id,
            'patient_profile_id': self.patient_profile_id,
            'doctor_id': self.doctor_id,
            'symptoms': self.symptoms,
            'ai_summary': self.ai_summary,
            'diagnosis': self.diagnosis,
            'notes': self.notes,
            'severity': self.severity,
            'status': self.status,
            'visit_date': self.visit_date.isoformat(),
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        
        if include_details:
            data['doctor_name'] = self.doctor.full_name if self.doctor else None
            data['lab_tests'] = [test.to_dict() for test in self.lab_tests]
            data['prescriptions'] = [rx.to_dict() for rx in self.prescriptions]
        
        return data


class LabTest(db.Model):
    """Lab test requests and results"""
    __tablename__ = 'lab_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Assigned lab
    
    # Test information
    test_name = db.Column(db.String(200), nullable=False)  # e.g., "Blood Sugar Test"
    test_type = db.Column(db.String(100), nullable=True)  # e.g., "blood", "urine"
    instructions = db.Column(db.Text, nullable=True)  # Special instructions
    
    # Scheduling and status
    status = db.Column(db.String(20), default='requested')  # 'requested', 'approved', 'rejected', 'scheduled', 'completed'
    scheduled_time = db.Column(db.DateTime, nullable=True)
    
    # Results
    result = db.Column(db.Text, nullable=True)  # Test results or findings
    remarks = db.Column(db.Text, nullable=True)  # Lab technician remarks
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lab = db.relationship('User', foreign_keys=[lab_id])
    reports = db.relationship('TestReport', backref='lab_test', cascade='all, delete-orphan')
    
    def to_dict(self, include_reports=False):
        data = {
            'id': self.id,
            'visit_id': self.visit_id,
            'lab_id': self.lab_id,
            'test_name': self.test_name,
            'test_type': self.test_type,
            'instructions': self.instructions,
            'status': self.status,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'result': self.result,
            'remarks': self.remarks,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_reports:
            data['reports'] = [report.to_dict() for report in self.reports]
        
        if self.lab:
            data['lab_name'] = self.lab.full_name
        
        return data


class TestReport(db.Model):
    """Metadata for uploaded lab test reports (optional file attachments)"""
    __tablename__ = 'test_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    lab_test_id = db.Column(db.Integer, db.ForeignKey('lab_tests.id'), nullable=False)
    
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Relative path or cloud URL
    file_type = db.Column(db.String(50), nullable=True)  # 'pdf', 'image'
    file_size = db.Column(db.Integer, nullable=True)  # In bytes
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'lab_test_id': self.lab_test_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class Prescription(db.Model):
    """Doctor's prescriptions for a visit"""
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    
    medication_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)  # e.g., "500mg"
    frequency = db.Column(db.String(100), nullable=False)  # e.g., "twice daily"
    duration = db.Column(db.String(100), nullable=False)  # e.g., "7 days"
    instructions = db.Column(db.Text, nullable=True)  # e.g., "take after meals"
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'visit_id': self.visit_id,
            'medication_name': self.medication_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'duration': self.duration,
            'instructions': self.instructions,
            'created_at': self.created_at.isoformat()
        }


class Message(db.Model):
    """Messages between patient and doctor (text + voice metadata)"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visits.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Message content
    message_type = db.Column(db.String(20), default='text')  # 'text', 'voice'
    content = db.Column(db.Text, nullable=True)  # Text message or transcription
    voice_file_path = db.Column(db.String(500), nullable=True)  # Path to voice file
    voice_duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'visit_id': self.visit_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.full_name,
            'message_type': self.message_type,
            'content': self.content,
            'voice_file_path': self.voice_file_path,
            'voice_duration': self.voice_duration,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read
        }


class Appointment(db.Model):
    """Appointments between patients and doctors with video consultation support"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Appointment details
    appointment_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)  # Default 30 min consultation
    reason = db.Column(db.Text, nullable=True)  # Reason for consultation
    notes = db.Column(db.Text, nullable=True)  # Doctor's notes after consultation
    
    # Status tracking
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'completed', 'cancelled', 'no_show'
    
    # Video consultation control
    # CRITICAL: meeting_status controls who can join the video call
    # - "not_started": Default state, patient CANNOT join
    # - "live": Doctor started meeting, patient CAN join
    # - "ended": Meeting finished, no one can join
    meeting_status = db.Column(db.String(20), default='not_started')
    meeting_started_at = db.Column(db.DateTime, nullable=True)
    meeting_ended_at = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('User', foreign_keys=[patient_id], backref='patient_appointments')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_appointments')
    
    def to_dict(self, include_participants=False):
        """Convert appointment to dictionary
        
        WHY meeting_status IS CRITICAL:
        - Patient dashboard checks this to enable/disable Join button
        - Doctor can only start their own appointments
        - appointment_id becomes the WebRTC room ID (no manual sharing needed)
        """
        data = {
            'id': self.id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'appointment_date': self.appointment_date.isoformat(),
            'duration_minutes': self.duration_minutes,
            'reason': self.reason,
            'notes': self.notes,
            'status': self.status,
            'meeting_status': self.meeting_status,  # Key field for video consultation control
            'meeting_started_at': self.meeting_started_at.isoformat() if self.meeting_started_at else None,
            'meeting_ended_at': self.meeting_ended_at.isoformat() if self.meeting_ended_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_participants:
            data['patient_name'] = self.patient.full_name if self.patient else None
            data['patient_phone'] = self.patient.phone_number if self.patient else None
            data['doctor_name'] = self.doctor.full_name if self.doctor else None
            data['doctor_phone'] = self.doctor.phone_number if self.doctor else None
        
        return data


class VideoMeeting(db.Model):
    """
    Video consultation meeting state management.
    
    Why separate from Appointment?
    - Not all appointments need video (some are in-person)
    - Meetings can be created ad-hoc without appointments
    - Cleaner state management for video lifecycle
    """
    __tablename__ = 'video_meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    
    # Meeting lifecycle
    status = db.Column(db.String(20), default='SCHEDULED')  # SCHEDULED, ACTIVE, ENDED, CANCELLED
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    duration_seconds = db.Column(db.Integer, nullable=True)  # Calculated from started_at to ended_at
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    doctor = db.relationship('User', foreign_keys=[doctor_id])
    patient = db.relationship('User', foreign_keys=[patient_id])
    appointment = db.relationship('Appointment', foreign_keys=[appointment_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'doctor_id': self.doctor_id,
            'patient_id': self.patient_id,
            'appointment_id': self.appointment_id,
            'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat()
        }


class Payment(db.Model):
    """
    Payment transaction records with idempotency.
    
    Why separate table?
    - Audit trail for financial transactions
    - Support multiple payment methods (Razorpay, UPI, cash)
    - Idempotency enforcement via unique constraints
    """
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Razorpay details
    razorpay_order_id = db.Column(db.String(100), nullable=False, index=True)
    razorpay_payment_id = db.Column(db.String(100), unique=True, nullable=False, index=True)  # Idempotency key
    
    # Payment details
    amount = db.Column(db.Integer, nullable=False)  # Amount in paise (smallest currency unit)
    currency = db.Column(db.String(10), default='INR')
    status = db.Column(db.String(20), default='PENDING')  # PENDING, PAID, FAILED, REFUNDED
    
    # Linked entity (appointment, lab test, etc.)
    entity_type = db.Column(db.String(50), nullable=True)  # 'appointment', 'lab_test', 'subscription'
    entity_id = db.Column(db.Integer, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    failed_at = db.Column(db.DateTime, nullable=True)
    refunded_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='payments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'razorpay_order_id': self.razorpay_order_id,
            'razorpay_payment_id': self.razorpay_payment_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'created_at': self.created_at.isoformat(),
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None
        }
