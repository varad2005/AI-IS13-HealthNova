"""
Quick test script to create database tables and test basic functionality
Run this after installing dependencies to verify setup
"""

from app import create_app
from models import db, User, PatientProfile

def initialize_database():
    """Create all database tables"""
    app, socketio = create_app('development')
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # Verify tables exist
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n✓ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        return app

def create_test_users(app):
    """Create sample users for testing (optional)"""
    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("\n⚠ Users already exist. Skipping test user creation.")
            return
        
        print("\nCreating test users...")
        
        # Create test patient
        patient_user = User(
            phone_number="1111111111",
            role="patient",
            full_name="Test Patient",
            email="patient@test.com"
        )
        patient_user.set_password("test123")
        db.session.add(patient_user)
        db.session.flush()
        
        # Create patient profile
        patient_profile = PatientProfile(
            user_id=patient_user.id,
            age=30,
            gender="male",
            blood_group="O+"
        )
        db.session.add(patient_profile)
        
        # Create test doctor
        doctor_user = User(
            phone_number="2222222222",
            role="doctor",
            full_name="Dr. Test Doctor",
            email="doctor@test.com"
        )
        doctor_user.set_password("test123")
        db.session.add(doctor_user)
        
        # Create test lab
        lab_user = User(
            phone_number="3333333333",
            role="lab",
            full_name="Test Lab Center",
            email="lab@test.com"
        )
        lab_user.set_password("test123")
        db.session.add(lab_user)
        
        db.session.commit()
        
        print("✓ Test users created successfully!")
        print("\nTest Credentials:")
        print("  Patient: 1111111111 / test123")
        print("  Doctor:  2222222222 / test123")
        print("  Lab:     3333333333 / test123")

if __name__ == "__main__":
    print("=" * 60)
    print("Rural Healthcare Platform - Database Setup")
    print("=" * 60)
    
    try:
        app = initialize_database()
        
        # Ask if user wants to create test users
        response = input("\nCreate test users for development? (y/n): ").lower()
        if response == 'y':
            create_test_users(app)
        
        print("\n" + "=" * 60)
        print("✓ Setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. API will be available at: http://localhost:5000")
        print("3. Check README.md for API documentation")
        
    except Exception as e:
        print(f"\n✗ Error during setup: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running")
        print("2. Check database credentials in .env file")
        print("3. Verify database 'rural_health' exists")
