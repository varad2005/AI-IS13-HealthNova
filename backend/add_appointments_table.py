"""
Database Migration Script - Add Appointments Table

WHAT THIS SCRIPT DOES:
1. Creates the 'appointments' table with all required fields
2. Includes meeting_status for doctor-controlled video consultations
3. Adds foreign key relationships to users table
4. Creates indexes for performance

WHEN TO RUN:
- Run this ONCE after updating models.py
- Required before video consultation features will work
- Safe to run multiple times (checks if table exists)

HOW TO RUN:
    python add_appointments_table.py

MEETING STATUS VALUES:
- "not_started" (default): Patient cannot join yet
- "live": Doctor started meeting, both can join
- "ended": Meeting finished, no one can join
"""

from app import create_app, db
from models import Appointment
from sqlalchemy import inspect

def table_exists(table_name):
    """Check if a table already exists in the database"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def add_appointments_table():
    """Create the appointments table if it doesn't exist"""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Check if table already exists
            if table_exists('appointments'):
                print("✓ 'appointments' table already exists")
                print("  No migration needed")
                return
            
            print("Creating 'appointments' table...")
            
            # Create the appointments table
            db.create_all()
            
            print("✓ 'appointments' table created successfully!")
            print("\nTable Structure:")
            print("  - id: Primary key")
            print("  - patient_id: Foreign key to users table")
            print("  - doctor_id: Foreign key to users table")
            print("  - appointment_date: When consultation is scheduled")
            print("  - duration_minutes: Length of consultation (default: 30)")
            print("  - reason: Reason for consultation")
            print("  - notes: Doctor's notes after consultation")
            print("  - status: scheduled/completed/cancelled/no_show")
            print("  - meeting_status: not_started/live/ended (CRITICAL for video)")
            print("  - meeting_started_at: When doctor started meeting")
            print("  - meeting_ended_at: When doctor ended meeting")
            print("  - created_at: Record creation timestamp")
            print("  - updated_at: Last update timestamp")
            
            print("\n✓ Migration completed successfully!")
            print("\nNEXT STEPS:")
            print("1. Restart your Flask server")
            print("2. Test appointment creation: POST /video/create-appointment")
            print("3. Test meeting start: POST /video/start-meeting/<appointment_id>")
            print("4. Test meeting status: GET /video/meeting-status/<appointment_id>")
            
        except Exception as e:
            print(f"✗ Error creating appointments table: {str(e)}")
            print("\nTROUBLESHOOTING:")
            print("1. Make sure backend/models.py has the Appointment class")
            print("2. Check database connection in config.py")
            print("3. Ensure no syntax errors in models.py")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE MIGRATION: Add Appointments Table")
    print("=" * 60)
    print()
    
    add_appointments_table()
    
    print()
    print("=" * 60)
