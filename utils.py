"""
Utility functions for the driving test platform
"""
from flask import request

def is_mobile_device():
    """
    Detect if the request is coming from a mobile device
    based on the User-Agent header
    """
    user_agent = request.headers.get('User-Agent', '').lower()
    
    mobile_keywords = [
        'android', 'iphone', 'ipad', 'ipod',
        'mobile', 'blackberry', 'windows phone',
        'webos', 'opera mini', 'opera mobi'
    ]
    
    return any(keyword in user_agent for keyword in mobile_keywords)

def get_device_type():
    """
    Get the device type (mobile or desktop)
    """
    # TEMPORARY: Force mobile for testing
    # return 'mobile'
    
    return 'mobile' if is_mobile_device() else 'desktop'
