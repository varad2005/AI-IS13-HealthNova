"""
Medical History Timeline Utility Functions
Append-only medical history tracking - replaces physical patient files
"""
from models import Visit, PatientProfile, User, Prescription, LabTest
from datetime import datetime


def format_timeline_entry(visit, include_patient_info=False):
    """
    Format a single visit into timeline entry with all medical data
    
    Args:
        visit: Visit object
        include_patient_info: Include patient demographic data (for doctor view)
    
    Returns:
        dict: Formatted timeline entry
    """
    entry = {
        'visit_id': visit.id,
        'visit_date': visit.visit_date.isoformat(),
        'created_at': visit.created_at.isoformat(),
        'status': visit.status,
        'severity': visit.severity,
        
        # Medical data
        'symptoms': visit.symptoms,
        'ai_summary': visit.ai_summary,
        'diagnosis': visit.diagnosis or 'Pending',
        'notes': visit.notes,
        
        # Doctor information
        'doctor_id': visit.doctor_id,
        'doctor_name': visit.doctor.full_name if visit.doctor else 'Not assigned',
        
        # Prescriptions
        'prescriptions': [
            {
                'medication_name': rx.medication_name,
                'dosage': rx.dosage,
                'frequency': rx.frequency,
                'duration': rx.duration,
                'instructions': rx.instructions,
                'prescribed_at': rx.created_at.isoformat()
            }
            for rx in visit.prescriptions
        ],
        
        # Lab tests and results
        'lab_tests': [
            {
                'test_name': test.test_name,
                'test_type': test.test_type,
                'status': test.status,
                'scheduled_time': test.scheduled_time.isoformat() if test.scheduled_time else None,
                'result': test.result,
                'remarks': test.remarks,
                'requested_at': test.created_at.isoformat()
            }
            for test in visit.lab_tests
        ]
    }
    
    # Include patient info if requested (for doctor view)
    if include_patient_info and visit.patient_profile:
        entry['patient'] = {
            'profile_id': visit.patient_profile.id,
            'name': visit.patient_profile.user.full_name,
            'age': visit.patient_profile.age,
            'gender': visit.patient_profile.gender,
            'blood_group': visit.patient_profile.blood_group
        }
    
    return entry


def get_patient_timeline(patient_profile_id, limit=None):
    """
    Get complete medical history timeline for a patient
    Ordered by date descending (newest first)
    
    Args:
        patient_profile_id: Patient profile ID
        limit: Optional limit on number of visits to return
    
    Returns:
        list: Timeline entries
    """
    query = Visit.query.filter_by(
        patient_profile_id=patient_profile_id
    ).order_by(Visit.visit_date.desc())
    
    if limit:
        query = query.limit(limit)
    
    visits = query.all()
    
    return [format_timeline_entry(visit) for visit in visits]


def get_patient_summary(patient_profile):
    """
    Get patient summary with key medical information
    
    Args:
        patient_profile: PatientProfile object
    
    Returns:
        dict: Patient summary
    """
    total_visits = Visit.query.filter_by(
        patient_profile_id=patient_profile.id
    ).count()
    
    completed_visits = Visit.query.filter_by(
        patient_profile_id=patient_profile.id,
        status='completed'
    ).count()
    
    # Get all unique doctors who treated this patient
    visits_with_doctors = Visit.query.filter(
        Visit.patient_profile_id == patient_profile.id,
        Visit.doctor_id.isnot(None)
    ).all()
    
    unique_doctor_ids = set([v.doctor_id for v in visits_with_doctors])
    doctors_count = len(unique_doctor_ids)
    
    return {
        'profile_id': patient_profile.id,
        'user_id': patient_profile.user_id,
        'name': patient_profile.user.full_name,
        'age': patient_profile.age,
        'gender': patient_profile.gender,
        'blood_group': patient_profile.blood_group,
        'phone': patient_profile.user.phone_number,
        'email': patient_profile.user.email,
        
        # Medical background
        'allergies': patient_profile.allergies,
        'chronic_conditions': patient_profile.chronic_conditions,
        'previous_surgeries': patient_profile.previous_surgeries,
        
        # Statistics
        'total_visits': total_visits,
        'completed_visits': completed_visits,
        'doctors_consulted': doctors_count,
        'member_since': patient_profile.created_at.isoformat()
    }


def create_visit_entry(patient_profile_id, symptoms, doctor_id=None, severity='medium'):
    """
    Create a new visit entry in medical history
    
    Args:
        patient_profile_id: Patient profile ID
        symptoms: Patient symptoms description
        doctor_id: Assigned doctor ID (optional)
        severity: Severity level (default: medium)
    
    Returns:
        Visit: Created visit object
    """
    from models import db
    
    visit = Visit(
        patient_profile_id=patient_profile_id,
        doctor_id=doctor_id,
        symptoms=symptoms,
        severity=severity,
        status='open',
        visit_date=datetime.utcnow()
    )
    
    db.session.add(visit)
    db.session.commit()
    
    return visit


def add_doctor_notes(visit_id, doctor_id, diagnosis=None, notes=None):
    """
    Add or append doctor's diagnosis and notes to a visit
    Maintains append-only integrity - never overwrites
    
    Args:
        visit_id: Visit ID
        doctor_id: Doctor ID (for verification)
        diagnosis: Diagnosis text
        notes: Clinical notes
    
    Returns:
        Visit: Updated visit object
    """
    from models import db
    
    visit = Visit.query.filter_by(id=visit_id, doctor_id=doctor_id).first()
    
    if not visit:
        raise ValueError("Visit not found or access denied")
    
    if visit.status == 'completed':
        raise ValueError("Cannot modify completed visit - history is append-only")
    
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    
    # Append diagnosis (never overwrite)
    if diagnosis:
        if visit.diagnosis:
            visit.diagnosis += f"\n\n[{timestamp}]\n{diagnosis}"
        else:
            visit.diagnosis = f"[{timestamp}]\n{diagnosis}"
    
    # Append notes (never overwrite)
    if notes:
        if visit.notes:
            visit.notes += f"\n\n[{timestamp}]\n{notes}"
        else:
            visit.notes = f"[{timestamp}]\n{notes}"
    
    db.session.commit()
    
    return visit


def validate_doctor_access(doctor_id, patient_profile_id):
    """
    Check if doctor has access to patient's medical history
    Access is granted if doctor has at least one assigned visit
    
    Args:
        doctor_id: Doctor ID
        patient_profile_id: Patient profile ID
    
    Returns:
        bool: True if access granted
    """
    has_visit = Visit.query.filter_by(
        doctor_id=doctor_id,
        patient_profile_id=patient_profile_id
    ).first()
    
    return has_visit is not None
