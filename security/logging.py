"""
Universal Security Framework - Security Logging
Centralized security logging and monitoring
"""
import logging
from datetime import datetime

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# Create file handler if not exists
if not security_logger.handlers:
    handler = logging.FileHandler('security.log')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)

def log_security_event(event_type, message, user=None, ip_address=None, severity='INFO'):
    """Log security events with context"""
    context = f"[{event_type}]"
    if user:
        context += f" User: {user}"
    if ip_address:
        context += f" IP: {ip_address}"
    
    full_message = f"{context} - {message}"
    
    if severity == 'CRITICAL':
        security_logger.critical(full_message)
    elif severity == 'ERROR':
        security_logger.error(full_message)
    elif severity == 'WARNING':
        security_logger.warning(full_message)
    else:
        security_logger.info(full_message)