#!/usr/bin/env python3
"""
Add test appointments for today
"""
from app import create_app
from models import db, Appointment, User
from datetime import datetime, timedelta
import random

app, socketio = create_app()

with app.app_context():
    print("\n" + "=" * 60)
    print("Adding test appointments for today")
    print("=" * 60)
    
    # Get all doctors
    doctors = User.query.filter_by(role='doctor', is_active=True).all()
    
    # Get all patients
    patients = User.query.filter_by(role='patient', is_active=True).all()
    
    if not doctors:
        print("\n❌ No doctors found in database!")
        print("   Run add_test_doctors.py first")
        exit(1)
    
    if not patients:
        print("\n⚠️  No patients found, creating a test patient...")
        from werkzeug.security import generate_password_hash
        
        test_patient = User(
            phone_number='1234567890',
            password_hash=generate_password_hash('patient123'),
            full_name='Test Patient',
            role='patient',
            is_active=True
        )
        db.session.add(test_patient)
        db.session.commit()
        patients = [test_patient]
        print(f"   ✅ Created test patient: {test_patient.full_name} (Phone: 1234567890)")
    
    # Create appointments for today
    today = datetime.now()
    
    # Define appointment times for today
    appointment_times = [
        today.replace(hour=9, minute=0, second=0),   # 9:00 AM
        today.replace(hour=10, minute=30, second=0), # 10:30 AM
        today.replace(hour=14, minute=0, second=0),  # 2:00 PM
        today.replace(hour=15, minute=30, second=0), # 3:30 PM
        today.replace(hour=16, minute=45, second=0), # 4:45 PM
    ]
    
    reasons = [
        'General checkup',
        'Follow-up consultation',
        'Blood pressure monitoring',
        'Fever and cold symptoms',
        'Diabetes management',
        'Routine health screening',
        'Prescription refill',
        'Medical report review'
    ]
    
    statuses = ['scheduled', 'scheduled', 'scheduled', 'completed', 'cancelled']
    
    created_count = 0
    
    for i, apt_time in enumerate(appointment_times):
        # Check if appointment already exists for this doctor at this time
        existing = Appointment.query.filter_by(
            doctor_id=doctors[0].id,
            appointment_date=apt_time
        ).first()
        
        if existing:
            print(f"   ⏭️  Skipping {apt_time.strftime('%I:%M %p')} - appointment already exists")
            continue
        
        # Create appointment
        appointment = Appointment(
            patient_id=random.choice(patients).id,
            doctor_id=doctors[0].id,  # Assign to first doctor
            appointment_date=apt_time,
            duration_minutes=30,
            reason=random.choice(reasons),
            status=random.choice(statuses),
            meeting_status='not_started'
        )
        
        db.session.add(appointment)
        created_count += 1
        print(f"   ✅ Added: {apt_time.strftime('%I:%M %p')} - {appointment.reason}")
    
    db.session.commit()
    
    print("\n" + "=" * 60)
    print(f"✅ Successfully added {created_count} appointments for today!")
    print("=" * 60)
    print(f"\n📅 Date: {today.strftime('%Y-%m-%d')}")
    print(f"👨‍⚕️ Doctor: {doctors[0].full_name}")
    print(f"\n🔐 Login with:")
    print(f"   Phone: {doctors[0].phone_number}")
    print(f"   Password: doctor123")
    print("\n" + "=" * 60)
