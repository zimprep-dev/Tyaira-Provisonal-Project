#!/usr/bin/env python
"""Initialize subscription plans in the database"""

from app import app, db
from models import SubscriptionPlan

def init_plans():
    with app.app_context():
        try:
            # Check if plans already exist
            existing_plans = SubscriptionPlan.query.count()
            
            if existing_plans > 0:
                print(f'Subscription plans already exist ({existing_plans} plans found)')
                return
        except Exception as e:
            # If query fails, it means migrations haven't run yet
            print(f'⚠️  Could not check existing plans (migrations may not be complete): {e}')
            print('Skipping plan initialization...')
            return
        
        # Create single monthly subscription plan with all required fields
        plans = [
            {
                'name': 'Premium Monthly',
                'plan_type': 'subscription',
                'duration_days': 30,
                'duration_months': 1,
                'price': 5.00,
                'currency': 'USD',
                'description': 'Monthly subscription - unlimited access to all driving theory tests',
                'has_unlimited_tests': True,
                'test_credits': 0,
                'max_tests_per_month': None,
                'has_download_access': True,
                'has_progress_tracking': True,
                'has_performance_analytics': True,
                'is_active': True,
                'is_featured': False
            }
        ]
        
        # Add plans to database
        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
        
        db.session.commit()
        print(f'Successfully created {len(plans)} subscription plans!')
        
        # Display created plans
        print('\nCreated Plans:')
        for plan in SubscriptionPlan.query.all():
            print(f'  - {plan.name}: ${plan.price:.2f} ({plan.duration_days} days)')

if __name__ == '__main__':
    init_plans()
