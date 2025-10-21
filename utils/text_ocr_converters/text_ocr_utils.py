"""
Text & OCR Processor Utilities
Helper functions for OCR processing, image enhancement, and text manipulation
"""

import os
import re
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Class for image preprocessing operations to improve OCR accuracy"""
    
    @staticmethod
    def resize_image(image: Image.Image, max_width: int = 3000, max_height: int = 3000) -> Image.Image:
        """
        Resize image if it's too large while maintaining aspect ratio
        
        Args:
            image: PIL Image object
            max_width: Maximum width allowed
            max_height: Maximum height allowed
            
        Returns:
            Resized PIL Image
        """
        width, height = image.size
        
        if width <= max_width and height <= max_height:
            return image
        
        # Calculate scaling factor
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def deskew_image(image: np.ndarray) -> np.ndarray:
        """
        Deskew a tilted image
        
        Args:
            image: Image as numpy array
            
        Returns:
            Deskewed image as numpy array
        """
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                gray = image.copy()
            
            # Apply threshold
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get the largest contour
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Get the minimum area rectangle
                rect = cv2.minAreaRect(largest_contour)
                angle = rect[2]
                
                # Correct the angle
                if angle < -45:
                    angle = 90 + angle
                    
                # Rotate the image
                if abs(angle) > 0.5:
                    center = (image.shape[1] // 2, image.shape[0] // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                    rotated = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]), 
                                           flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                    return rotated
            
            return image
        except Exception as e:
            logger.warning(f"Deskew failed: {str(e)}")
            return image
    
    @staticmethod
    def remove_noise(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        Remove noise from image using morphological operations
        
        Args:
            image: Image as numpy array
            kernel_size: Size of the kernel for morphological operations
            
        Returns:
            Denoised image as numpy array
        """
        try:
            # Apply morphological operations
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            
            # Opening - removes small white noise
            opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
            
            # Closing - removes small black noise
            closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
            
            return closed
        except Exception as e:
            logger.warning(f"Noise removal failed: {str(e)}")
            return image
    
    @staticmethod
    def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
        """
        Enhance image contrast
        
        Args:
            image: PIL Image object
            factor: Contrast enhancement factor
            
        Returns:
            Enhanced PIL Image
        """
        try:
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(factor)
        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {str(e)}")
            return image


class TextProcessor:
    """Class for text post-processing operations"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and fixing common issues
        
        Args:
            text: Raw OCR text
            
        Returns:
            Cleaned text
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove spaces before punctuation
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        # Add space after punctuation if missing
        text = re.sub(r'([.,!?;:])([A-Za-z])', r'\1 \2', text)
        
        # Fix common OCR mistakes
        replacements = {
            ' i ': ' I ',
            ' dont ': " don't ",
            ' wont ': " won't ",
            ' cant ': " can't ",
            ' ive ': " I've ",
            ' im ': " I'm ",
            ' youre ': " you're ",
            ' theyre ': " they're ",
            ' were ': " we're ",
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_paragraphs(text: str, min_length: int = 50) -> List[str]:
        """
        Extract paragraphs from text
        
        Args:
            text: Input text
            min_length: Minimum length for a valid paragraph
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\n+|\r\n\r\n+', text)
        
        # Filter out short paragraphs
        valid_paragraphs = []
        for para in paragraphs:
            para = para.strip()
            if len(para) >= min_length:
                valid_paragraphs.append(para)
        
        return valid_paragraphs
    
    @staticmethod
    def detect_text_structure(text: str) -> Dict[str, any]:
        """
        Detect structure in text (headers, lists, etc.)
        
        Args:
            text: Input text
            
        Returns:
            Dictionary containing structure information
        """
        structure = {
            'has_headers': False,
            'has_lists': False,
            'has_tables': False,
            'headers': [],
            'lists': []
        }
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detect headers (lines in all caps or with specific patterns)
            if line and (line.isupper() or re.match(r'^#{1,6}\s+', line) or 
                        re.match(r'^\d+\.\s+[A-Z]', line)):
                structure['has_headers'] = True
                structure['headers'].append({
                    'text': line,
                    'line_number': i + 1
                })
            
            # Detect lists
            if re.match(r'^[\*\-\+]\s+', line) or re.match(r'^\d+\.\s+', line):
                structure['has_lists'] = True
                structure['lists'].append({
                    'text': line,
                    'line_number': i + 1
                })
            
            # Simple table detection (lines with multiple | characters)
            if line.count('|') >= 2:
                structure['has_tables'] = True
        
        return structure


