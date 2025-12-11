"""
Professional File Management System for Cropio SaaS Platform
Implements secure file handling, validation, cleanup, and monitoring
"""
import os
import shutil
import hashlib
import magic
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from flask import current_app
from werkzeug.utils import secure_filename
from core.logging_config import cropio_logger


@dataclass
class FileInfo:
    """File information container"""
    filename: str
    filepath: str
    size: int
    mime_type: str
    extension: str
    hash_md5: str
    hash_sha256: str
    created_at: datetime
    is_safe: bool
    validation_errors: List[str]


class FileValidationError(Exception):
    """File validation error"""
    pass


class FileSizeExceededError(FileValidationError):
    """File size exceeded error"""
    pass


class FileTypeNotAllowedError(FileValidationError):
    """File type not allowed error"""
    pass


class MaliciousFileError(FileValidationError):
    """Malicious file detected error"""
    pass


class FileSecurityValidator:
    """Advanced file security validation"""
    
    # Dangerous file signatures (magic numbers)
    DANGEROUS_SIGNATURES = {
        # Executable files
        b'MZ': 'Windows executable',
        b'\x7fELF': 'Linux executable',
        b'\xca\xfe\xba\xbe': 'Mach-O executable',
        b'\xfe\xed\xfa\xce': 'Mach-O executable',
        
        # Scripts and potentially dangerous files
        b'#!/bin/sh': 'Shell script',
        b'#!/bin/bash': 'Bash script',
        b'#!/usr/bin/python': 'Python script',
        b'<?php': 'PHP script',
        b'<script': 'JavaScript/HTML script',
    }
    
    # Dangerous file patterns
    DANGEROUS_PATTERNS = [
        b'<?php',
        b'<script',
        b'<iframe',
        b'javascript:',
        b'vbscript:',
        b'onerror=',
        b'onclick=',
        b'onload=',
        b'eval(',
        b'exec(',
        b'system(',
        b'shell_exec(',
        b'passthru(',
        b'base64_decode(',
    ]
    
    def __init__(self):
        self.mime_checker = magic.Magic(mime=True)
        self.file_checker = magic.Magic()
    
    def validate_file_signature(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate file signature against known dangerous patterns"""
        errors = []
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)  # Read first 1KB
            
            # Check for dangerous signatures
            for signature, description in self.DANGEROUS_SIGNATURES.items():
                if header.startswith(signature):
                    errors.append(f"Dangerous file signature detected: {description}")
            
            # Check for dangerous patterns
            header_lower = header.lower()
            for pattern in self.DANGEROUS_PATTERNS:
                if pattern in header_lower:
                    errors.append(f"Potentially malicious pattern detected: {pattern.decode('utf-8', errors='ignore')}")
            
        except Exception as e:
            cropio_logger.error(f"Error validating file signature: {e}")
            errors.append("Unable to validate file signature")
        
        return len(errors) == 0, errors
    
    def validate_mime_type(self, file_path: str, allowed_extensions: set) -> Tuple[bool, List[str]]:
        """Validate MIME type matches file extension"""
        errors = []
        
        try:
            detected_mime = self.mime_checker.from_file(file_path)
            file_extension = Path(file_path).suffix.lower()[1:]  # Remove dot
            
            # MIME type mappings for common file types
            mime_mappings = {
                'pdf': ['application/pdf'],
                'png': ['image/png'],
                'jpg': ['image/jpeg'],
                'jpeg': ['image/jpeg'],
                'gif': ['image/gif'],
                'webp': ['image/webp'],
                'bmp': ['image/bmp', 'image/x-ms-bmp'],
                'tiff': ['image/tiff'],
                'tif': ['image/tiff'],
                'svg': ['image/svg+xml'],
                'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
                'doc': ['application/msword'],
                'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
                'xls': ['application/vnd.ms-excel'],
                'pptx': ['application/vnd.openxmlformats-officedocument.presentationml.presentation'],
                'ppt': ['application/vnd.ms-powerpoint'],
                'txt': ['text/plain'],
                'csv': ['text/csv', 'text/plain'],
                'zip': ['application/zip'],
                'rar': ['application/x-rar-compressed'],
                'mp4': ['video/mp4'],
                'avi': ['video/x-msvideo'],
                'mp3': ['audio/mpeg'],
                'wav': ['audio/wav', 'audio/x-wav'],
            }
            
            if file_extension in allowed_extensions:
                expected_mimes = mime_mappings.get(file_extension, [])
                if expected_mimes and detected_mime not in expected_mimes:
                    errors.append(f"MIME type mismatch: expected {expected_mimes}, got {detected_mime}")
            
        except Exception as e:
            cropio_logger.warning(f"MIME type validation failed: {e}")
            # Don't fail validation for MIME type issues, just log warning
        
        return len(errors) == 0, errors
    
    def scan_for_embedded_files(self, file_path: str) -> Tuple[bool, List[str]]:
        """Scan for embedded executable files or scripts"""
        errors = []
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Look for embedded executables
            for signature, description in self.DANGEROUS_SIGNATURES.items():
                # Check if signature appears anywhere in the file (not just header)
                if signature in content[100:]:  # Skip first 100 bytes to avoid false positives
                    errors.append(f"Embedded {description} detected")
            
            # Check for suspicious base64 patterns (potential payload)
            import base64
            import re
            
            base64_pattern = re.compile(rb'[A-Za-z0-9+/]{50,}={0,2}')
            matches = base64_pattern.findall(content)
            
            for match in matches[:5]:  # Check first 5 matches
                try:
                    decoded = base64.b64decode(match)
                    # Check if decoded content contains dangerous patterns
                    for pattern in self.DANGEROUS_PATTERNS:
                        if pattern in decoded.lower():
                            errors.append("Suspicious base64 encoded content detected")
                            break
                except:
                    continue
            
        except Exception as e:
            cropio_logger.warning(f"Embedded file scan failed: {e}")
        
        return len(errors) == 0, errors


class FileManager:
    """Professional file management system"""
    
    def __init__(self, app=None):
        self.app = app
        self.validator = FileSecurityValidator()
        self.upload_folder = None
        self.max_file_size = 100 * 1024 * 1024  # 100MB default
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize file manager with Flask app"""
        self.app = app
        self.upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        self.max_file_size = app.config.get('MAX_CONTENT_LENGTH', 100 * 1024 * 1024)
        
        # Ensure upload directory exists
        os.makedirs(self.upload_folder, exist_ok=True)
        
        cropio_logger.info(f"File manager initialized: {self.upload_folder}")
    
    def calculate_file_hashes(self, file_path: str) -> Dict[str, str]:
        """Calculate MD5 and SHA256 hashes for file"""
        md5_hash = hashlib.md5()
        sha256_hash = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
                sha256_hash.update(chunk)
        
        return {
            'md5': md5_hash.hexdigest(),
            'sha256': sha256_hash.hexdigest()
        }
    
    def validate_file(self, file_obj, allowed_extensions: set, 
                     max_size: Optional[int] = None) -> FileInfo:
        """Comprehensive file validation"""
        if not file_obj or not file_obj.filename:
            raise FileValidationError("No file provided")
        
        # Secure the filename
        original_filename = file_obj.filename
        safe_filename = secure_filename(original_filename)
        
        if not safe_filename:
            raise FileValidationError("Invalid filename")
        
        # Check file extension
        file_extension = Path(safe_filename).suffix.lower()[1:]  # Remove dot
        if file_extension not in allowed_extensions:
            raise FileTypeNotAllowedError(
                f"File type '.{file_extension}' not allowed. "
                f"Allowed types: {', '.join(sorted(allowed_extensions))}"
            )
        
        # Save file temporarily for validation
        temp_filename = f"temp_{int(time.time())}_{safe_filename}"
        temp_path = os.path.join(self.upload_folder, temp_filename)
        
        try:
            file_obj.save(temp_path)
            
            # Get file size
            file_size = os.path.getsize(temp_path)
            
            # Check file size
            max_size = max_size or self.max_file_size
            if file_size > max_size:
                raise FileSizeExceededError(
                    f"File size ({file_size} bytes) exceeds maximum allowed "
                    f"size ({max_size} bytes)"
                )
            
            # Get MIME type
            try:
                mime_type = self.validator.mime_checker.from_file(temp_path)
            except Exception:
                mime_type = "unknown"
            
            # Calculate file hashes
            hashes = self.calculate_file_hashes(temp_path)
            
            # Security validation
            validation_errors = []
            is_safe = True
            
            # Validate file signature
            sig_safe, sig_errors = self.validator.validate_file_signature(temp_path)
            if not sig_safe:
                is_safe = False
                validation_errors.extend(sig_errors)
            
            # Validate MIME type
            mime_safe, mime_errors = self.validator.validate_mime_type(temp_path, allowed_extensions)
            if not mime_safe:
                validation_errors.extend(mime_errors)
                # MIME type mismatches are warnings, not blocking errors
            
            # Scan for embedded files
            embed_safe, embed_errors = self.validator.scan_for_embedded_files(temp_path)
            if not embed_safe:
                is_safe = False
                validation_errors.extend(embed_errors)
            
            if not is_safe:
                raise MaliciousFileError(f"File failed security validation: {'; '.join(validation_errors)}")
            
            # Create FileInfo object
            file_info = FileInfo(
                filename=safe_filename,
                filepath=temp_path,
                size=file_size,
                mime_type=mime_type,
                extension=file_extension,
                hash_md5=hashes['md5'],
                hash_sha256=hashes['sha256'],
                created_at=datetime.utcnow(),
                is_safe=is_safe,
                validation_errors=validation_errors
            )
            
            # Log file validation
            cropio_logger.info(
                f"File validated successfully: {safe_filename}",
                extra_data={
                    'filename': safe_filename,
                    'size': file_size,
                    'mime_type': mime_type,
                    'extension': file_extension,
                    'md5': hashes['md5'],
                    'validation_warnings': validation_errors
                }
            )
            
            return file_info
            
        except (FileValidationError, MaliciousFileError):
            # Clean up temp file on validation failure
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        except Exception as e:
            # Clean up temp file on any error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            cropio_logger.error(f"Unexpected error during file validation: {e}", exc_info=True)
            raise FileValidationError(f"File validation failed: {str(e)}")
    
    def move_validated_file(self, file_info: FileInfo, 
                           destination_folder: str) -> str:
        """Move validated file to destination folder"""
        if not file_info.is_safe:
            raise MaliciousFileError("Cannot move unsafe file")
        
        # Create destination folder if it doesn't exist
        os.makedirs(destination_folder, exist_ok=True)
        
        # Generate unique filename to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{file_info.hash_md5[:8]}_{file_info.filename}"
        destination_path = os.path.join(destination_folder, unique_filename)
        
        # Move file
        shutil.move(file_info.filepath, destination_path)
        
        cropio_logger.info(
            f"File moved to destination: {unique_filename}",
            extra_data={
                'original_path': file_info.filepath,
                'destination_path': destination_path,
                'filename': file_info.filename
            }
        )
        
        return destination_path
    
    def cleanup_old_files(self, folder_path: str, max_age_hours: int = 24) -> Dict[str, int]:
        """Clean up old files from specified folder"""
        if not os.path.exists(folder_path):
            return {'deleted': 0, 'errors': 0}
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cutoff_timestamp = cutoff_time.timestamp()
        
        deleted_count = 0
        error_count = 0
        total_size_freed = 0
        
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                if not os.path.isfile(file_path):
                    continue
                
                try:
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_timestamp:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        total_size_freed += file_size
                        
                        cropio_logger.info(
                            f"Cleaned up old file: {filename}",
                            extra_data={
                                'file_path': file_path,
                                'file_size': file_size,
                                'age_hours': (time.time() - file_mtime) / 3600
                            }
                        )
                        
                except Exception as e:
                    error_count += 1
                    cropio_logger.error(f"Error deleting file {file_path}: {e}")
        
        except Exception as e:
            cropio_logger.error(f"Error during cleanup of {folder_path}: {e}")
            error_count += 1
        
        result = {
            'deleted': deleted_count,
            'errors': error_count,
            'size_freed': total_size_freed
        }
        
        if deleted_count > 0:
            cropio_logger.info(
                f"Cleanup completed for {folder_path}",
                extra_data=result
            )
        
        return result
    
    def get_folder_stats(self, folder_path: str) -> Dict[str, Union[int, float]]:
        """Get statistics for a folder"""
        if not os.path.exists(folder_path):
            return {'files': 0, 'total_size': 0, 'avg_file_size': 0}
        
        file_count = 0
        total_size = 0
        
        try:
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                if os.path.isfile(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)
        
        except Exception as e:
            cropio_logger.error(f"Error getting folder stats for {folder_path}: {e}")
        
        return {
            'files': file_count,
            'total_size': total_size,
            'avg_file_size': total_size / file_count if file_count > 0 else 0
        }
    
    def quarantine_file(self, file_path: str, reason: str) -> str:
        """Move suspicious file to quarantine folder"""
        quarantine_folder = os.path.join(self.upload_folder, 'quarantine')
        os.makedirs(quarantine_folder, exist_ok=True)
        
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        quarantine_filename = f"quarantine_{timestamp}_{filename}"
        quarantine_path = os.path.join(quarantine_folder, quarantine_filename)
        
        # Move file to quarantine
        shutil.move(file_path, quarantine_path)
        
        # Log quarantine action
        cropio_logger.security_event(
            'file_quarantined',
            f"File quarantined: {filename}",
            extra_data={
                'original_path': file_path,
                'quarantine_path': quarantine_path,
                'reason': reason,
                'filename': filename
            }
        )
        
        return quarantine_path


# Global file manager instance
file_manager = FileManager()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.1f} PB"


def is_file_type_allowed(filename: str, allowed_extensions: set) -> bool:
    """Check if file type is allowed"""
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def generate_secure_filename(original_filename: str, user_id: int = None) -> str:
    """Generate secure filename with timestamp and user ID"""
    safe_name = secure_filename(original_filename)
    name, ext = os.path.splitext(safe_name)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = hashlib.md5(f"{original_filename}{time.time()}".encode()).hexdigest()[:8]
    
    if user_id:
        return f"{timestamp}_{user_id}_{random_suffix}_{name}{ext}"
    else:
        return f"{timestamp}_{random_suffix}_{name}{ext}"
