"""
Universal Security Framework - Cryptography
Secure hashing and encryption utilities
"""
import hashlib
import hmac
import secrets
from datetime import datetime

def secure_hash(data, algorithm='sha256'):
    """Generate secure hash of data"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    if algorithm == 'sha256':
        return hashlib.sha256(data).hexdigest()
    elif algorithm == 'sha512':
        return hashlib.sha512(data).hexdigest()
    else:
        return hashlib.sha256(data).hexdigest()

def generate_token(length=32):
    """Generate secure random token"""
    return secrets.token_urlsafe(length)

def verify_hmac(message, signature, key):
    """Verify HMAC signature"""
    if isinstance(message, str):
        message = message.encode('utf-8')
    if isinstance(key, str):
        key = key.encode('utf-8')
    
    expected = hmac.new(key, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)