class OCRValidator:
    """Class for validating OCR results"""
    
    @staticmethod
    def calculate_confidence_metrics(confidence_scores: List[float]) -> Dict[str, float]:
        """
        Calculate various confidence metrics
        
        Args:
            confidence_scores: List of confidence scores
            
        Returns:
            Dictionary with confidence metrics
        """
        if not confidence_scores:
            return {
                'average': 0,
                'median': 0,
                'min': 0,
                'max': 0,
                'std_dev': 0
            }
        
        return {
            'average': np.mean(confidence_scores),
            'median': np.median(confidence_scores),
            'min': np.min(confidence_scores),
            'max': np.max(confidence_scores),
            'std_dev': np.std(confidence_scores)
        }
    
    @staticmethod
    def validate_text_quality(text: str, confidence: float) -> Dict[str, any]:
        """
        Validate the quality of extracted text
        
        Args:
            text: Extracted text
            confidence: Overall confidence score
            
        Returns:
            Dictionary with quality metrics and warnings
        """
        quality = {
            'is_valid': True,
            'warnings': [],
            'suggestions': []
        }
        
        # Check if text is too short
        if len(text) < 10:
            quality['warnings'].append('Extracted text is very short')
            quality['suggestions'].append('Ensure the image contains readable text')
        
        # Check confidence level
        if confidence < 70:
            quality['warnings'].append('Low confidence score')
            quality['suggestions'].append('Try enhancing image quality or resolution')
        
        # Check for excessive special characters (might indicate poor OCR)
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s.,!?;:\-]', text)) / len(text) if text else 0
        if special_char_ratio > 0.3:
            quality['warnings'].append('High proportion of special characters')
            quality['suggestions'].append('Check if the image is clear and properly oriented')
        
        # Check for common OCR errors
        common_errors = ['|', '\\', '~', '^', '{', '}', '[', ']']
        error_count = sum(text.count(char) for char in common_errors)
        if error_count > len(text) * 0.1:
            quality['warnings'].append('Possible OCR errors detected')
            quality['suggestions'].append('Consider manual review of the results')
        
        quality['is_valid'] = len(quality['warnings']) == 0
        
        return quality


class FileHandler:
    """Class for handling file operations"""
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, any]:
        """
        Get information about a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information
        """
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': os.path.splitext(file_path)[1].lower(),
                'exists': True
            }
        except:
            return {
                'size': 0,
                'size_mb': 0,
                'extension': '',
                'exists': False
            }
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
        """
        Validate file size
        
        Args:
            file_path: Path to the file
            max_size_mb: Maximum allowed size in MB
            
        Returns:
            Tuple of (is_valid, message)
        """
        info = FileHandler.get_file_info(file_path)
        
        if not info['exists']:
            return False, "File does not exist"
        
        if info['size_mb'] > max_size_mb:
            return False, f"File size ({info['size_mb']}MB) exceeds limit ({max_size_mb}MB)"
        
        return True, "File size is valid"


# Utility functions for language detection
def get_language_name(code: str) -> str:
    """
    Get full language name from language code
    
    Args:
        code: Language code (e.g., 'eng', 'hin')
        
    Returns:
        Full language name
    """
    language_map = {
        'eng': 'English',
        'hin': 'Hindi',
        'spa': 'Spanish',
        'fra': 'French',
        'deu': 'German',
        'ara': 'Arabic',
        'chi_sim': 'Chinese (Simplified)',
        'jpn': 'Japanese',
        'kor': 'Korean',
        'rus': 'Russian'
    }
    
    return language_map.get(code, 'Unknown')


def estimate_processing_time(file_size_mb: float, is_pdf: bool = False) -> int:
    """
    Estimate OCR processing time based on file size
    
    Args:
        file_size_mb: File size in megabytes
        is_pdf: Whether the file is a PDF
        
    Returns:
        Estimated time in seconds
    """
    # Base time per MB
    time_per_mb = 3 if not is_pdf else 5
    
    # Calculate estimated time
    estimated_time = int(file_size_mb * time_per_mb)
    
    # Add base processing time
    estimated_time += 2
    
    # Cap at reasonable maximum
    return min(estimated_time, 60)