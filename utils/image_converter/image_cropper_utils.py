# utils/image_converter/image_cropper_utils.py - IMAGE CROPPER UTILITIES
# Dedicated utilities for image cropping functionality
import os
import tempfile
import shutil
import json
import math
from pathlib import Path
import logging
from typing import List, Optional, Tuple, Dict, Any, Union

# Universal Security Framework Integration
try:
    from security.core.validators import validate_content, validate_filename
    from security.core.sanitizers import sanitize_filename
    SECURITY_FRAMEWORK_AVAILABLE = True
except ImportError:
    SECURITY_FRAMEWORK_AVAILABLE = False

# Image processing dependencies
try:
    from PIL import Image, ImageDraw, ImageFilter, ImageOps, ExifTags
    from PIL.ImageFile import LOAD_TRUNCATED_IMAGES
    PIL_AVAILABLE = True
    # Enable loading of truncated images
    LOAD_TRUNCATED_IMAGES = True
except ImportError:
    PIL_AVAILABLE = False

# Additional image processing libraries
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageCropper:
    """
    Dedicated image cropper supporting:
    - Free crop mode
    - Fixed aspect ratio cropping
    - Shape cropping (circle, rounded corners)
    - Batch processing
    - Multiple output formats
    - Quality control
    """
    
    def __init__(self):
        self.temp_dirs = []  # Track temporary directories for cleanup
        
        # Check for required dependencies
        self.dependencies = self._check_dependencies()
        
        # Supported formats
        self.input_formats = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp', 'gif'}
        self.output_formats = {'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'gif'}
        
        # Default settings
        self.default_quality = 85
        self.max_dimension = 10000  # Maximum width/height for safety
        
    def __del__(self):
        """Cleanup temporary directories on object destruction"""
        self.cleanup_temp_dirs()
        
    def cleanup_temp_dirs(self):
        """Clean up all temporary directories created by this instance"""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp dir {temp_dir}: {e}")
        self.temp_dirs.clear()
    
    def _check_dependencies(self) -> Dict[str, bool]:
        """Check availability of all dependencies"""
        return {
            'pil': PIL_AVAILABLE,
            'opencv': OPENCV_AVAILABLE
        }
    
    def is_format_supported(self, format_name: str) -> bool:
        """Check if image format is supported"""
        return format_name.lower() in self.output_formats
    
    def is_shape_cropping_available(self) -> bool:
        """Check if shape cropping is available"""
        return self.dependencies['pil']
    
    def validate_file_security(self, file_path: str) -> Tuple[bool, List[str]]:
        """Validate file using universal security framework"""
        if not SECURITY_FRAMEWORK_AVAILABLE:
            logger.warning("Security framework not available - performing basic validation")
            return self._basic_file_validation(file_path)
        
        try:
            # Read file content for security validation
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Determine file type
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            
            # Perform security validation
            is_safe, issues = validate_content(file_content, file_ext)
            
            if not is_safe:
                logger.error(f"Security validation failed for {file_path}: {issues}")
                return False, issues
            
            logger.info(f"Security validation passed for {file_path}")
            return True, []
            
        except Exception as e:
            logger.error(f"Security validation error for {file_path}: {e}")
            return False, [f"Security validation error: {str(e)}"]
    
    def _basic_file_validation(self, file_path: str) -> Tuple[bool, List[str]]:
        """Basic file validation when security framework is not available"""
        try:
            if not os.path.exists(file_path):
                return False, ["File does not exist"]
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, ["File is empty"]
            
            if file_size > 100 * 1024 * 1024:  # 100MB limit
                return False, ["File too large"]
            
            # Try to open as image
            try:
                with Image.open(file_path) as img:
                    # Basic image validation
                    img.verify()  # Verify it's a valid image
                
                # Reopen for additional checks (verify() invalidates the image)
                with Image.open(file_path) as img:
                    if img.width <= 0 or img.height <= 0:
                        return False, ["Invalid image dimensions"]
                    
                    if img.width > self.max_dimension or img.height > self.max_dimension:
                        return False, [f"Image dimensions too large (max: {self.max_dimension}x{self.max_dimension})"]
                    
            except Exception as e:
                return False, [f"Invalid image file: {str(e)}"]
            
            return True, []
            
        except Exception as e:
            return False, [f"Basic validation error: {str(e)}"]
    
    def _load_image(self, input_path: str) -> Optional[Image.Image]:
        """Load and validate image file"""
        try:
            if not PIL_AVAILABLE:
                logger.error("PIL not available for image processing")
                return None
            
            # Open and verify image
            with Image.open(input_path) as img:
                # Handle EXIF orientation
                img = ImageOps.exif_transpose(img)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # For formats that support transparency, preserve it for PNG
                    if input_path.lower().endswith('.png'):
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                    else:
                        # Convert to RGB for other formats
                        if img.mode == 'RGBA':
                            # Create white background
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                            img = background
                        else:
                            img = img.convert('RGB')
                elif img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                # Create a copy to avoid issues with file handles
                return img.copy()
                
        except Exception as e:
            logger.error(f"Failed to load image {input_path}: {e}")
            return None
    
    def _calculate_crop_box(self, img: Image.Image, crop_options: Dict) -> Tuple[int, int, int, int]:
        """Calculate crop box coordinates based on options"""
        width, height = img.size
        
        # Default to full image
        left, top, right, bottom = 0, 0, width, height
        
        crop_mode = crop_options.get('crop_mode', 'free')
        crop_data = crop_options.get('crop_data')
        
        # Use crop data from frontend if available
        if crop_data and isinstance(crop_data, dict):
            try:
                # Crop data from Cropper.js: {x, y, width, height, rotate, scaleX, scaleY}
                x = crop_data.get('x', 0)
                y = crop_data.get('y', 0)
                crop_width = crop_data.get('width', width)
                crop_height = crop_data.get('height', height)
                
                left = max(0, int(x))
                top = max(0, int(y))
                right = min(width, int(x + crop_width))
                bottom = min(height, int(y + crop_height))
                
                logger.info(f"Using frontend crop data: ({left}, {top}, {right}, {bottom})")
                return left, top, right, bottom
                
            except Exception as e:
                logger.warning(f"Invalid crop data, falling back to automatic cropping: {e}")
        
        # Automatic cropping based on mode
        if crop_mode == 'aspect':
            aspect_ratio = crop_options.get('aspect_ratio', '1:1')
            target_ratio = self._parse_aspect_ratio(aspect_ratio)
            
            if target_ratio:
                # Calculate crop box to match aspect ratio
                current_ratio = width / height
                
                if current_ratio > target_ratio:
                    # Image is wider than target ratio, crop width
                    new_width = int(height * target_ratio)
                    left = (width - new_width) // 2
                    right = left + new_width
                else:
                    # Image is taller than target ratio, crop height
                    new_height = int(width / target_ratio)
                    top = (height - new_height) // 2
                    bottom = top + new_height
        
        elif crop_mode == 'free':
            # Use custom dimensions if provided
            custom_width = crop_options.get('custom_width')
            custom_height = crop_options.get('custom_height')
            center_crop = crop_options.get('center_crop', True)
            
            if custom_width or custom_height:
                if custom_width:
                    crop_width = min(int(custom_width), width)
                    if center_crop:
                        left = (width - crop_width) // 2
                        right = left + crop_width
                    else:
                        right = min(crop_width, width)
                
                if custom_height:
                    crop_height = min(int(custom_height), height)
                    if center_crop:
                        top = (height - crop_height) // 2
                        bottom = top + crop_height
                    else:
                        bottom = min(crop_height, height)
        
        # Ensure crop box is within image bounds
        left = max(0, min(left, width - 1))
        top = max(0, min(top, height - 1))
        right = min(width, max(right, left + 1))
        bottom = min(height, max(bottom, top + 1))
        
        logger.info(f"Calculated crop box: ({left}, {top}, {right}, {bottom})")
        return left, top, right, bottom
    
    def _parse_aspect_ratio(self, aspect_str: str) -> Optional[float]:
        """Parse aspect ratio string like '16:9' into float"""
        try:
            if ':' in aspect_str:
                w, h = aspect_str.split(':')
                return float(w) / float(h)
            else:
                return float(aspect_str)
        except ValueError:
            logger.warning(f"Invalid aspect ratio: {aspect_str}")
            return None
    
    def _apply_shape_crop(self, img: Image.Image, crop_shape: str) -> Image.Image:
        """Apply shape-based cropping (circle, rounded corners)"""
        if crop_shape == 'circle':
            return self._create_circular_crop(img)
        elif crop_shape == 'rounded':
            return self._create_rounded_crop(img)
        else:
            return img  # Rectangle (default)
    
    def _create_circular_crop(self, img: Image.Image) -> Image.Image:
        """Create circular crop"""
        try:
            # Make image square first
            size = min(img.size)
            left = (img.width - size) // 2
            top = (img.height - size) // 2
            img = img.crop((left, top, left + size, top + size))
            
            # Create circular mask
            mask = Image.new('L', (size, size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, size, size), fill=255)
            
            # Apply mask
            img.putalpha(mask)
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to create circular crop: {e}")
            return img
    
    def _create_rounded_crop(self, img: Image.Image, radius: int = 20) -> Image.Image:
        """Create rounded corners crop"""
        try:
            # Create mask with rounded corners
            mask = Image.new('L', img.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            
            # Draw rounded rectangle
            width, height = img.size
            mask_draw.rounded_rectangle(
                [(0, 0), (width, height)], 
                radius=radius, 
                fill=255
            )
            
            # Apply mask
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            img.putalpha(mask)
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to create rounded crop: {e}")
            return img
    
    def _save_image(self, img: Image.Image, output_path: str, 
                   output_format: str, quality: int = 85) -> bool:
        """Save image with specified format and quality"""
        try:
            # Prepare save options
            save_kwargs = {}
            
            # Handle format-specific options
            if output_format.lower() in ['jpg', 'jpeg']:
                # Convert to RGB if necessary for JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparent images
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                save_kwargs.update({
                    'format': 'JPEG',
                    'quality': quality,
                    'optimize': True
                })
            
            elif output_format.lower() == 'png':
                save_kwargs.update({
                    'format': 'PNG',
                    'optimize': True
                })
            
            elif output_format.lower() == 'webp':
                save_kwargs.update({
                    'format': 'WEBP',
                    'quality': quality,
                    'method': 6  # Best compression method
                })
            
            elif output_format.lower() == 'bmp':
                # Convert to RGB for BMP
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                save_kwargs.update({'format': 'BMP'})
            
            elif output_format.lower() in ['tiff', 'tif']:
                save_kwargs.update({
                    'format': 'TIFF',
                    'compression': 'lzw'  # Use LZW compression
                })
            
            elif output_format.lower() == 'gif':
                # Convert to P mode for GIF
                if img.mode == 'RGBA':
                    # Handle transparency
                    img = img.convert('P', palette=Image.ADAPTIVE, colors=255)
                elif img.mode != 'P':
                    img = img.convert('P', palette=Image.ADAPTIVE)
                save_kwargs.update({'format': 'GIF'})
            
            else:
                # Default to JPEG
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    img = background
                
                save_kwargs.update({
                    'format': 'JPEG',
                    'quality': quality,
                    'optimize': True
                })
            
            # Save image
            img.save(output_path, **save_kwargs)
            
            # Verify the saved file
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"Successfully saved image: {output_path}")
                return True
            else:
                logger.error(f"Failed to save image or file is empty: {output_path}")
                return False
            
        except Exception as e:
            logger.error(f"Error saving image {output_path}: {e}")
            return False
    
    def crop_image(self, input_path: str, output_path: str, **crop_options) -> bool:
        """
        Crop a single image with specified options
        
        Args:
            input_path: Path to input image
            output_path: Path to save cropped image
            **crop_options: Cropping options including:
                - crop_mode: 'free', 'aspect', 'shape'
                - aspect_ratio: '1:1', '4:3', '16:9', '3:2'
                - crop_shape: 'rectangle', 'circle', 'rounded'
                - custom_width: Custom width in pixels
                - custom_height: Custom height in pixels
                - maintain_aspect: Boolean to maintain aspect ratio
                - center_crop: Boolean to center the crop
                - output_format: Output format ('jpg', 'png', etc.)
                - quality: Quality percentage (1-100)
                - crop_data: Crop data from frontend
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate input
            if not PIL_AVAILABLE:
                logger.error("PIL not available for image cropping")
                return False
            
            # Validate file security
            is_safe, security_issues = self.validate_file_security(input_path)
            if not is_safe:
                logger.error(f"Security validation failed: {security_issues}")
                return False
            
            # Load image
            img = self._load_image(input_path)
            if img is None:
                logger.error(f"Failed to load image: {input_path}")
                return False
            
            logger.info(f"Loaded image: {img.size[0]}x{img.size[1]} ({img.mode})")
            
            # Calculate crop box
            left, top, right, bottom = self._calculate_crop_box(img, crop_options)
            
            # Apply crop
            cropped_img = img.crop((left, top, right, bottom))
            logger.info(f"Cropped to: {cropped_img.size[0]}x{cropped_img.size[1]}")
            
            # Apply shape cropping if specified
            crop_shape = crop_options.get('crop_shape', 'rectangle')
            if crop_shape != 'rectangle':
                cropped_img = self._apply_shape_crop(cropped_img, crop_shape)
                logger.info(f"Applied {crop_shape} shape cropping")
            
            # Save cropped image
            output_format = crop_options.get('output_format', 'jpg')
            quality = crop_options.get('quality', self.default_quality)
            
            success = self._save_image(cropped_img, output_path, output_format, quality)
            
            # Clean up
            img.close()
            cropped_img.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Image cropping failed: {e}")
            return False
    
    def crop_images_batch(self, input_paths: List[str], output_dir: str, **crop_options) -> Dict:
        """
        Crop multiple images with the same settings
        
        Args:
            input_paths: List of input image paths
            output_dir: Directory to save cropped images
            **crop_options: Same as crop_image method
        
        Returns:
            Dict with success status and results
        """
        try:
            results = {
                'success': True,
                'processed': [],
                'failed': [],
                'total': len(input_paths)
            }
            
            os.makedirs(output_dir, exist_ok=True)
            
            for input_path in input_paths:
                try:
                    # Generate output filename
                    input_filename = os.path.basename(input_path)
                    name, ext = os.path.splitext(input_filename)
                    
                    output_format = crop_options.get('output_format', 'jpg')
                    output_ext = f".{output_format}"
                    output_filename = f"{name}_cropped{output_ext}"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Crop image
                    if self.crop_image(input_path, output_path, **crop_options):
                        results['processed'].append({
                            'input': input_path,
                            'output': output_path,
                            'filename': output_filename
                        })
                        logger.info(f"Successfully cropped: {input_filename}")
                    else:
                        results['failed'].append({
                            'input': input_path,
                            'error': 'Cropping failed'
                        })
                        logger.error(f"Failed to crop: {input_filename}")
                        
                except Exception as e:
                    results['failed'].append({
                        'input': input_path,
                        'error': str(e)
                    })
                    logger.error(f"Error processing {input_path}: {e}")
            
            # Set overall success status
            results['success'] = len(results['processed']) > 0
            
            logger.info(f"Batch cropping completed: {len(results['processed'])}/{results['total']} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch cropping failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed': [],
                'failed': input_paths,
                'total': len(input_paths)
            }
    
    def get_image_info(self, input_path: str) -> Optional[Dict]:
        """Get basic information about an image"""
        try:
            img = self._load_image(input_path)
            if img is None:
                return None
            
            info = {
                'width': img.width,
                'height': img.height,
                'mode': img.mode,
                'format': img.format,
                'size_bytes': os.path.getsize(input_path),
                'has_transparency': img.mode in ('RGBA', 'LA', 'P') and 'transparency' in img.info
            }
            
            # Get EXIF data if available
            try:
                exif = img._getexif()
                if exif:
                    info['exif'] = {
                        ExifTags.TAGS.get(k, k): v for k, v in exif.items()
                        if k in ExifTags.TAGS
                    }
            except (AttributeError, OSError):
                pass
            
            img.close()
            return info
            
        except Exception as e:
            logger.error(f"Failed to get image info for {input_path}: {e}")
            return None
    
    def validate_crop_options(self, crop_options: Dict) -> Tuple[bool, List[str]]:
        """Validate crop options"""
        errors = []
        
        # Validate crop mode
        crop_mode = crop_options.get('crop_mode', 'free')
        if crop_mode not in ['free', 'aspect', 'shape']:
            errors.append(f"Invalid crop mode: {crop_mode}")
        
        # Validate aspect ratio
        if crop_mode == 'aspect':
            aspect_ratio = crop_options.get('aspect_ratio')
            if not aspect_ratio or not self._parse_aspect_ratio(aspect_ratio):
                errors.append(f"Invalid aspect ratio: {aspect_ratio}")
        
        # Validate crop shape
        if crop_mode == 'shape':
            crop_shape = crop_options.get('crop_shape', 'rectangle')
            if crop_shape not in ['rectangle', 'circle', 'rounded']:
                errors.append(f"Invalid crop shape: {crop_shape}")
        
        # Validate dimensions
        custom_width = crop_options.get('custom_width')
        custom_height = crop_options.get('custom_height')
        
        if custom_width is not None:
            try:
                width = int(custom_width)
                if width <= 0 or width > self.max_dimension:
                    errors.append(f"Invalid width: {width}")
            except ValueError:
                errors.append(f"Invalid width value: {custom_width}")
        
        if custom_height is not None:
            try:
                height = int(custom_height)
                if height <= 0 or height > self.max_dimension:
                    errors.append(f"Invalid height: {height}")
            except ValueError:
                errors.append(f"Invalid height value: {custom_height}")
        
        # Validate output format
        output_format = crop_options.get('output_format', 'jpg')
        if not self.is_format_supported(output_format):
            errors.append(f"Unsupported output format: {output_format}")
        
        # Validate quality
        quality = crop_options.get('quality', 85)
        try:
            quality_int = int(quality)
            if quality_int < 1 or quality_int > 100:
                errors.append(f"Quality must be between 1-100: {quality}")
        except ValueError:
            errors.append(f"Invalid quality value: {quality}")
        
        return len(errors) == 0, errors