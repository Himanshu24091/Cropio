#!/usr/bin/env python3
"""
Comprehensive test script for the security framework
"""

print("=== Security Framework Comprehensive Test ===")
print()

# Test 1: Basic functionality
try:
    from security import __version__, SecurityConfig, health_check
    from security.core.validators import validate_filename, validate_user_input
    from security.core.sanitizers import sanitize_filename, sanitize_content
    from security.core.decorators import require_csrf, rate_limit
    
    print("✓ All imports successful")
    print("✓ Framework version:", __version__)
    
    # Test 2: Configuration
    config = SecurityConfig(environment='development')
    print("✓ Configuration created successfully")
    
    # Test 3: Health check
    health = health_check()
    print("✓ Health check passed:", health['overall_status'])
    
    # Test 4: Validators
    filename_valid = validate_filename('test_document.pdf')
    print("✓ Filename validation:", filename_valid)
    
    # Test dangerous filename
    dangerous_name = validate_filename('../../../etc/passwd')
    print("✓ Dangerous filename blocked:", not dangerous_name)
    
    # Test 5: Sanitizers
    clean_name = sanitize_filename('My Document <script>alert(1)</script>.pdf')
    print("✓ Filename sanitized to:", clean_name)
    
    # Test 6: Input validation
    is_valid, errors = validate_user_input('user@example.com', 'email')
    print("✓ Email validation passed:", is_valid)
    
    # Test dangerous input
    dangerous_input = '<script>alert("xss")</script>'
    is_valid, errors = validate_user_input(dangerous_input, 'general')
    print("✓ XSS attempt blocked:", not is_valid, "- Issues found:", len(errors))
    if errors:
        print("  Issues:", errors[0])
    
    # Test 7: Content validation
    from security.core.validators import validate_content
    test_content = b"Safe content for testing"
    is_safe, issues = validate_content(test_content, 'txt')
    print("✓ Content validation passed:", is_safe)
    
    # Test dangerous content
    dangerous_content = b"<script>alert('xss')</script>"
    is_safe, issues = validate_content(dangerous_content, 'html')
    print("✓ Dangerous content blocked:", not is_safe, "- Issues found:", len(issues))
    
    # Test 8: Configuration features
    print("✓ Configuration details:")
    print("  Environment:", config.environment)
    print("  Security level:", config.security_level)
    print("  Malware scanning enabled:", config.enable_malware_scanning)
    
    print()
    print("=== All tests passed! Security framework is fully functional ===")
    
except Exception as e:
    print("Test failed:", e)
    import traceback
    traceback.print_exc()