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
        
        # Create default subscription plans
        plans = [
            {
                'name': '1 Month Premium',
                'duration_days': 30,
                'price': 5.00,
                'currency': 'USD',
                'description': 'One month of unlimited access to all driving theory tests',
                'is_active': True
            },
            {
                'name': '3 Months Premium',
                'duration_days': 90,
                'price': 12.00,
                'currency': 'USD',
                'description': 'Three months of unlimited access - Save 20%!',
                'is_active': True
            },
            {
                'name': '6 Months Premium',
                'duration_days': 180,
                'price': 20.00,
                'currency': 'USD',
                'description': 'Six months of unlimited access - Save 33%!',
                'is_active': True
            },
            {
                'name': '1 Year Premium',
                'duration_days': 365,
                'price': 35.00,
                'currency': 'USD',
                'description': 'One full year of unlimited access - Best value, save 42%!',
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
