"""
Link existing subscribers to their subscription plans
Run this to properly associate users with their plans
"""

from app import app, db
from models import User, SubscriptionPlan

def link_subscribers():
    with app.app_context():
        try:
            # Find the $5 plan (Premium Monthly or similar)
            five_dollar_plan = SubscriptionPlan.query.filter_by(price=5.0).first()
            
            if not five_dollar_plan:
                print("❌ No $5 plan found. Creating one...")
                # Create a default Premium Monthly plan if it doesn't exist
                five_dollar_plan = SubscriptionPlan(
                    name="Premium Monthly",
                    plan_type="subscription",
                    duration_days=30,
                    duration_months=1,
                    price=5.0,
                    currency="USD",
                    description="Monthly premium subscription",
                    has_unlimited_tests=True,
                    has_download_access=True,
                    has_progress_tracking=True,
                    has_performance_analytics=True,
                    is_active=True
                )
                db.session.add(five_dollar_plan)
                db.session.commit()
                print(f"✅ Created Premium Monthly plan (ID: {five_dollar_plan.id})")
            else:
                print(f"✅ Found plan: {five_dollar_plan.name} (ID: {five_dollar_plan.id}, Price: ${five_dollar_plan.price})")
            
            # Find all active subscribers without a plan_id
            unlinked_subscribers = User.query.filter_by(
                is_subscriber=True,
                subscription_plan_id=None
            ).all()
            
            if not unlinked_subscribers:
                print("ℹ️  No unlinked subscribers found")
                return
            
            print(f"\n🔗 Linking {len(unlinked_subscribers)} subscriber(s) to {five_dollar_plan.name}...")
            
            for user in unlinked_subscribers:
                user.subscription_plan_id = five_dollar_plan.id
                print(f"   - Linked user: {user.username}")
            
            db.session.commit()
            print(f"\n✅ Successfully linked {len(unlinked_subscribers)} subscriber(s)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()

if __name__ == '__main__':
    link_subscribers()
