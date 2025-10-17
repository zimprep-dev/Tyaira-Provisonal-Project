"""
Access Control System - Enforces plan limits and feature access
"""

from models import User, TestResult
from datetime import datetime, timezone
from flask import flash

def can_take_test(user):
    """
    Check if user can take a test based on their plan
    Returns: (can_take: bool, reason: str)
    """
    # Admin can always take tests
    if user.username == 'admin':
        return True, None
    
    # Check if user has active subscription
    if not user.has_active_subscription():
        return False, "You need an active subscription to take tests"
    
    # Get user's plan
    if not user.subscription_plan_id:
        return False, "No plan associated with your account"
    
    plan = user.subscription_plan
    
    # Check unlimited tests
    if plan.has_unlimited_tests:
        return True, None
    
    # Check test credits (for usage-based plans)
    if plan.test_credits > 0:
        # Count tests taken since subscription started
        tests_taken = TestResult.query.filter_by(user_id=user.id).filter(
            TestResult.timestamp >= user.subscription_start_date
        ).count()
        
        if tests_taken >= plan.test_credits:
            return False, f"You've used all {plan.test_credits} test credits. Please purchase more."
        
        remaining = plan.test_credits - tests_taken
        if remaining <= 2:
            flash(f"Warning: You have {remaining} test(s) remaining!", "warning")
        
        return True, None
    
    # Check monthly test limit
    if plan.max_tests_per_month:
        # Count tests in current month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        tests_this_month = TestResult.query.filter_by(user_id=user.id).filter(
            TestResult.timestamp >= month_start
        ).count()
        
        if tests_this_month >= plan.max_tests_per_month:
            return False, f"Monthly limit of {plan.max_tests_per_month} tests reached. Try again next month."
        
        remaining = plan.max_tests_per_month - tests_this_month
        if remaining <= 3:
            flash(f"Notice: {remaining} test(s) remaining this month", "info")
        
        return True, None
    
    # Default: allow test
    return True, None


def can_download_pdf(user):
    """Check if user can download PDFs"""
    if user.username == 'admin':
        return True
    
    if not user.has_active_subscription():
        return False
    
    if not user.subscription_plan_id:
        return False
    
    return user.subscription_plan.has_download_access


def can_view_progress(user):
    """Check if user can view progress tracking"""
    if user.username == 'admin':
        return True
    
    if not user.has_active_subscription():
        return False
    
    if not user.subscription_plan_id:
        return False
    
    return user.subscription_plan.has_progress_tracking


def can_view_analytics(user):
    """Check if user can view performance analytics"""
    if user.username == 'admin':
        return True
    
    if not user.has_active_subscription():
        return False
    
    if not user.subscription_plan_id:
        return False
    
    return user.subscription_plan.has_performance_analytics


def get_test_stats(user):
    """
    Get user's test usage statistics
    Returns: dict with test counts and limits
    """
    if not user.has_active_subscription() or not user.subscription_plan_id:
        return {
            'total_tests': 0,
            'limit': 0,
            'unlimited': False,
            'remaining': 0
        }
    
    plan = user.subscription_plan
    
    if plan.has_unlimited_tests:
        tests_taken = TestResult.query.filter_by(user_id=user.id).count()
        return {
            'total_tests': tests_taken,
            'limit': None,
            'unlimited': True,
            'remaining': None
        }
    
    if plan.test_credits > 0:
        tests_taken = TestResult.query.filter_by(user_id=user.id).filter(
            TestResult.timestamp >= user.subscription_start_date
        ).count()
        return {
            'total_tests': tests_taken,
            'limit': plan.test_credits,
            'unlimited': False,
            'remaining': max(0, plan.test_credits - tests_taken)
        }
    
    if plan.max_tests_per_month:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        tests_this_month = TestResult.query.filter_by(user_id=user.id).filter(
            TestResult.timestamp >= month_start
        ).count()
        return {
            'total_tests': tests_this_month,
            'limit': plan.max_tests_per_month,
            'unlimited': False,
            'remaining': max(0, plan.max_tests_per_month - tests_this_month),
            'monthly': True
        }
    
    return {
        'total_tests': 0,
        'limit': 0,
        'unlimited': False,
        'remaining': 0
    }
