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
        
        # Determine if we should use real Paynow or mock
        # Use real Paynow on Vercel/when BASE_URL is set, otherwise use mock for localhost
        self.is_production = bool(os.getenv('VERCEL')) or bool(os.getenv('BASE_URL'))
        
        # Log the detected URLs for debugging
        print(f"🌐 Paynow Handler initialized:")
        print(f"   Base URL: {self.base_url}")
        print(f"   Return URL: {self.return_url}")
        print(f"   Result URL: {self.result_url}")
        print(f"   Production Mode: {self.is_production}")
        print(f"   Integration ID: {self.integration_id}")
        
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
        base_url = os.getenv('BASE_URL')
        if base_url:
            url = base_url.rstrip('/')
            # Ensure URL has protocol (http:// or https://)
            if not url.startswith('http://') and not url.startswith('https://'):
                url = f"https://{url}"
            print(f"📍 Using BASE_URL from environment: {url}")
            return url
        
        # 2. Check for Render
        if os.getenv('RENDER'):
            render_service = os.getenv('RENDER_EXTERNAL_URL') or os.getenv('RENDER_SERVICE_NAME')
            if render_service:
                if render_service.startswith('http'):
                    url = render_service.rstrip('/')
                else:
                    url = f"https://{render_service}.onrender.com"
                print(f"📍 Using Render URL: {url}")
                return url
        
        # 3. Check for Heroku
        if os.getenv('DYNO'):
            app_name = os.getenv('HEROKU_APP_NAME')
            if app_name:
                url = f"https://{app_name}.herokuapp.com"
                print(f"📍 Using Heroku URL: {url}")
                return url
        
        # 4. Check for Railway
        railway_url = os.getenv('RAILWAY_STATIC_URL')
        if railway_url:
            url = railway_url.rstrip('/')
            print(f"📍 Using Railway URL: {url}")
            return url
        
        # 5. Check for Vercel
        vercel_url = os.getenv('VERCEL_URL')
        if vercel_url:
            # VERCEL_URL doesn't include protocol, so add it
            url = f"https://{vercel_url}"
            print(f"📍 Using Vercel URL: {url}")
            return url
        
        # 6. Check for production environment variable
        if os.getenv('FLASK_ENV') == 'production':
            prod_url = os.getenv('PRODUCTION_URL')
            if prod_url:
                url = prod_url.rstrip('/')
                print(f"📍 Using PRODUCTION_URL: {url}")
                return url
        
        # 7. Default to localhost for development
        url = 'http://localhost:5000'
        print(f"📍 Using default localhost: {url}")
        return url
        
    def create_payment(self, user, plan, reference):
        """
        Create a new payment request using Paynow SDK
        Returns: dict with payment_url and poll_url or None if failed
        """
        try:
            print(f"\n{'='*60}")
            print(f"💳 PAYMENT CREATION STARTED")
            print(f"{'='*60}")
            print(f"Reference: {reference}")
            print(f"User Email: {user.email}")
            print(f"Plan: {plan.name}")
            print(f"Amount: ${plan.price} {plan.currency}")
            print(f"Return URL: {self.return_url}")
            print(f"Result URL: {self.result_url}")
            print(f"Production Mode: {self.is_production}")
            print(f"{'='*60}\n")
            
            # Create payment using Paynow SDK
            payment = self.paynow.create_payment(reference, user.email)
            print(f"✅ Payment object created")
            
            # Add item to payment
            payment.add(f"{plan.name} Subscription", plan.price)
            print(f"✅ Item added to payment: {plan.name} - ${plan.price}")
            
            # Send payment request to Paynow
            if self.is_production:
                # Production: Send to real Paynow
                print(f"💳 Sending payment to REAL Paynow API...")
                print(f"   Integration ID: {self.integration_id}")
                print(f"   Integration Key: {self.integration_key[:10]}...")
                response = self.paynow.send(payment)
                print(f"📡 Response received from Paynow")
            else:
                # Development: Use mock gateway
                print(f"🧪 Using MOCK payment gateway (localhost mode)")
                return {
                    'success': True,
                    'payment_url': f'{self.base_url}/payment/mock?ref={reference}',
                    'poll_url': f'{self.base_url}/payment/poll?ref={reference}'
                }
            
            # Check if payment initiation was successful
            if response.success:
                print(f"\n{'='*60}")
                print(f"✅ PAYMENT CREATED SUCCESSFULLY")
                print(f"{'='*60}")
                print(f"Redirect URL: {response.redirect_url}")
                print(f"Poll URL: {response.poll_url}")
                print(f"{'='*60}\n")
                return {
                    'success': True,
                    'payment_url': response.redirect_url,  # URL to redirect user to
                    'poll_url': response.poll_url  # URL to check payment status
                }
            else:
                # Payment failed - gather detailed error information
                print(f"\n{'='*60}")
                print(f"❌ PAYNOW PAYMENT FAILED")
                print(f"{'='*60}")
                
                # Try to get error from multiple sources
                error_msg = 'Payment initiation failed - no error details provided'
                
                # Check for error in response.data dict (most reliable)
                if hasattr(response, 'data') and isinstance(response.data, dict):
                    if 'error' in response.data:
                        error_msg = response.data['error']
                        print(f"Error from response.data['error']: {error_msg}")
                
                # Check for errors attribute
                elif hasattr(response, 'errors') and response.errors:
                    error_msg = str(response.errors)
                    print(f"Error from response.errors: {error_msg}")
                    print(f"Error type: {type(response.errors)}")
                
                # Check for error attribute (singular)
                elif hasattr(response, 'error') and response.error:
                    # Skip if error is a type object
                    if not isinstance(response.error, type):
                        error_msg = str(response.error)
                        print(f"Error from response.error: {error_msg}")
                        print(f"Error type: {type(response.error)}")
                
                # Show all response attributes for debugging
                print(f"Response attributes:")
                for attr, value in response.__dict__.items():
                    print(f"   {attr}: {value} (type: {type(value).__name__})")
                
                print(f"Response success: {response.success}")
                print(f"{'='*60}\n")
                
                # Ensure error_msg is always a string
                if not isinstance(error_msg, str):
                    error_msg = str(error_msg)
                
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            print(f"\n{'='*60}")
            print(f"❌ EXCEPTION DURING PAYMENT CREATION")
            print(f"{'='*60}")
            print(f"Exception type: {type(e).__name__}")
            print(f"Exception message: {str(e)}")
            print(f"{'='*60}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
            return {
                'success': False,
                'error': f"{type(e).__name__}: {str(e)}"
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
            if self.is_production and hash_value:
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
            if self.is_production:
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
