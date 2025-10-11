"""
Script to apply the subscription_end_date migration to the database.
Run this after updating the models.
"""
from app import app, db
from models import User
from datetime import datetime
from dateutil.relativedelta import relativedelta

def apply_migration():
    with app.app_context():
        # Check if column exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        if 'subscription_end_date' not in columns:
            print("Adding subscription_end_date column...")
            # Add the column using raw SQL (quote "user" since it's a reserved keyword in PostgreSQL)
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE "user" ADD COLUMN subscription_end_date TIMESTAMP'))
                conn.commit()
            print("✓ Column added successfully!")
        else:
            print("✓ Column already exists!")
        
        # Update existing subscribers with end dates
        print("\nUpdating existing subscribers...")
        subscribers = User.query.filter_by(is_subscriber=True).all()
        
        for user in subscribers:
            if not user.subscription_end_date and user.subscription_date:
                # Set end date to 1 month from subscription date
                user.subscription_end_date = user.subscription_date + relativedelta(months=1)
                print(f"  - Updated {user.username}: end date set to {user.subscription_end_date.strftime('%Y-%m-%d')}")
        
        db.session.commit()
        print(f"\n✓ Updated {len(subscribers)} subscribers!")
        
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Test the subscription cancellation flow")
        print("2. Verify users can continue using the platform after cancellation")
        print("3. Check that free tier limits work correctly")

if __name__ == '__main__':
    apply_migration()
