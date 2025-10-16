"""
Payment handler for Paynow integration
Handles payment initialization, confirmation, and status checking
"""

import os
from datetime import datetime, timedelta
from models import db, User, PendingPayment, Transaction, SubscriptionPlan
import hashlib
import hmac
import urllib.parse

class PaynowHandler:
    def __init__(self):
        self.integration_id = os.getenv('PAYNOW_INTEGRATION_ID', 'test_integration')
        self.integration_key = os.getenv('PAYNOW_INTEGRATION_KEY', 'test_key')
        self.return_url = os.getenv('PAYNOW_RETURN_URL', 'http://localhost:5000/payment/return')
        self.result_url = os.getenv('PAYNOW_RESULT_URL', 'http://localhost:5000/payment/notify')
        self.paynow_url = os.getenv('PAYNOW_URL', 'https://www.paynow.co.zw/interface/initiatetransaction')
        
    def create_payment(self, user, plan, reference):
        """
        Create a new payment request
        Returns: dict with payment_url and poll_url or None if failed
        """
        try:
            # Build payment data
            payment_data = {
                'id': self.integration_id,
                'reference': reference,
                'amount': f"{plan.price:.2f}",
                'additionalinfo': f"{plan.name} Subscription",
                'returnurl': self.return_url,
                'resulturl': self.result_url,
                'authemail': user.email,
                'status': 'Message'
            }
            
            # Generate hash
            payment_data['hash'] = self._generate_hash(payment_data)
            
            # In production, you would POST this to Paynow
            # For now, we'll simulate the response
            
            # Simulated response (in production, parse Paynow's actual response)
            if os.getenv('FLASK_ENV') == 'production':
                # TODO: Implement actual HTTP POST to Paynow
                import requests
                response = requests.post(self.paynow_url, data=payment_data)
                response_data = self._parse_response(response.text)
            else:
                # Development/Test mode - simulate success
                response_data = {
                    'status': 'Ok',
                    'browserurl': f'http://localhost:5000/payment/mock?ref={reference}',
                    'pollurl': f'http://localhost:5000/payment/poll?ref={reference}',
                    'hash': 'test_hash'
                }
            
            if response_data.get('status') == 'Ok':
                return {
                    'success': True,
                    'payment_url': response_data.get('browserurl'),
                    'poll_url': response_data.get('pollurl')
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('error', 'Unknown error')
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
            pending.updated_at = datetime.utcnow()
            
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
            start_date = datetime.utcnow()
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
        Check payment status using poll URL
        Returns: dict with status information
        """
        try:
            if os.getenv('FLASK_ENV') == 'production':
                # TODO: Implement actual polling to Paynow
                import requests
                response = requests.post(poll_url, data={'id': self.integration_id})
                return self._parse_response(response.text)
            else:
                # Development mode - return mock status
                return {
                    'status': 'Paid',
                    'reference': 'TEST-REF',
                    'amount': '10.00',
                    'paynowreference': 'PAYNOW-12345'
                }
        except Exception as e:
            return {
                'status': 'Error',
                'error': str(e)
            }
    
    def _generate_hash(self, data):
        """Generate hash for Paynow integration"""
        # Create string from data
        values = [
            self.integration_id,
            data.get('reference', ''),
            data.get('amount', ''),
            data.get('additionalinfo', ''),
            self.return_url,
            self.result_url,
            data.get('authemail', ''),
            data.get('status', '')
        ]
        
        hash_string = ''.join(str(v) for v in values)
        hash_string += self.integration_key
        
        # Generate SHA512 hash
        return hashlib.sha512(hash_string.encode()).hexdigest().upper()
    
    def _parse_response(self, response_text):
        """Parse Paynow response into dictionary"""
        result = {}
        for line in response_text.split('&'):
            if '=' in line:
                key, value = line.split('=', 1)
                result[key.lower()] = urllib.parse.unquote_plus(value)
        return result

# Global payment handler instance
payment_handler = PaynowHandler()
