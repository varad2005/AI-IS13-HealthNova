"""
Add test doctors to database for booking functionality
"""
from app import create_app
from models import db, User

# Create app and push context
app, socketio = create_app('development')

with app.app_context():
    # Check if doctors already exist
    existing_doctors = User.query.filter_by(role='doctor').all()
    
    if len(existing_doctors) >= 3:
        print(f"\n✅ Database already has {len(existing_doctors)} doctors:")
        for doc in existing_doctors:
            print(f"   - {doc.full_name} ({doc.phone_number})")
        print("\nNo need to add more doctors.")
    else:
        print("\n📋 Adding test doctors to database...")
        
        # Test doctors to add
        test_doctors = [
            {
                'phone_number': '9876543210',
                'full_name': 'Dr. Priya Sharma',
                'email': 'priya.sharma@healthnova.com',
                'password': 'doctor123'
            },
            {
                'phone_number': '9876543211',
                'full_name': 'Dr. Rajesh Kumar',
                'email': 'rajesh.kumar@healthnova.com',
                'password': 'doctor123'
            },
            {
                'phone_number': '9876543212',
                'full_name': 'Dr. Anjali Verma',
                'email': 'anjali.verma@healthnova.com',
                'password': 'doctor123'
            },
            {
                'phone_number': '9876543213',
                'full_name': 'Dr. Suresh Patel',
                'email': 'suresh.patel@healthnova.com',
                'password': 'doctor123'
            },
            {
                'phone_number': '9876543214',
                'full_name': 'Dr. Kavita Singh',
                'email': 'kavita.singh@healthnova.com',
                'password': 'doctor123'
            }
        ]
        
        added_count = 0
        
        for doc_data in test_doctors:
            # Check if doctor already exists
            existing = User.query.filter_by(phone_number=doc_data['phone_number']).first()
            
            if existing:
                print(f"⏭️  Doctor {doc_data['full_name']} already exists")
                continue
            
            # Create new doctor
            doctor = User(
                phone_number=doc_data['phone_number'],
                full_name=doc_data['full_name'],
                email=doc_data['email'],
                role='doctor',
                is_active=True
            )
            doctor.set_password(doc_data['password'])
            
            db.session.add(doctor)
            added_count += 1
            print(f"✅ Added: {doc_data['full_name']} (Phone: {doc_data['phone_number']})")
        
        if added_count > 0:
            db.session.commit()
            print(f"\n✅ Successfully added {added_count} doctors to database!")
            print("\n📋 Test Doctor Credentials:")
            print("   Phone: 9876543210, Password: doctor123 (Dr. Priya Sharma)")
            print("   Phone: 9876543211, Password: doctor123 (Dr. Rajesh Kumar)")
            print("   Phone: 9876543212, Password: doctor123 (Dr. Anjali Verma)")
            print("   Phone: 9876543213, Password: doctor123 (Dr. Suresh Patel)")
            print("   Phone: 9876543214, Password: doctor123 (Dr. Kavita Singh)")
        else:
            print("\n✅ All doctors already exist in database!")

print("\n" + "="*60)
print("Database ready for appointment booking!")
print("="*60)
