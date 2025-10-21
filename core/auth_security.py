"""
Professional Authentication Security System for Cropio SaaS Platform
Implements advanced password policies, rate limiting, session management, and audit logging
"""
import re
import time
import hashlib
import secrets
import pyotp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import request, session, current_app, g
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from collections import defaultdict
from core.logging_config import cropio_logger


class AuthenticationError(Exception):
    """Authentication related errors"""
    pass


class PasswordPolicyViolation(AuthenticationError):
    """Password policy violation error"""
    pass


class AccountLockedException(AuthenticationError):
    """Account locked error"""
    pass


class RateLimitExceededError(AuthenticationError):
    """Rate limit exceeded error"""
    pass


class PasswordSecurityManager:
    """Advanced password security management"""
    
    # Common passwords to reject
    COMMON_PASSWORDS = {
        'password', '123456', '123456789', 'qwerty', 'abc123', 'password123',
        'admin', 'administrator', 'root', 'user', 'guest', 'test', 'demo',
        'login', 'welcome', '111111', '000000', 'secret', 'letmein',
        'dragon', 'sunshine', 'master', 'hello', 'freedom', 'whatever',
        'qazwsx', '123123', 'football', 'monkey', 'mustang', 'shadow'
    }
    
    # Keyboard patterns to detect
    KEYBOARD_PATTERNS = [
        'qwerty', 'qwertyui', 'asdf', 'asdfgh', 'zxcv', 'zxcvbn',
        '1234567890', '0987654321', 'abcdefg', 'zyxwvuts'
    ]
    
    def __init__(self):
        self.ph = PasswordHasher(
            memory_cost=65536,  # 64 MB
            time_cost=3,        # 3 iterations
            parallelism=4,      # 4 parallel threads
            hash_len=32,        # 32 byte hash
            salt_len=16         # 16 byte salt
        )
    
    def validate_password_strength(self, password: str, username: str = None, 
                                 email: str = None) -> Tuple[bool, List[str]]:
        """Comprehensive password strength validation"""
        errors = []
        
        # Basic length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")
        
        # Character diversity requirements
        has_lower = bool(re.search(r'[a-z]', password))
        has_upper = bool(re.search(r'[A-Z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not has_lower:
            errors.append("Password must contain at least one lowercase letter")
        if not has_upper:
            errors.append("Password must contain at least one uppercase letter")
        if not has_digit:
            errors.append("Password must contain at least one number")
        if not has_special:
            errors.append("Password must contain at least one special character")
        
        # Check for common passwords
        if password.lower() in self.COMMON_PASSWORDS:
            errors.append("Password is too common. Please choose a more unique password")
        
        # Check for keyboard patterns
        password_lower = password.lower()
        for pattern in self.KEYBOARD_PATTERNS:
            if pattern in password_lower or pattern[::-1] in password_lower:
                errors.append("Password contains common keyboard patterns")
                break
        
        # Check for personal information in password
        if username:
            if username.lower() in password_lower:
                errors.append("Password must not contain your username")
        
        if email:
            email_parts = email.lower().split('@')[0]
            if len(email_parts) >= 3 and email_parts in password_lower:
                errors.append("Password must not contain your email address")
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password must not contain more than 2 consecutive identical characters")
        
        # Check for sequential characters
        sequences = ['abc', 'bcd', 'cde', 'def', '123', '234', '345', '456']
        for seq in sequences:
            if seq in password_lower or seq[::-1] in password_lower:
                errors.append("Password must not contain sequential characters")
                break
        
        # Calculate password entropy
        entropy = self._calculate_entropy(password)
        if entropy < 50:
            errors.append("Password is too predictable. Please use a more complex password")
        
        return len(errors) == 0, errors
    
    def _calculate_entropy(self, password: str) -> float:
        """Calculate password entropy"""
        character_sets = 0
        if re.search(r'[a-z]', password):
            character_sets += 26
        if re.search(r'[A-Z]', password):
            character_sets += 26
        if re.search(r'\d', password):
            character_sets += 10
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            character_sets += 32
        
        if character_sets == 0:
            return 0
        
        import math
        return len(password) * math.log2(character_sets)
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        try:
            return self.ph.hash(password)
        except HashingError as e:
            cropio_logger.error(f"Password hashing failed: {e}")
            # Fallback to Werkzeug
            return generate_password_hash(password)
    
    def verify_password(self, hashed: str, password: str) -> bool:
        """Verify password against hash"""
        try:
            # Try Argon2 first
            if hashed.startswith('$argon2'):
                self.ph.verify(hashed, password)
                return True
            else:
                # Fallback to Werkzeug for legacy passwords
                return check_password_hash(hashed, password)
        except VerifyMismatchError:
            return False
        except Exception as e:
            cropio_logger.error(f"Password verification failed: {e}")
            return False
    
    def needs_rehash(self, hashed: str) -> bool:
        """Check if password needs rehashing"""
        if not hashed.startswith('$argon2'):
            return True  # Upgrade from Werkzeug to Argon2
        
        try:
            return self.ph.check_needs_rehash(hashed)
        except Exception:
            return True


class LoginRateLimiter:
    """Advanced login rate limiting with IP and account-based tracking"""
    
    def __init__(self):
        self.login_attempts = defaultdict(list)
        self.locked_accounts = defaultdict(dict)
        self.ip_attempts = defaultdict(list)
        self.suspicious_ips = set()
    
    def is_account_locked(self, identifier: str) -> Tuple[bool, Optional[int]]:
        """Check if account is locked"""
        if identifier not in self.locked_accounts:
            return False, None
        
        lock_info = self.locked_accounts[identifier]
        lock_time = lock_info.get('lock_time', 0)
        duration = lock_info.get('duration', 300)  # 5 minutes default
        
        if time.time() - lock_time < duration:
            remaining = int(duration - (time.time() - lock_time))
            return True, remaining
        else:
            # Lock expired, remove it
            del self.locked_accounts[identifier]
            self.login_attempts[identifier] = []
            return False, None
    
    def record_login_attempt(self, identifier: str, ip_address: str, 
                           success: bool, user_id: int = None) -> None:
        """Record a login attempt"""
        now = time.time()
        
        # Clean old attempts (keep last 24 hours)
        cutoff = now - 86400  # 24 hours
        self.login_attempts[identifier] = [
            attempt for attempt in self.login_attempts[identifier]
            if attempt['timestamp'] > cutoff
        ]
        
        self.ip_attempts[ip_address] = [
            attempt for attempt in self.ip_attempts[ip_address]
            if attempt['timestamp'] > cutoff
        ]
        
        # Record attempt
        attempt_data = {
            'timestamp': now,
            'ip_address': ip_address,
            'success': success,
            'user_id': user_id
        }
        
        if not success:
            self.login_attempts[identifier].append(attempt_data)
            self.ip_attempts[ip_address].append(attempt_data)
            
            # Check for account lockout
            self._check_account_lockout(identifier)
            self._check_suspicious_ip(ip_address)
        else:
            # Successful login, reset attempts for this account
            self.login_attempts[identifier] = []
        
        # Log attempt
        cropio_logger.security_event(
            'login_attempt',
            f"Login attempt: {identifier} from {ip_address}",
            user_id=user_id,
            extra_data={
                'identifier': identifier,
                'ip_address': ip_address,
                'success': success,
                'user_agent': request.headers.get('User-Agent', ''),
                'referer': request.headers.get('Referer', '')
            }
        )
    
    def _check_account_lockout(self, identifier: str) -> None:
        """Check if account should be locked"""
        attempts = self.login_attempts[identifier]
        recent_attempts = [
            a for a in attempts 
            if time.time() - a['timestamp'] < 3600  # Last hour
        ]
        
        if len(recent_attempts) >= 5:
            # Progressive lockout duration
            previous_locks = len([
                lock for lock in self.locked_accounts.get(identifier + '_history', [])
                if time.time() - lock < 86400  # Last 24 hours
            ])
            
            duration = min(300 * (2 ** previous_locks), 3600)  # Max 1 hour
            
            self.locked_accounts[identifier] = {
                'lock_time': time.time(),
                'duration': duration,
                'reason': f'Too many failed login attempts ({len(recent_attempts)})'
            }
            
            # Track lock history
            history_key = identifier + '_history'
            if history_key not in self.locked_accounts:
                self.locked_accounts[history_key] = []
            self.locked_accounts[history_key].append(time.time())
            
            cropio_logger.security_event(
                'account_locked',
                f"Account locked: {identifier}",
                extra_data={
                    'identifier': identifier,
                    'duration': duration,
                    'failed_attempts': len(recent_attempts),
                    'lockout_number': previous_locks + 1
                }
            )
    
    def _check_suspicious_ip(self, ip_address: str) -> None:
        """Check for suspicious IP activity"""
        attempts = self.ip_attempts[ip_address]
        recent_attempts = [
            a for a in attempts 
            if time.time() - a['timestamp'] < 3600  # Last hour
        ]
        
        # Mark IP as suspicious if many failed attempts from different accounts
        unique_accounts = len(set(
            request.form.get('username_or_email', '') 
            for a in recent_attempts
        ))
        
        if len(recent_attempts) >= 10 or unique_accounts >= 5:
            self.suspicious_ips.add(ip_address)
            
            cropio_logger.security_event(
                'suspicious_ip_detected',
                f"Suspicious IP detected: {ip_address}",
                extra_data={
                    'ip_address': ip_address,
                    'failed_attempts': len(recent_attempts),
                    'unique_accounts_targeted': unique_accounts,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            )
    
    def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP is marked as suspicious"""
        return ip_address in self.suspicious_ips


class SessionManager:
    """Advanced session management with security features"""
    
    def __init__(self):
        self.active_sessions = defaultdict(dict)
    
    def create_session(self, user_id: int, ip_address: str, user_agent: str) -> str:
        """Create a new secure session"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'csrf_token': secrets.token_urlsafe(32)
        }
        
        self.active_sessions[user_id][session_id] = session_data
        
        # Store in Flask session
        session['session_id'] = session_id
        session['csrf_token'] = session_data['csrf_token']
        session.permanent = True
        
        cropio_logger.info(
            f"New session created for user {user_id}",
            extra_data={
                'user_id': user_id,
                'session_id': session_id[:8] + '...',  # Partial session ID for logging
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
        
        return session_id
    
    def validate_session(self, user_id: int, session_id: str, 
                        ip_address: str, user_agent: str) -> bool:
        """Validate session security"""
        if user_id not in self.active_sessions:
            return False
        
        if session_id not in self.active_sessions[user_id]:
            return False
        
        session_data = self.active_sessions[user_id][session_id]
        
        # Check IP address (with some flexibility for mobile networks)
        if session_data['ip_address'] != ip_address:
            # Allow IP changes within same subnet for mobile users
            if not self._is_same_network(session_data['ip_address'], ip_address):
                cropio_logger.security_event(
                    'session_ip_mismatch',
                    f"Session IP mismatch for user {user_id}",
                    user_id=user_id,
                    extra_data={
                        'original_ip': session_data['ip_address'],
                        'current_ip': ip_address,
                        'session_id': session_id[:8] + '...'
                    }
                )
                return False
        
        # Check user agent (basic check)
        if session_data['user_agent'] != user_agent:
            cropio_logger.security_event(
                'session_user_agent_mismatch',
                f"User agent changed for user {user_id}",
                user_id=user_id,
                extra_data={
                    'original_ua': session_data['user_agent'],
                    'current_ua': user_agent,
                    'session_id': session_id[:8] + '...'
                }
            )
            # Don't invalidate for user agent changes, just log
        
        # Check session age
        max_age = timedelta(hours=24)
        if datetime.utcnow() - session_data['created_at'] > max_age:
            self.invalidate_session(user_id, session_id)
            return False
        
        # Check inactivity
        max_inactivity = timedelta(hours=4)
        if datetime.utcnow() - session_data['last_activity'] > max_inactivity:
            self.invalidate_session(user_id, session_id)
            return False
        
        # Update last activity
        session_data['last_activity'] = datetime.utcnow()
        return True
    
    def _is_same_network(self, ip1: str, ip2: str) -> bool:
        """Check if two IPs are in the same /24 network"""
        try:
            import ipaddress
            net1 = ipaddress.IPv4Network(f"{ip1}/24", strict=False)
            ip2_addr = ipaddress.IPv4Address(ip2)
            return ip2_addr in net1
        except:
            return ip1 == ip2
    
    def invalidate_session(self, user_id: int, session_id: str) -> None:
        """Invalidate a specific session"""
        if (user_id in self.active_sessions and 
            session_id in self.active_sessions[user_id]):
            del self.active_sessions[user_id][session_id]
            
            cropio_logger.info(
                f"Session invalidated for user {user_id}",
                extra_data={
                    'user_id': user_id,
                    'session_id': session_id[:8] + '...'
                }
            )
    
    def invalidate_all_sessions(self, user_id: int) -> None:
        """Invalidate all sessions for a user"""
        if user_id in self.active_sessions:
            session_count = len(self.active_sessions[user_id])
            del self.active_sessions[user_id]
            
            cropio_logger.security_event(
                'all_sessions_invalidated',
                f"All sessions invalidated for user {user_id}",
                user_id=user_id,
                extra_data={
                    'user_id': user_id,
                    'session_count': session_count
                }
            )


class TwoFactorManager:
    """Two-factor authentication management"""
    
    def generate_secret(self, username: str) -> str:
        """Generate a new 2FA secret"""
        return pyotp.random_base32()
    
    def generate_qr_code_url(self, secret: str, username: str, 
                           issuer_name: str = "Cropio") -> str:
        """Generate QR code URL for 2FA setup"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=issuer_name
        )
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify 2FA token"""
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            cropio_logger.error(f"2FA verification error: {e}")
            return False
    
    def generate_backup_codes(self, count: int = 8) -> List[str]:
        """Generate backup codes for 2FA"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice('0123456789') for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes


# Global instances
password_manager = PasswordSecurityManager()
rate_limiter = LoginRateLimiter()
session_manager = SessionManager()
two_factor_manager = TwoFactorManager()


def enhance_user_model():
    """Add security-related methods to User model"""
    
    def set_secure_password(self, password: str) -> bool:
        """Set password with security validation"""
        is_valid, errors = password_manager.validate_password_strength(
            password, self.username, self.email
        )
        
        if not is_valid:
            raise PasswordPolicyViolation("; ".join(errors))
        
        self.password_hash = password_manager.hash_password(password)
        self.password_changed_at = datetime.utcnow()
        return True
    
    def check_secure_password(self, password: str) -> bool:
        """Check password and handle rehashing"""
        is_valid = password_manager.verify_password(self.password_hash, password)
        
        if is_valid and password_manager.needs_rehash(self.password_hash):
            # Rehash password with current settings
            self.password_hash = password_manager.hash_password(password)
            # Don't update password_changed_at for rehashing
        
        return is_valid
    
    def is_account_locked(self) -> Tuple[bool, Optional[int]]:
        """Check if account is locked due to failed attempts"""
        if self.account_locked:
            return True, None
        
        return rate_limiter.is_account_locked(self.username)
    
    def enable_two_factor(self) -> Tuple[str, str]:
        """Enable 2FA and return secret and QR code URL"""
        secret = two_factor_manager.generate_secret(self.username)
        qr_url = two_factor_manager.generate_qr_code_url(secret, self.username)
        
        self.two_factor_secret = secret
        self.two_factor_enabled = True
        
        cropio_logger.security_event(
            'two_factor_enabled',
            f"2FA enabled for user {self.username}",
            user_id=self.id
        )
        
        return secret, qr_url
    
    def verify_two_factor(self, token: str) -> bool:
        """Verify 2FA token"""
        if not self.two_factor_enabled or not self.two_factor_secret:
            return True  # 2FA not enabled
        
        return two_factor_manager.verify_token(self.two_factor_secret, token)
    
    # Add methods to User class (would be done via monkey patching or model extension)
    # This is for reference - actual implementation would integrate with the User model


def log_security_event(event_type: str, description: str, user_id: int = None, 
                      extra_data: Dict[str, Any] = None) -> None:
    """Log security-related events"""
    cropio_logger.security_event(
        event_type,
        description,
        user_id=user_id,
        extra_data=extra_data or {}
    )
