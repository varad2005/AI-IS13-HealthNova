"""
Database migration script to add Digital Patient History fields to Visit model
Run this after updating the models.py file

Usage:
    python migrations/add_visit_fields.py
"""

from app import create_app, db
from models import Visit
from sqlalchemy import text

def upgrade():
    """Add new fields to visits table"""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Add new columns if they don't exist
            with db.engine.connect() as conn:
                # Check if columns exist
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='visits'
                """))
                existing_columns = [row[0] for row in result]
                
                # Add ai_summary if it doesn't exist
                if 'ai_summary' not in existing_columns:
                    conn.execute(text("ALTER TABLE visits ADD COLUMN ai_summary TEXT"))
                    print("✓ Added ai_summary column")
                
                # Add severity if it doesn't exist
                if 'severity' not in existing_columns:
                    conn.execute(text("ALTER TABLE visits ADD COLUMN severity VARCHAR(20)"))
                    print("✓ Added severity column")
                
                # Add visit_date if it doesn't exist
                if 'visit_date' not in existing_columns:
                    conn.execute(text("ALTER TABLE visits ADD COLUMN visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                    print("✓ Added visit_date column")
                
                # Update status column values from 'pending' to 'open'
                conn.execute(text("UPDATE visits SET status = 'open' WHERE status = 'pending'"))
                print("✓ Updated status values from 'pending' to 'open'")
                
                conn.commit()
            
            print("\n✓ Migration completed successfully!")
            print("\nNew fields added:")
            print("  - ai_summary: TEXT (optional AI-generated summary)")
            print("  - severity: VARCHAR(20) (low, medium, high, critical)")
            print("  - visit_date: TIMESTAMP (actual visit date)")
            
        except Exception as e:
            print(f"\n✗ Migration failed: {str(e)}")
            db.session.rollback()

def downgrade():
    """Remove added fields (for rollback)"""
    app = create_app('development')
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE visits DROP COLUMN IF EXISTS ai_summary"))
                conn.execute(text("ALTER TABLE visits DROP COLUMN IF EXISTS severity"))
                conn.execute(text("ALTER TABLE visits DROP COLUMN IF EXISTS visit_date"))
                conn.commit()
            
            print("✓ Rollback completed successfully!")
            
        except Exception as e:
            print(f"✗ Rollback failed: {str(e)}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
