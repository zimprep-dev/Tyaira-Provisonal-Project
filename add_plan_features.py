"""
Add access control features to SubscriptionPlan model
Run this script to update existing database
"""

from app import app, db
from sqlalchemy import text

def add_plan_features():
    with app.app_context():
        try:
            # Add plan_type column
            print("Adding 'plan_type' column...")
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS plan_type VARCHAR(20) DEFAULT 'subscription'"
            ))
            
            # Add access control columns
            print("Adding access control columns...")
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_unlimited_tests BOOLEAN DEFAULT TRUE"
            ))
            
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS test_credits INTEGER DEFAULT 0"
            ))
            
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS max_tests_per_month INTEGER"
            ))
            
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_download_access BOOLEAN DEFAULT TRUE"
            ))
            
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_progress_tracking BOOLEAN DEFAULT TRUE"
            ))
            
            db.session.execute(text(
                "ALTER TABLE subscription_plan ADD COLUMN IF NOT EXISTS has_performance_analytics BOOLEAN DEFAULT TRUE"
            ))
            
            db.session.commit()
            print("✅ Successfully added all plan feature columns")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    add_plan_features()
