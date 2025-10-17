"""
Add created_at column to User model
Run this script to update existing database
"""

from app import app, db
from models import User
from datetime import datetime, timezone
from sqlalchemy import text

def add_created_at_column():
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='user' AND column_name='created_at'"
            ))
            
            if result.fetchone():
                print("✅ Column 'created_at' already exists")
                return
            
            # Add the column
            print("Adding 'created_at' column to User table...")
            db.session.execute(text(
                "ALTER TABLE \"user\" ADD COLUMN created_at TIMESTAMP"
            ))
            
            # Set default value for existing users
            print("Setting default created_at for existing users...")
            default_date = datetime.now(timezone.utc)
            db.session.execute(text(
                f"UPDATE \"user\" SET created_at = :date WHERE created_at IS NULL"
            ), {'date': default_date})
            
            db.session.commit()
            print("✅ Successfully added 'created_at' column")
            print(f"✅ Set default date for existing users: {default_date}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_created_at_column()
