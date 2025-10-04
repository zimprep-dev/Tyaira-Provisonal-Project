"""
Simple script to test mobile device detection
Run this to verify the utils.py module works correctly
"""

from utils import is_mobile_device, get_device_type

# Test various User-Agent strings
test_cases = [
    {
        'name': 'iPhone 13',
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15',
        'expected': 'mobile'
    },
    {
        'name': 'Android Samsung',
        'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36',
        'expected': 'mobile'
    },
    {
        'name': 'iPad',
        'user_agent': 'Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15',
        'expected': 'mobile'
    },
    {
        'name': 'Desktop Chrome',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/95.0',
        'expected': 'desktop'
    },
    {
        'name': 'Desktop Firefox',
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:93.0) Gecko/20100101 Firefox/93.0',
        'expected': 'desktop'
    }
]

def test_device_detection():
    print("=" * 60)
    print("MOBILE DEVICE DETECTION TEST")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        # Simulate the User-Agent header
        from flask import Flask
        app = Flask(__name__)
        
        with app.test_request_context(headers={'User-Agent': test['user_agent']}):
            detected = get_device_type()
            is_correct = detected == test['expected']
            
            status = "✓ PASS" if is_correct else "✗ FAIL"
            
            print(f"\n{status} - {test['name']}")
            print(f"  Expected: {test['expected']}")
            print(f"  Detected: {detected}")
            
            if is_correct:
                passed += 1
            else:
                failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✓ All tests passed! Mobile detection is working correctly.")
    else:
        print("✗ Some tests failed. Check the utils.py implementation.")

if __name__ == '__main__':
    test_device_detection()
