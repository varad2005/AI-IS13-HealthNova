"""
Admin utility script for common administrative tasks
Use this for testing and development only
"""

from app import create_app
from models import db, User, Visit, PatientProfile
from sqlalchemy import func

def list_users():
    """List all users by role"""
    app = create_app('development')
    with app.app_context():
        print("\n" + "=" * 60)
        print("REGISTERED USERS")
        print("=" * 60)
        
        for role in ['patient', 'doctor', 'lab']:
            users = User.query.filter_by(role=role).all()
            print(f"\n{role.upper()}S ({len(users)}):")
            for user in users:
                print(f"  ID: {user.id} | {user.full_name} | {user.phone_number}")


def list_visits():
    """List all visits with their status"""
    app = create_app('development')
    with app.app_context():
        print("\n" + "=" * 60)
        print("ALL VISITS")
        print("=" * 60)
        
        visits = Visit.query.order_by(Visit.created_at.desc()).all()
        
        if not visits:
            print("\nNo visits found.")
            return
        
        for visit in visits:
            patient = visit.patient_profile.user
            doctor = visit.doctor.full_name if visit.doctor else "Unassigned"
            print(f"\nVisit ID: {visit.id}")
            print(f"  Patient: {patient.full_name} (ID: {patient.id})")
            print(f"  Doctor: {doctor}")
            print(f"  Status: {visit.status}")
            print(f"  Symptoms: {visit.symptoms[:50]}...")
            print(f"  Created: {visit.created_at.strftime('%Y-%m-%d %H:%M')}")


def assign_visit_to_doctor(visit_id, doctor_id):
    """Assign a visit to a doctor"""
    app = create_app('development')
    with app.app_context():
        visit = Visit.query.get(visit_id)
        if not visit:
            print(f"✗ Visit {visit_id} not found")
            return
        
        doctor = User.query.filter_by(id=doctor_id, role='doctor').first()
        if not doctor:
            print(f"✗ Doctor {doctor_id} not found")
            return
        
        visit.doctor_id = doctor_id
        db.session.commit()
        
        print(f"✓ Visit {visit_id} assigned to Dr. {doctor.full_name}")


def unassign_visit(visit_id):
    """Remove doctor assignment from a visit"""
    app = create_app('development')
    with app.app_context():
        visit = Visit.query.get(visit_id)
        if not visit:
            print(f"✗ Visit {visit_id} not found")
            return
        
        visit.doctor_id = None
        db.session.commit()
        
        print(f"✓ Visit {visit_id} unassigned")


def delete_all_data():
    """Delete all data from database (DANGEROUS - use for testing only)"""
    app = create_app('development')
    with app.app_context():
        confirm = input("⚠ This will delete ALL data. Type 'DELETE' to confirm: ")
        if confirm != 'DELETE':
            print("Aborted.")
            return
        
        print("\nDeleting all data...")
        
        # Delete in correct order due to foreign keys
        from models import Message, Prescription, TestReport, LabTest, Visit, PatientProfile, User
        
        Message.query.delete()
        Prescription.query.delete()
        TestReport.query.delete()
        LabTest.query.delete()
        Visit.query.delete()
        PatientProfile.query.delete()
        User.query.delete()
        
        db.session.commit()
        
        print("✓ All data deleted")


def show_stats():
    """Show database statistics"""
    app = create_app('development')
    with app.app_context():
        print("\n" + "=" * 60)
        print("DATABASE STATISTICS")
        print("=" * 60)
        
        stats = {
            'Total Users': User.query.count(),
            'Patients': User.query.filter_by(role='patient').count(),
            'Doctors': User.query.filter_by(role='doctor').count(),
            'Labs': User.query.filter_by(role='lab').count(),
            'Total Visits': Visit.query.count(),
            'Pending Visits': Visit.query.filter_by(status='pending').count(),
            'In Progress Visits': Visit.query.filter_by(status='in_progress').count(),
            'Completed Visits': Visit.query.filter_by(status='completed').count(),
            'Lab Tests': db.session.query(func.count()).select_from(db.session.query(db.select(db.text('1')).select_from(db.text('lab_tests'))).subquery()).scalar() or 0
        }
        
        for key, value in stats.items():
            print(f"  {key}: {value}")


def interactive_menu():
    """Interactive menu for admin tasks"""
    while True:
        print("\n" + "=" * 60)
        print("ADMIN UTILITY - Rural Healthcare Platform")
        print("=" * 60)
        print("\n1. List all users")
        print("2. List all visits")
        print("3. Assign visit to doctor")
        print("4. Unassign visit")
        print("5. Show statistics")
        print("6. Delete all data (DANGEROUS)")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            list_users()
        
        elif choice == '2':
            list_visits()
        
        elif choice == '3':
            list_visits()
            visit_id = int(input("\nEnter Visit ID: "))
            list_users()
            doctor_id = int(input("\nEnter Doctor ID: "))
            assign_visit_to_doctor(visit_id, doctor_id)
        
        elif choice == '4':
            list_visits()
            visit_id = int(input("\nEnter Visit ID to unassign: "))
            unassign_visit(visit_id)
        
        elif choice == '5':
            show_stats()
        
        elif choice == '6':
            delete_all_data()
        
        elif choice == '0':
            print("\nGoodbye!")
            break
        
        else:
            print("\n✗ Invalid choice")


if __name__ == "__main__":
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
