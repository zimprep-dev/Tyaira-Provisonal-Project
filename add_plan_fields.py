"""
Add duration_months, is_featured, and subscribers relationship to SubscriptionPlan
Add subscription_plan_id to User
Run this script to update existing database
"""

from app import app, db
from sqlalchemy import text

def add_plan_fields():
    with app.app_context():
        try:
            # Add duration_months to subscription_plan
            print("Adding 'duration_months' column to subscription_plan table...")
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS duration_months INTEGER DEFAULT 1 NOT NULL"
            ))
            
            # Add is_featured to subscription_plan
            print("Adding 'is_featured' column to subscription_plan table...")
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE"
            ))
            
            # Add subscription_plan_id to user
            print("Adding 'subscription_plan_id' column to user table...")
            db.session.execute(text(
                "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS subscription_plan_id INTEGER"
            ))
            
            # Set duration_months based on duration_days for existing plans
            print("Updating duration_months values...")
            db.session.execute(text(
                """
                UPDATE subscription_plan 
                SET duration_months = 
                    CASE 
                        WHEN duration_days <= 31 THEN 1
                        WHEN duration_days <= 93 THEN 3
                        WHEN duration_days <= 186 THEN 6
                        ELSE 12
                    END
                WHERE duration_months IS NULL OR duration_months = 0
                """
            ))
            
            db.session.commit()
            print("✅ Successfully added all fields")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_plan_fields()
