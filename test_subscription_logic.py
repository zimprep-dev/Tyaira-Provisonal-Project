"""
Test script to verify subscription logic works correctly
"""
from app import app, db
from models import User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def test_subscription_logic():
    with app.app_context():
        print("🧪 Testing Subscription Logic\n")
        print("=" * 60)
        
        # Test 1: Active Subscriber
        print("\n✅ Test 1: Active Subscriber")
        user1 = User(
            username='test_active',
            email='active@test.com',
            password_hash='test',
            is_subscriber=True,
            subscription_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + relativedelta(months=1)
        )
        print(f"   is_subscriber: {user1.is_subscriber}")
        print(f"   subscription_end_date: {user1.subscription_end_date}")
        print(f"   has_active_subscription(): {user1.has_active_subscription()}")
        assert user1.has_active_subscription() == True, "Active subscriber should have access"
        print("   ✓ PASSED")
        
        # Test 2: Cancelled Subscription (Grace Period)
        print("\n✅ Test 2: Cancelled Subscription (Grace Period)")
        user2 = User(
            username='test_cancelled',
            email='cancelled@test.com',
            password_hash='test',
            is_subscriber=False,
            subscription_date=datetime.utcnow() - timedelta(days=15),
            subscription_end_date=datetime.utcnow() + timedelta(days=15)
        )
        print(f"   is_subscriber: {user2.is_subscriber}")
        print(f"   subscription_end_date: {user2.subscription_end_date}")
        print(f"   has_active_subscription(): {user2.has_active_subscription()}")
        assert user2.has_active_subscription() == True, "Cancelled user in grace period should have access"
        print("   ✓ PASSED")
        
        # Test 3: Expired Subscription
        print("\n✅ Test 3: Expired Subscription")
        user3 = User(
            username='test_expired',
            email='expired@test.com',
            password_hash='test',
            is_subscriber=False,
            subscription_date=datetime.utcnow() - timedelta(days=60),
            subscription_end_date=datetime.utcnow() - timedelta(days=30)
        )
        print(f"   is_subscriber: {user3.is_subscriber}")
        print(f"   subscription_end_date: {user3.subscription_end_date}")
        print(f"   has_active_subscription(): {user3.has_active_subscription()}")
        assert user3.has_active_subscription() == False, "Expired subscription should not have access"
        print("   ✓ PASSED")
        
        # Test 4: Never Subscribed
        print("\n✅ Test 4: Never Subscribed")
        user4 = User(
            username='test_free',
            email='free@test.com',
            password_hash='test',
            is_subscriber=False,
            subscription_date=None,
            subscription_end_date=None
        )
        print(f"   is_subscriber: {user4.is_subscriber}")
        print(f"   subscription_end_date: {user4.subscription_end_date}")
        print(f"   has_active_subscription(): {user4.has_active_subscription()}")
        assert user4.has_active_subscription() == False, "Free user should not have premium access"
        print("   ✓ PASSED")
        
        # Test 5: Edge Case - End Date Today
        print("\n✅ Test 5: Edge Case - Subscription Ends Today")
        user5 = User(
            username='test_today',
            email='today@test.com',
            password_hash='test',
            is_subscriber=False,
            subscription_date=datetime.utcnow() - timedelta(days=30),
            subscription_end_date=datetime.utcnow() + timedelta(hours=1)
        )
        print(f"   is_subscriber: {user5.is_subscriber}")
        print(f"   subscription_end_date: {user5.subscription_end_date}")
        print(f"   has_active_subscription(): {user5.has_active_subscription()}")
        assert user5.has_active_subscription() == True, "User should have access until end of day"
        print("   ✓ PASSED")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("\nSubscription logic is working correctly:")
        print("  • Active subscribers have unlimited access")
        print("  • Cancelled users retain access during grace period")
        print("  • Expired subscriptions return to free tier")
        print("  • Free users have limited access")

if __name__ == '__main__':
    test_subscription_logic()
