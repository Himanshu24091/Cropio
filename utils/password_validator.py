"""
Password Strength Validator Utility
Centralized password validation logic for checking password strength
"""
import re
from typing import Dict, List


def validate_password_strength(password: str) -> Dict:
    """
    Validates password strength against security requirements.
    
    Args:
        password (str): The password to validate
        
    Returns:
        dict: {
            'is_strong': bool - Whether password meets all requirements,
            'score': int - Number of requirements met (0-5),
            'missing_requirements': list - List of unmet requirements,
            'met_requirements': list - List of met requirements,
            'details': dict - Detailed check results
        }
    """
    if not password:
        return {
            'is_strong': False,
            'score': 0,
            'missing_requirements': ['Password is required'],
            'met_requirements': [],
            'details': {}
        }
    
    # Check each requirement
    requirements = {
        'length': {
            'met': len(password) >= 8,
            'message': 'At least 8 characters'
        },
        'lowercase': {
            'met': bool(re.search(r'[a-z]', password)),
            'message': 'One lowercase letter (a-z)'
        },
        'uppercase': {
            'met': bool(re.search(r'[A-Z]', password)),
            'message': 'One uppercase letter (A-Z)'
        },
        'number': {
            'met': bool(re.search(r'[0-9]', password)),
            'message': 'One number (0-9)'
        },
        'special': {
            'met': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            'message': 'One special character (!@#$%^&*)'
        }
    }
    
    # Calculate score and categorize requirements
    met_requirements = []
    missing_requirements = []
    
    for key, req in requirements.items():
        if req['met']:
            met_requirements.append(req['message'])
        else:
            missing_requirements.append(req['message'])
    
    score = len(met_requirements)
    is_strong = score == 5  # All requirements must be met
    
    return {
        'is_strong': is_strong,
        'score': score,
        'missing_requirements': missing_requirements,
        'met_requirements': met_requirements,
        'details': requirements
    }


def get_password_strength_level(score: int) -> str:
    """
    Get password strength level based on score.
    
    Args:
        score (int): Password strength score (0-5)
        
    Returns:
        str: 'weak', 'medium', or 'strong'
    """
    if score >= 5:
        return 'strong'
    elif score >= 3:
        return 'medium'
    else:
        return 'weak'


def format_password_errors(validation_result: Dict) -> List[str]:
    """
    Format validation result into user-friendly error messages.
    
    Args:
        validation_result (dict): Result from validate_password_strength()
        
    Returns:
        list: List of error messages
    """
    if validation_result['is_strong']:
        return []
    
    errors = []
    if validation_result['missing_requirements']:
        errors.append('Password must contain:')
        for req in validation_result['missing_requirements']:
            errors.append(f'  • {req}')
    
    return errors
