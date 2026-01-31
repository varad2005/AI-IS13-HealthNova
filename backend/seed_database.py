#!/usr/bin/env python3
"""
Comprehensive Database Seeding Script
======================================
Creates a complete, realistic dataset for the Rural Healthcare Platform.

This script creates:
- Multiple doctors with different specializations
- Multiple lab technicians
- Realistic patient profiles with medical history
- Past and upcoming appointments
- Medical visits with diagnoses
- Lab tests and prescriptions
- Complete medical records
"""

from app import create_app
from models import (
    db, User, PatientProfile, Visit, LabTest, TestReport, 
    Prescription, Message, Appointment, VideoMeeting, Payment
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

app, socketio = create_app()

# ============================================
# SEED DATA CONFIGURATION
# ============================================

DOCTORS_DATA = [
    {
        'phone': '9876543210',
        'password': 'doctor123',
        'name': 'Dr. Priya Sharma',
        'email': 'priya.sharma@healthnova.com',
        'specialization': 'General Physician'
    },
    {
        'phone': '9876543211',
        'password': 'doctor123',
        'name': 'Dr. Rajesh Kumar',
        'email': 'rajesh.kumar@healthnova.com',
        'specialization': 'Cardiologist'
    },
    {
        'phone': '9876543212',
        'password': 'doctor123',
        'name': 'Dr. Anita Singh',
        'email': 'anita.singh@healthnova.com',
        'specialization': 'Pediatrician'
    },
    {
        'phone': '9876543213',
        'password': 'doctor123',
        'name': 'Dr. Vikram Patel',
        'email': 'vikram.patel@healthnova.com',
        'specialization': 'Orthopedic Surgeon'
    }
]

LAB_TECHNICIANS_DATA = [
    {
        'phone': '9876543220',
        'password': 'lab123',
        'name': 'Ramesh Lab Services',
        'email': 'ramesh.lab@healthnova.com'
    },
    {
        'phone': '9876543221',
        'password': 'lab123',
        'name': 'City Diagnostics Center',
        'email': 'city.diagnostics@healthnova.com'
    }
]

PATIENTS_DATA = [
    {
        'phone': '9123456780',
        'password': 'patient123',
        'name': 'Ramesh Kumar',
        'email': 'ramesh.kumar@email.com',
        'age': 45,
        'gender': 'Male',
        'blood_group': 'B+',
        'address': 'Village Rampur, District Sitapur, UP - 261001',
        'emergency_contact': '9123456789',
        'allergies': 'Penicillin, Peanuts',
        'chronic_conditions': 'Type 2 Diabetes, Hypertension',
        'previous_surgeries': 'Appendectomy (2015)'
    },
    {
        'phone': '9123456781',
        'password': 'patient123',
        'name': 'Sunita Devi',
        'email': 'sunita.devi@email.com',
        'age': 38,
        'gender': 'Female',
        'blood_group': 'O+',
        'address': 'Mohalla Nagar, Lucknow, UP - 226001',
        'emergency_contact': '9123456790',
        'allergies': 'None',
        'chronic_conditions': 'Asthma',
        'previous_surgeries': 'None'
    },
    {
        'phone': '9123456782',
        'password': 'patient123',
        'name': 'Amit Verma',
        'email': 'amit.verma@email.com',
        'age': 52,
        'gender': 'Male',
        'blood_group': 'A+',
        'address': 'Sector 15, Noida, UP - 201301',
        'emergency_contact': '9123456791',
        'allergies': 'Sulfa drugs',
        'chronic_conditions': 'High Cholesterol, Arthritis',
        'previous_surgeries': 'Knee Replacement (2020)'
    },
    {
        'phone': '9123456783',
        'password': 'patient123',
        'name': 'Priya Yadav',
        'email': 'priya.yadav@email.com',
        'age': 29,
        'gender': 'Female',
        'blood_group': 'AB+',
        'address': 'Gomti Nagar, Lucknow, UP - 226010',
        'emergency_contact': '9123456792',
        'allergies': 'Latex',
        'chronic_conditions': 'None',
        'previous_surgeries': 'None'
    },
    {
        'phone': '9123456784',
        'password': 'patient123',
        'name': 'Suresh Gupta',
        'email': 'suresh.gupta@email.com',
        'age': 65,
        'gender': 'Male',
        'blood_group': 'O-',
        'address': 'Civil Lines, Allahabad, UP - 211001',
        'emergency_contact': '9123456793',
        'allergies': 'Aspirin',
        'chronic_conditions': 'Heart Disease, Diabetes, Kidney Disease',
        'previous_surgeries': 'Bypass Surgery (2018), Cataract (2021)'
    },
    {
        'phone': '9123456785',
        'password': 'patient123',
        'name': 'Meena Sharma',
        'email': 'meena.sharma@email.com',
        'age': 42,
        'gender': 'Female',
        'blood_group': 'B-',
        'address': 'Hazratganj, Lucknow, UP - 226001',
        'emergency_contact': '9123456794',
        'allergies': 'None',
        'chronic_conditions': 'Thyroid disorder',
        'previous_surgeries': 'Gallbladder removal (2019)'
    },
    {
        'phone': '9123456786',
        'password': 'patient123',
        'name': 'Rahul Singh',
        'email': 'rahul.singh@email.com',
        'age': 35,
        'gender': 'Male',
        'blood_group': 'A-',
        'address': 'Indirapuram, Ghaziabad, UP - 201014',
        'emergency_contact': '9123456795',
        'allergies': 'None',
        'chronic_conditions': 'None',
        'previous_surgeries': 'None'
    },
    {
        'phone': '9123456787',
        'password': 'patient123',
        'name': 'Anjali Mishra',
        'email': 'anjali.mishra@email.com',
        'age': 27,
        'gender': 'Female',
        'blood_group': 'AB-',
        'address': 'Aliganj, Lucknow, UP - 226024',
        'emergency_contact': '9123456796',
        'allergies': 'Iodine',
        'chronic_conditions': 'PCOD',
        'previous_surgeries': 'None'
    }
]

SYMPTOMS_LIBRARY = [
    "Fever, headache, and body aches for 3 days",
    "Persistent cough and chest congestion",
    "Severe abdominal pain and nausea",
    "High blood sugar levels, feeling tired and thirsty",
    "Joint pain and stiffness in knees",
    "Breathing difficulty and wheezing",
    "Chest pain and irregular heartbeat",
    "Skin rash and itching",
    "Back pain radiating to legs",
    "Frequent urination and burning sensation",
    "Dizziness and low blood pressure",
    "Migraine headache with vision problems"
]

DIAGNOSES_LIBRARY = [
    "Viral Fever - Common Cold",
    "Acute Bronchitis",
    "Gastroenteritis",
    "Uncontrolled Diabetes Type 2",
    "Osteoarthritis",
    "Asthma Exacerbation",
    "Angina Pectoris",
    "Allergic Dermatitis",
    "Lumbar Disc Prolapse",
    "Urinary Tract Infection",
    "Hypotension",
    "Migraine with Aura"
]

MEDICATIONS_LIBRARY = [
    ("Paracetamol", "500mg", "Three times daily", "5 days", "Take after meals"),
    ("Amoxicillin", "500mg", "Twice daily", "7 days", "Complete full course"),
    ("Metformin", "500mg", "Twice daily", "30 days", "Take with meals"),
    ("Ibuprofen", "400mg", "As needed", "10 days", "Don't exceed 3 doses per day"),
    ("Omeprazole", "20mg", "Once daily", "14 days", "Take before breakfast"),
    ("Salbutamol Inhaler", "2 puffs", "As needed", "30 days", "Use during breathing difficulty"),
    ("Atorvastatin", "10mg", "Once daily at night", "30 days", "Take after dinner"),
    ("Cetirizine", "10mg", "Once daily", "7 days", "Take at bedtime"),
    ("Diclofenac Gel", "Apply", "Three times daily", "10 days", "For external use only"),
    ("Norfloxacin", "400mg", "Twice daily", "5 days", "Take with plenty of water")
]

LAB_TESTS_LIBRARY = [
    ("Complete Blood Count (CBC)", "blood"),
    ("Blood Sugar (Fasting)", "blood"),
    ("Lipid Profile", "blood"),
    ("Liver Function Test", "blood"),
    ("Kidney Function Test", "blood"),
    ("Thyroid Profile", "blood"),
    ("Urine Routine", "urine"),
    ("Chest X-Ray", "imaging"),
    ("ECG", "diagnostic"),
    ("HbA1c", "blood")
]


def clear_database():
    """Clear all existing data from database"""
    print("\n🗑️  Clearing existing database...")
    
    # Ensure tables exist
    db.create_all()
    
    try:
        # Delete in reverse order of dependencies
        db.session.execute(db.text('DELETE FROM payments'))
        db.session.execute(db.text('DELETE FROM video_meetings'))
        db.session.execute(db.text('DELETE FROM messages'))
        db.session.execute(db.text('DELETE FROM prescriptions'))
        db.session.execute(db.text('DELETE FROM test_reports'))
        db.session.execute(db.text('DELETE FROM lab_tests'))
        db.session.execute(db.text('DELETE FROM visits'))
        db.session.execute(db.text('DELETE FROM appointments'))
        db.session.execute(db.text('DELETE FROM patient_profiles'))
        db.session.execute(db.text('DELETE FROM users'))
        
        db.session.commit()
        print("   ✅ All existing data cleared")
    except Exception as e:
        db.session.rollback()
        print(f"   ⚠️  Error clearing data: {str(e)}")
        print("   ✅ Continuing with fresh database...")


def create_doctors():
    """Create doctor accounts"""
    print("\n👨‍⚕️  Creating doctors...")
    doctors = []
    
    for doc_data in DOCTORS_DATA:
        doctor = User(
            phone_number=doc_data['phone'],
            password_hash=generate_password_hash(doc_data['password']),
            role='doctor',
            full_name=doc_data['name'],
            email=doc_data['email'],
            is_active=True
        )
        db.session.add(doctor)
        doctors.append(doctor)
        print(f"   ✅ {doc_data['name']} - {doc_data['specialization']}")
    
    db.session.commit()
    return doctors


def create_lab_technicians():
    """Create lab technician accounts"""
    print("\n🔬 Creating lab technicians...")
    labs = []
    
    for lab_data in LAB_TECHNICIANS_DATA:
        lab = User(
            phone_number=lab_data['phone'],
            password_hash=generate_password_hash(lab_data['password']),
            role='lab',
            full_name=lab_data['name'],
            email=lab_data['email'],
            is_active=True
        )
        db.session.add(lab)
        labs.append(lab)
        print(f"   ✅ {lab_data['name']}")
    
    db.session.commit()
    return labs


def create_patients():
    """Create patient accounts with profiles"""
    print("\n👥 Creating patients with medical profiles...")
    patients = []
    
    for patient_data in PATIENTS_DATA:
        # Create user account
        user = User(
            phone_number=patient_data['phone'],
            password_hash=generate_password_hash(patient_data['password']),
            role='patient',
            full_name=patient_data['name'],
            email=patient_data['email'],
            is_active=True
        )
        db.session.add(user)
        db.session.flush()  # Get user ID
        
        # Create patient profile
        profile = PatientProfile(
            user_id=user.id,
            age=patient_data['age'],
            gender=patient_data['gender'],
            blood_group=patient_data['blood_group'],
            address=patient_data['address'],
            emergency_contact=patient_data['emergency_contact'],
            allergies=patient_data['allergies'],
            chronic_conditions=patient_data['chronic_conditions'],
            previous_surgeries=patient_data['previous_surgeries']
        )
        db.session.add(profile)
        
        patients.append({'user': user, 'profile': profile})
        print(f"   ✅ {patient_data['name']} - {patient_data['age']}y, {patient_data['blood_group']}")
    
    db.session.commit()
    return patients


def create_past_visits(patients, doctors, labs):
    """Create historical medical visits with complete records"""
    print("\n📋 Creating past medical visits...")
    
    for patient in patients[:5]:  # First 5 patients have medical history
        num_visits = random.randint(2, 5)
        
        for i in range(num_visits):
            # Create visit
            days_ago = random.randint(30, 365)
            visit = Visit(
                patient_profile_id=patient['profile'].id,
                doctor_id=random.choice(doctors).id,
                symptoms=random.choice(SYMPTOMS_LIBRARY),
                diagnosis=random.choice(DIAGNOSES_LIBRARY),
                notes=f"Patient responded well to treatment. Follow-up recommended.",
                severity=random.choice(['low', 'medium', 'high']),
                status='completed',
                visit_date=datetime.now() - timedelta(days=days_ago),
                created_at=datetime.now() - timedelta(days=days_ago),
                completed_at=datetime.now() - timedelta(days=days_ago-7)
            )
            db.session.add(visit)
            db.session.flush()
            
            # Add prescriptions
            num_prescriptions = random.randint(1, 3)
            for _ in range(num_prescriptions):
                med = random.choice(MEDICATIONS_LIBRARY)
                prescription = Prescription(
                    visit_id=visit.id,
                    medication_name=med[0],
                    dosage=med[1],
                    frequency=med[2],
                    duration=med[3],
                    instructions=med[4]
                )
                db.session.add(prescription)
            
            # Add lab tests
            if random.random() > 0.5:  # 50% chance of lab tests
                num_tests = random.randint(1, 3)
                for _ in range(num_tests):
                    test = random.choice(LAB_TESTS_LIBRARY)
                    lab_test = LabTest(
                        visit_id=visit.id,
                        lab_id=random.choice(labs).id,
                        test_name=test[0],
                        test_type=test[1],
                        status='completed',
                        result='Normal range' if random.random() > 0.3 else 'Abnormal - See remarks',
                        remarks='Test completed successfully',
                        scheduled_time=datetime.now() - timedelta(days=days_ago-2)
                    )
                    db.session.add(lab_test)
            
            print(f"   ✅ Visit for {patient['user'].full_name} - {visit.diagnosis}")
    
    db.session.commit()


def create_appointments(patients, doctors):
    """Create past, today's, and future appointments"""
    print("\n📅 Creating appointments...")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    appointments = []
    
    # Past appointments (completed)
    print("\n   Past Appointments:")
    for i in range(5):
        days_ago = random.randint(1, 14)
        apt = Appointment(
            patient_id=random.choice(patients)['user'].id,
            doctor_id=random.choice(doctors).id,
            appointment_date=today - timedelta(days=days_ago, hours=random.randint(9, 16)),
            duration_minutes=30,
            reason=random.choice(SYMPTOMS_LIBRARY),
            notes="Consultation completed. Treatment prescribed.",
            status='completed',
            meeting_status='ended',
            meeting_started_at=today - timedelta(days=days_ago, hours=10),
            meeting_ended_at=today - timedelta(days=days_ago, hours=10, minutes=25)
        )
        db.session.add(apt)
        appointments.append(apt)
        print(f"      ✅ Completed - {apt.appointment_date.strftime('%b %d')}")
    
    # Today's appointments
    print("\n   Today's Appointments:")
    appointment_times = [
        (9, 0),   # 9:00 AM
        (10, 30), # 10:30 AM
        (14, 0),  # 2:00 PM
        (15, 30), # 3:30 PM
        (16, 45)  # 4:45 PM
    ]
    
    for hour, minute in appointment_times:
        apt = Appointment(
            patient_id=random.choice(patients)['user'].id,
            doctor_id=doctors[0].id,  # Assign to Dr. Priya Sharma
            appointment_date=today.replace(hour=hour, minute=minute),
            duration_minutes=30,
            reason=random.choice(SYMPTOMS_LIBRARY),
            status='scheduled',
            meeting_status='not_started'
        )
        db.session.add(apt)
        appointments.append(apt)
        print(f"      ✅ Scheduled - {apt.appointment_date.strftime('%I:%M %p')}")
    
    # Future appointments
    print("\n   Future Appointments:")
    for i in range(8):
        days_ahead = random.randint(1, 30)
        apt = Appointment(
            patient_id=random.choice(patients)['user'].id,
            doctor_id=random.choice(doctors).id,
            appointment_date=today + timedelta(days=days_ahead, hours=random.randint(9, 16)),
            duration_minutes=30,
            reason=random.choice(SYMPTOMS_LIBRARY),
            status='scheduled',
            meeting_status='not_started'
        )
        db.session.add(apt)
        appointments.append(apt)
        print(f"      ✅ Scheduled - {apt.appointment_date.strftime('%b %d, %I:%M %p')}")
    
    db.session.commit()
    return appointments


def print_summary(doctors, labs, patients, appointments):
    """Print summary of seeded data"""
    print("\n" + "=" * 70)
    print("🎉 DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    print(f"\n📊 Summary:")
    print(f"   • Doctors: {len(doctors)}")
    print(f"   • Lab Technicians: {len(labs)}")
    print(f"   • Patients: {len(patients)}")
    print(f"   • Total Appointments: {len(appointments)}")
    print(f"   • Medical Visits: {Visit.query.count()}")
    print(f"   • Lab Tests: {LabTest.query.count()}")
    print(f"   • Prescriptions: {Prescription.query.count()}")
    
    print("\n🔐 Login Credentials:")
    print("\n   Doctors:")
    for doc in DOCTORS_DATA:
        print(f"      📞 Phone: {doc['phone']}")
        print(f"      🔑 Password: {doc['password']}")
        print(f"      👤 Name: {doc['name']}\n")
    
    print("   Patients (Sample):")
    for patient in PATIENTS_DATA[:3]:
        print(f"      📞 Phone: {patient['phone']}")
        print(f"      🔑 Password: {patient['password']}")
        print(f"      👤 Name: {patient['name']}\n")
    
    print("   Lab Technicians:")
    for lab in LAB_TECHNICIANS_DATA:
        print(f"      📞 Phone: {lab['phone']}")
        print(f"      🔑 Password: {lab['password']}")
        print(f"      👤 Name: {lab['name']}\n")
    
    print("=" * 70)
    print("✅ You can now login with any of the above credentials")
    print("🌐 Server: http://127.0.0.1:5000")
    print("=" * 70 + "\n")


def main():
    """Main seeding function"""
    with app.app_context():
        print("\n" + "=" * 70)
        print("🌱 RURAL HEALTHCARE PLATFORM - DATABASE SEEDING")
        print("=" * 70)
        
        # Clear existing data
        clear_database()
        
        # Create users
        doctors = create_doctors()
        labs = create_lab_technicians()
        patients = create_patients()
        
        # Create medical records
        create_past_visits(patients, doctors, labs)
        
        # Create appointments
        appointments = create_appointments(patients, doctors)
        
        # Print summary
        print_summary(doctors, labs, patients, appointments)


if __name__ == '__main__':
    main()
