#!/usr/bin/env python
"""Initialize subscription plans in the database"""

from app import app, db
from models import SubscriptionPlan

def init_plans():
    with app.app_context():
        # Check if plans already exist
        existing_plans = SubscriptionPlan.query.count()
        
        if existing_plans > 0:
            print(f'Subscription plans already exist ({existing_plans} plans found)')
            return
        
        # Create single monthly subscription plan
        plans = [
            {
                'name': 'Premium Monthly',
                'duration_days': 30,
                'price': 5.00,
                'currency': 'USD',
                'description': 'Monthly subscription - unlimited access to all driving theory tests',
                'is_active': True
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
