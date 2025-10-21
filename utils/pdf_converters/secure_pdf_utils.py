# utils/pdf_converters/secure_pdf_utils.py
"""
Secure PDF Utilities - PDF Security and Protection Operations
Provides encryption, decryption, QR code generation, and security validation
"""

import os
import io
import uuid
import time
import hashlib
import secrets
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import logging

# Universal Security Framework Integration
try:
    from security.core.validators import validate_content, validate_filename
    from security.core.sanitizers import sanitize_filename
    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False

# PDF Processing
try:
    import PyPDF2
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# QR Code Generation
try:
    import qrcode
    from qrcode.image.pure import PyPNGImage
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

# Image Processing for QR
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Setup logger
logger = logging.getLogger(__name__)


# ============================================================================
# PASSWORD VALIDATION AND STRENGTH CHECKING
# ============================================================================

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength and return detailed analysis.
    
    Args:
        password: Password string to validate
        
    Returns:
        Dictionary with strength score, level, and recommendations
    """
    if not password:
        return {
            'valid': False,
            'score': 0,
            'level': 'invalid',
            'message': 'Password is required',
            'recommendations': ['Password cannot be empty']
        }
    
    score = 0
    recommendations = []
    
    # Length checks
    length = len(password)
    if length < 6:
        return {
            'valid': False,
            'score': 0,
            'level': 'too_short',
            'message': 'Password must be at least 6 characters',
            'recommendations': ['Use at least 6 characters']
        }
    
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    else:
        recommendations.append('Use 12 or more characters for better security')
    
    # Character variety checks
    has_lowercase = any(c.islower() for c in password)
    has_uppercase = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)
    
    if has_lowercase:
        score += 1
    else:
        recommendations.append('Include lowercase letters')
    
    if has_uppercase:
        score += 1
    else:
        recommendations.append('Include uppercase letters')
    
    if has_digit:
        score += 1
    else:
        recommendations.append('Include numbers')
    
    if has_special:
        score += 1
    else:
        recommendations.append('Include special characters (!@#$%^&*)')
    
    # Determine level
    if score <= 2:
        level = 'weak'
        message = 'Weak password - not recommended'
    elif score <= 4:
        level = 'fair'
        message = 'Fair password - consider strengthening'
    elif score <= 5:
        level = 'good'
        message = 'Good password'
    else:
        level = 'strong'
        message = 'Strong password'
    
    return {
        'valid': True,
        'score': score,
        'level': level,
        'message': message,
        'recommendations': recommendations,
        'has_lowercase': has_lowercase,
        'has_uppercase': has_uppercase,
        'has_digit': has_digit,
        'has_special': has_special
    }


def passwords_match(password: str, confirm_password: str) -> bool:
    """
    Check if two passwords match.
    
    Args:
        password: First password
        confirm_password: Confirmation password
        
    Returns:
        True if passwords match, False otherwise
    """
    return password == confirm_password


# ============================================================================
# PDF ENCRYPTION AND PROTECTION
# ============================================================================

def encrypt_pdf_with_password(
    pdf_file: Union[str, BytesIO, Any],
    password: str,
    user_permissions: Optional[Dict[str, bool]] = None
) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
    """
    Encrypt a PDF file with password protection.
    
    Args:
        pdf_file: PDF file path, BytesIO object, or file-like object
        password: Password to encrypt the PDF
        user_permissions: Optional dictionary of permissions (printing, copying, etc.)
        
    Returns:
        Tuple of (success, encrypted_pdf_buffer, error_message)
    """
    if not PYPDF2_AVAILABLE:
        return False, None, "PyPDF2 library is not available"
    
    if not password:
        return False, None, "Password is required for encryption"
    
    try:
        # Read the PDF
        if isinstance(pdf_file, str):
            # File path provided
            with open(pdf_file, 'rb') as f:
                pdf_reader = PdfReader(f)
                return _perform_encryption(pdf_reader, password, user_permissions)
        else:
            # File-like object (BytesIO, FileStorage, etc.)
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            pdf_reader = PdfReader(pdf_file)
            return _perform_encryption(pdf_reader, password, user_permissions)
            
    except Exception as e:
        logger.error(f"Error encrypting PDF: {e}")
        return False, None, f"Error encrypting PDF: {str(e)}"


def _perform_encryption(
    pdf_reader: PdfReader,
    password: str,
    user_permissions: Optional[Dict[str, bool]] = None
) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
    """
    Internal function to perform PDF encryption.
    """
    try:
        # Check if already encrypted
        if pdf_reader.is_encrypted:
            return False, None, "PDF is already encrypted"
        
        # Create writer
        pdf_writer = PdfWriter()
        
        # Copy all pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Copy metadata if available
        if pdf_reader.metadata:
            pdf_writer.add_metadata(pdf_reader.metadata)
        
        # Encrypt with password
        # PyPDF2 3.x uses encrypt() method
        pdf_writer.encrypt(
            user_password=password,
            owner_password=password,
            use_128bit=True
        )
        
        # Write to buffer
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        logger.info("PDF encrypted successfully")
        return True, output_buffer, None
        
    except Exception as e:
        logger.error(f"Error performing encryption: {e}")
        return False, None, f"Error performing encryption: {str(e)}"


# ============================================================================
# PDF DECRYPTION AND UNLOCKING
# ============================================================================

def decrypt_pdf_with_password(
    pdf_file: Union[str, BytesIO, Any],
    password: str
) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
    """
    Decrypt a password-protected PDF file.
    
    Args:
        pdf_file: PDF file path, BytesIO object, or file-like object
        password: Password to decrypt the PDF
        
    Returns:
        Tuple of (success, decrypted_pdf_buffer, error_message)
    """
    if not PYPDF2_AVAILABLE:
        return False, None, "PyPDF2 library is not available"
    
    if not password:
        return False, None, "Password is required for decryption"
    
    try:
        # Read the PDF
        if isinstance(pdf_file, str):
            with open(pdf_file, 'rb') as f:
                pdf_reader = PdfReader(f)
                return _perform_decryption(pdf_reader, password)
        else:
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            pdf_reader = PdfReader(pdf_file)
            return _perform_decryption(pdf_reader, password)
            
    except Exception as e:
        logger.error(f"Error decrypting PDF: {e}")
        return False, None, f"Error decrypting PDF: {str(e)}"


def _perform_decryption(
    pdf_reader: PdfReader,
    password: str
) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
    """
    Internal function to perform PDF decryption.
    """
    try:
        # Check if encrypted
        if not pdf_reader.is_encrypted:
            return False, None, "PDF is not encrypted"
        
        # Try to decrypt
        decrypt_result = pdf_reader.decrypt(password)
        
        # Check decryption result
        # In PyPDF2 3.x, decrypt() returns an integer (0 = failed, 1 = user password, 2 = owner password)
        if decrypt_result == 0:
            return False, None, "Incorrect password"
        
        # Create writer without encryption
        pdf_writer = PdfWriter()
        
        # Copy all pages
        for page in pdf_reader.pages:
            pdf_writer.add_page(page)
        
        # Copy metadata if available
        if pdf_reader.metadata:
            pdf_writer.add_metadata(pdf_reader.metadata)
        
        # Write to buffer
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        logger.info("PDF decrypted successfully")
        return True, output_buffer, None
        
    except Exception as e:
        logger.error(f"Error performing decryption: {e}")
        return False, None, f"Error performing decryption: {str(e)}"


# ============================================================================
# PDF SECURITY CHECKING
# ============================================================================

def check_pdf_encryption_status(
    pdf_file: Union[str, BytesIO, Any]
) -> Dict[str, Any]:
    """
    Check the encryption status and properties of a PDF file.
    
    Args:
        pdf_file: PDF file path, BytesIO object, or file-like object
        
    Returns:
        Dictionary with encryption status and metadata
    """
    if not PYPDF2_AVAILABLE:
        return {
            'success': False,
            'error': 'PyPDF2 library is not available'
        }
    
    try:
        # Read the PDF
        if isinstance(pdf_file, str):
            with open(pdf_file, 'rb') as f:
                pdf_reader = PdfReader(f)
                return _analyze_pdf_security(pdf_reader)
        else:
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            pdf_reader = PdfReader(pdf_file)
            return _analyze_pdf_security(pdf_reader)
            
    except Exception as e:
        logger.error(f"Error checking PDF security: {e}")
        return {
            'success': False,
            'error': f"Error checking PDF: {str(e)}"
        }


def _analyze_pdf_security(pdf_reader: PdfReader) -> Dict[str, Any]:
    """
    Internal function to analyze PDF security.
    """
    try:
        is_encrypted = pdf_reader.is_encrypted
        
        result = {
            'success': True,
            'is_encrypted': is_encrypted,
            'page_count': len(pdf_reader.pages),
        }
        
        # Get metadata if not encrypted or if accessible
        if not is_encrypted:
            try:
                metadata = pdf_reader.metadata
                if metadata:
                    result['metadata'] = {
                        'title': metadata.get('/Title', 'N/A'),
                        'author': metadata.get('/Author', 'N/A'),
                        'subject': metadata.get('/Subject', 'N/A'),
                        'creator': metadata.get('/Creator', 'N/A'),
                        'producer': metadata.get('/Producer', 'N/A'),
                    }
            except:
                result['metadata'] = None
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing PDF security: {e}")
        return {
            'success': False,
            'error': f"Error analyzing PDF: {str(e)}"
        }


# ============================================================================
# QR CODE GENERATION FOR PDF UNLOCKING
# ============================================================================

def generate_qr_code_for_unlock(
    unlock_url: str,
    size: int = 10,
    border: int = 4
) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
    """
    Generate a QR code image for PDF unlock URL.
    
    Args:
        unlock_url: URL that will unlock the PDF
        size: Size of QR code box (default: 10)
        border: Border size (default: 4)
        
    Returns:
        Tuple of (success, qr_image_buffer, error_message)
    """
    if not QRCODE_AVAILABLE:
        return False, None, "qrcode library is not available"
    
    if not PIL_AVAILABLE:
        return False, None, "PIL library is not available"
    
    if not unlock_url:
        return False, None, "Unlock URL is required"
    
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        
        # Add data
        qr.add_data(unlock_url)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        logger.info("QR code generated successfully")
        return True, img_buffer, None
        
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return False, None, f"Error generating QR code: {str(e)}"


# ============================================================================
# TOKEN MANAGEMENT FOR QR UNLOCK
# ============================================================================

def generate_unlock_token(
    pdf_data: bytes,
    password: str,
    filename: str,
    expiry_hours: int = 1
) -> Dict[str, Any]:
    """
    Generate a secure unlock token for QR-based PDF unlocking.
    
    Args:
        pdf_data: PDF file data as bytes
        password: Password for the PDF
        filename: Original filename
        expiry_hours: Token expiry time in hours (default: 1)
        
    Returns:
        Dictionary with token and metadata
    """
    try:
        # Generate unique token
        token = str(uuid.uuid4())
        
        # Create token data
        token_data = {
            'token': token,
            'filename': filename,
            'password': password,
            'pdf_data': pdf_data,
            'created_at': time.time(),
            'expires_at': time.time() + (expiry_hours * 3600),
            'expiry_hours': expiry_hours,
            'used': False
        }
        
        logger.info(f"Generated unlock token: {token}")
        return token_data
        
    except Exception as e:
        logger.error(f"Error generating unlock token: {e}")
        return None


def validate_unlock_token(
    token_data: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Validate an unlock token.
    
    Args:
        token_data: Token data dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not token_data:
        return False, "Token not found"
    
    try:
        current_time = time.time()
        
        # Check if token has been used
        if token_data.get('used', False):
            return False, "Token has already been used"
        
        # Check if token is expired
        if current_time > token_data.get('expires_at', 0):
            return False, "Token has expired"
        
        # Check if required fields exist
        required_fields = ['pdf_data', 'password', 'filename']
        for field in required_fields:
            if field not in token_data:
                return False, f"Token is missing required field: {field}"
        
        return True, None
        
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return False, f"Error validating token: {str(e)}"


def mark_token_as_used(token_data: Dict[str, Any]) -> None:
    """
    Mark a token as used (one-time use).
    
    Args:
        token_data: Token data dictionary
    """
    if token_data:
        token_data['used'] = True
        token_data['used_at'] = time.time()


def cleanup_expired_tokens(
    token_storage: Dict[str, Dict[str, Any]]
) -> int:
    """
    Remove expired tokens from storage.
    
    Args:
        token_storage: Dictionary storing tokens
        
    Returns:
        Number of tokens removed
    """
    if not token_storage:
        return 0
    
    try:
        current_time = time.time()
        expired_tokens = []
        
        # Find expired tokens
        for token, data in token_storage.items():
            if current_time > data.get('expires_at', 0):
                expired_tokens.append(token)
        
        # Remove expired tokens
        for token in expired_tokens:
            del token_storage[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        
        return len(expired_tokens)
        
    except Exception as e:
        logger.error(f"Error cleaning up tokens: {e}")
        return 0


def get_token_expiry_info(token_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get human-readable expiry information for a token.
    
    Args:
        token_data: Token data dictionary
        
    Returns:
        Dictionary with expiry information
    """
    if not token_data:
        return {
            'expired': True,
            'message': 'Invalid token'
        }
    
    try:
        current_time = time.time()
        expires_at = token_data.get('expires_at', 0)
        
        if current_time > expires_at:
            return {
                'expired': True,
                'message': 'Token has expired'
            }
        
        time_remaining = expires_at - current_time
        hours_remaining = int(time_remaining // 3600)
        minutes_remaining = int((time_remaining % 3600) // 60)
        
        if hours_remaining > 0:
            message = f"{hours_remaining} hour(s) {minutes_remaining} minute(s)"
        else:
            message = f"{minutes_remaining} minute(s)"
        
        return {
            'expired': False,
            'time_remaining_seconds': time_remaining,
            'hours_remaining': hours_remaining,
            'minutes_remaining': minutes_remaining,
            'message': message
        }
        
    except Exception as e:
        logger.error(f"Error getting token expiry info: {e}")
        return {
            'expired': True,
            'message': 'Error checking expiry'
        }


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def save_pdf_to_buffer(pdf_writer: PdfWriter) -> Tuple[bool, Optional[BytesIO], Optional[str]]:
    """
    Save a PDF writer object to a BytesIO buffer.
    
    Args:
        pdf_writer: PyPDF2 PdfWriter object
        
    Returns:
        Tuple of (success, buffer, error_message)
    """
    if not PYPDF2_AVAILABLE:
        return False, None, "PyPDF2 library is not available"
    
    try:
        output_buffer = BytesIO()
        pdf_writer.write(output_buffer)
        output_buffer.seek(0)
        
        return True, output_buffer, None
        
    except Exception as e:
        logger.error(f"Error saving PDF to buffer: {e}")
        return False, None, f"Error saving PDF: {str(e)}"


def generate_protected_filename(original_filename: str, prefix: str = "protected") -> str:
    """
    Generate a filename for a protected PDF.
    
    Args:
        original_filename: Original PDF filename
        prefix: Prefix to add (default: "protected")
        
    Returns:
        New filename with prefix
    """
    if SECURITY_FRAMEWORK_AVAILABLE:
        original_filename = sanitize_filename(original_filename)
    
    # Extract name and extension
    name, ext = os.path.splitext(original_filename)
    
    # Ensure .pdf extension
    if not ext.lower() == '.pdf':
        ext = '.pdf'
    
    # Generate new filename
    return f"{prefix}_{name}{ext}"


def generate_unlocked_filename(original_filename: str, prefix: str = "unlocked") -> str:
    """
    Generate a filename for an unlocked PDF.
    
    Args:
        original_filename: Original PDF filename
        prefix: Prefix to add (default: "unlocked")
        
    Returns:
        New filename with prefix
    """
    return generate_protected_filename(original_filename, prefix)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies are available.
    
    Returns:
        Dictionary with dependency availability status
    """
    return {
        'pypdf2': PYPDF2_AVAILABLE,
        'qrcode': QRCODE_AVAILABLE,
        'pil': PIL_AVAILABLE,
        'security_framework': SECURITY_FRAMEWORK_AVAILABLE
    }


def get_pdf_info(pdf_file: Union[str, BytesIO, Any]) -> Dict[str, Any]:
    """
    Get basic information about a PDF file.
    
    Args:
        pdf_file: PDF file path, BytesIO object, or file-like object
        
    Returns:
        Dictionary with PDF information
    """
    if not PYPDF2_AVAILABLE:
        return {
            'success': False,
            'error': 'PyPDF2 library is not available'
        }
    
    try:
        if isinstance(pdf_file, str):
            with open(pdf_file, 'rb') as f:
                pdf_reader = PdfReader(f)
                return _get_pdf_details(pdf_reader)
        else:
            if hasattr(pdf_file, 'seek'):
                pdf_file.seek(0)
            pdf_reader = PdfReader(pdf_file)
            return _get_pdf_details(pdf_reader)
            
    except Exception as e:
        logger.error(f"Error getting PDF info: {e}")
        return {
            'success': False,
            'error': f"Error reading PDF: {str(e)}"
        }


def _get_pdf_details(pdf_reader: PdfReader) -> Dict[str, Any]:
    """
    Internal function to extract PDF details.
    """
    try:
        return {
            'success': True,
            'page_count': len(pdf_reader.pages),
            'is_encrypted': pdf_reader.is_encrypted,
            'has_metadata': pdf_reader.metadata is not None
        }
    except Exception as e:
        logger.error(f"Error getting PDF details: {e}")
        return {
            'success': False,
            'error': f"Error extracting details: {str(e)}"
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Password validation
    'validate_password_strength',
    'passwords_match',
    
    # PDF encryption/decryption
    'encrypt_pdf_with_password',
    'decrypt_pdf_with_password',
    'check_pdf_encryption_status',
    
    # QR code generation
    'generate_qr_code_for_unlock',
    
    # Token management
    'generate_unlock_token',
    'validate_unlock_token',
    'mark_token_as_used',
    'cleanup_expired_tokens',
    'get_token_expiry_info',
    
    # File operations
    'save_pdf_to_buffer',
    'generate_protected_filename',
    'generate_unlocked_filename',
    
    # Utilities
    'check_dependencies',
    'get_pdf_info',
]

