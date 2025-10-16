"""
Payment handler for Paynow integration using official Paynow SDK
Handles payment initialization, confirmation, and status checking
"""

import os
from datetime import datetime, timedelta, timezone
from models import db, User, PendingPayment, Transaction, SubscriptionPlan
from paynow import Paynow

class PaynowHandler:
    def __init__(self):
        self.integration_id = os.getenv('PAYNOW_INTEGRATION_ID', '22233')
        self.integration_key = os.getenv('PAYNOW_INTEGRATION_KEY', '5edbeab4-3c75-4132-9785-a81b3fde4bde')
        
        # Auto-detect hosting environment and build correct URLs
        self.base_url = self._get_base_url()
        self.return_url = f"{self.base_url}/payment/return"
        self.result_url = f"{self.base_url}/payment/notify"
        
        # Log the detected URLs for debugging
        print(f"🌐 Paynow Handler initialized:")
        print(f"   Base URL: {self.base_url}")
        print(f"   Return URL: {self.return_url}")
        print(f"   Result URL: {self.result_url}")
        
        # Initialize Paynow SDK
        self.paynow = Paynow(
            self.integration_id,
            self.integration_key,
            self.return_url,
            self.result_url
        )
    
    def _get_base_url(self):
        """
        Auto-detect the base URL based on hosting environment
        Supports: Render, Heroku, Railway, Vercel, and local development
        """
        # 1. Check for explicitly set BASE_URL in environment
        if os.getenv('BASE_URL'):
            return os.getenv('BASE_URL').rstrip('/')
        
        # 2. Check for Render
        if os.getenv('RENDER'):
            render_service = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('RENDER_SERVICE_NAME')
            if render_service:
                if render_service.startswith('http'):
                    return render_service.rstrip('/')
                else:
                    return f"https://{render_service}.onrender.com"
        
        # 3. Check for Heroku
        if os.getenv('DYNO'):
            app_name = os.getenv('HEROKU_APP_NAME')
            if app_name:
                return f"https://{app_name}.herokuapp.com"
        
        # 4. Check for Railway
        if os.getenv('RAILWAY_STATIC_URL'):
            return os.getenv('RAILWAY_STATIC_URL').rstrip('/')
        
        # 5. Check for production environment variable
        if os.getenv('FLASK_ENV') == 'production' and os.getenv('PRODUCTION_URL'):
            return os.getenv('PRODUCTION_URL').rstrip('/')
        
        # 6. Default to localhost for development
        return 'http://localhost:5000'
        
    def create_payment(self, user, plan, reference):
        """
        Create a new payment request using Paynow SDK
        Returns: dict with payment_url and poll_url or None if failed
        """
        try:
            # Create payment using Paynow SDK
            payment = self.paynow.create_payment(reference, user.email)
            
            # Add item to payment
            payment.add(f"{plan.name} Subscription", plan.price)
            
            # Send payment request to Paynow
            if os.getenv('FLASK_ENV') == 'production':
                # Production: Send to real Paynow
                response = self.paynow.send(payment)
            else:
                # Development: Use mock gateway
                return {
                    'success': True,
                    'payment_url': f'http://localhost:5000/payment/mock?ref={reference}',
                    'poll_url': f'http://localhost:5000/payment/poll?ref={reference}'
                }
            
            # Check if payment initiation was successful
            if response.success:
                return {
                    'success': True,
                    'payment_url': response.redirect_url,  # URL to redirect user to
                    'poll_url': response.poll_url  # URL to check payment status
                }
            else:
                return {
                    'success': False,
                    'error': response.errors if hasattr(response, 'errors') else 'Payment initiation failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, reference, status, paynow_reference=None, hash_value=None):
        """
        Verify and process a payment notification from Paynow
        Returns: True if payment was processed successfully
        """
        try:
            # Find pending payment
            pending = PendingPayment.query.filter_by(payment_reference=reference).first()
            
            if not pending:
                return False
            
            # In production, verify the hash
            if os.getenv('FLASK_ENV') == 'production' and hash_value:
                # TODO: Verify hash matches
                pass
            
            # Update pending payment
            pending.status = status.lower()
            pending.paynow_reference = paynow_reference
            pending.updated_at = datetime.now(timezone.utc)
            
            # If payment is confirmed
            if status.lower() in ['paid', 'delivered', 'sent']:
                return self._activate_subscription(pending)
            
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error verifying payment: {e}")
            db.session.rollback()
            return False
    
    def _activate_subscription(self, pending_payment):
        """Activate user subscription after successful payment"""
        try:
            user = User.query.get(pending_payment.user_id)
            plan = SubscriptionPlan.query.get(pending_payment.plan_id)
            
            if not user or not plan:
                return False
            
            # Calculate subscription dates
            start_date = datetime.now(timezone.utc)
            end_date = start_date + timedelta(days=plan.duration_days)
            
            # Update user subscription
            user.is_subscriber = True
            user.subscription_date = start_date
            user.subscription_end_date = end_date
            
            # Create transaction record
            transaction = Transaction(
                user_id=user.id,
                amount=pending_payment.amount,
                currency=pending_payment.currency,
                reference=pending_payment.payment_reference,
                paynow_reference=pending_payment.paynow_reference,
                status='completed',
                payment_method='paynow',
                plan_id=plan.id,
                subscription_start=start_date,
                subscription_end=end_date,
                notes=f'Subscription activated: {plan.name}'
            )
            
            # Update pending payment status
            pending_payment.status = 'completed'
            
            # Save everything
            db.session.add(transaction)
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error activating subscription: {e}")
            db.session.rollback()
            return False
    
    def check_payment_status(self, poll_url):
        """
        Check payment status using poll URL with Paynow SDK
        Returns: dict with status information
        """
        try:
            if os.getenv('FLASK_ENV') == 'production':
                # Production: Check status with Paynow SDK
                status = self.paynow.check_transaction_status(poll_url)
                
                if status.paid:
                    return {
                        'status': 'Paid',
                        'reference': status.reference,
                        'amount': str(status.amount) if hasattr(status, 'amount') else '0.00',
                        'paynowreference': status.paynow_reference
                    }
                else:
                    return {
                        'status': status.status,
                        'reference': status.reference
                    }
            else:
                # Development mode - return mock status
                return {
                    'status': 'Paid',
                    'reference': 'TEST-REF',
                    'amount': '5.00',
                    'paynowreference': 'PAYNOW-12345'
                }
        except Exception as e:
            return {
                'status': 'Error',
                'error': str(e)
            }

# Global payment handler instance
payment_handler = PaynowHandler()
