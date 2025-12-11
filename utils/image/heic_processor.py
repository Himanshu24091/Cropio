"""
HEIC ⇄ JPG Processor Utility
Handles Apple HEIC image format conversion
"""

import os
import uuid
from PIL import Image
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

class HEICProcessor:
    """Utility class for HEIC and JPG processing"""
    
    def __init__(self):
        self.upload_folder = 'uploads'
        
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def heic_to_jpg(self, input_path, quality=95):
        """Convert HEIC file to JPG"""
        if not HEIF_AVAILABLE:
            raise Exception("HEIC support requires pillow-heif library. Install with: pip install pillow-heif")
            
        try:
            # Open HEIC image
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (HEIC might be in different color space)
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Generate output filename
                output_filename = f"{uuid.uuid4().hex}_converted.jpg"
                output_path = os.path.join(self.upload_folder, output_filename)
                
                # Save as JPG with specified quality
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                
                return output_path
                
        except Exception as e:
            raise Exception(f"HEIC to JPG conversion failed: {str(e)}")
    
    def jpg_to_heic(self, input_path, quality=80):
        """Convert JPG file to HEIC (if system supports it)"""
        try:
            # Check if HEIF is available for encoding
            if not HEIF_AVAILABLE:
                raise Exception("HEIC encoding requires pillow-heif library. Install with: pip install pillow-heif")
            
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Try to save as HEIC first
                try:
                    # Generate HEIC output filename
                    output_filename = f"{uuid.uuid4().hex}_converted.heic"
                    output_path = os.path.join(self.upload_folder, output_filename)
                    
                    # Save as HEIC format
                    img.save(output_path, 'HEIF', quality=quality, optimize=True)
                    
                    # Verify the file was actually created as HEIC
                    if os.path.exists(output_path):
                        return output_path
                    else:
                        raise Exception("HEIC file creation failed")
                        
                except Exception as heic_error:
                    # Fallback to high-quality JPG if HEIC encoding fails
                    output_filename = f"{uuid.uuid4().hex}_heic_fallback.jpg"
                    output_path = os.path.join(self.upload_folder, output_filename)
                    
                    # Save as high-quality JPG with notice
                    img.save(output_path, 'JPEG', quality=min(quality + 10, 100), optimize=True)
                    
                    # Log the fallback
                    print(f"Warning: HEIC encoding failed ({heic_error}), saved as high-quality JPG instead")
                    return output_path
                
        except Exception as e:
            raise Exception(f"JPG to HEIC conversion failed: {str(e)}")
    
    def convert_heic_with_metadata(self, input_path, output_format='JPEG', quality=95):
        """Convert HEIC with metadata preservation"""
        try:
            with Image.open(input_path) as img:
                # Preserve EXIF data
                exif = img.getexif()
                
                # Convert color mode if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Generate output filename
                ext = 'jpg' if output_format == 'JPEG' else output_format.lower()
                output_filename = f"{uuid.uuid4().hex}_converted.{ext}"
                output_path = os.path.join(self.upload_folder, output_filename)
                
                # Save with metadata
                save_kwargs = {
                    'format': output_format,
                    'quality': quality,
                    'optimize': True
                }
                
                if exif:
                    save_kwargs['exif'] = exif
                
                img.save(output_path, **save_kwargs)
                
                return output_path
                
        except Exception as e:
            raise Exception(f"HEIC conversion with metadata failed: {str(e)}")
    
    def get_heic_info(self, input_path):
        """Get information about HEIC file"""
        try:
            with Image.open(input_path) as img:
                info = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'width': img.width,
                    'height': img.height
                }
                
                # Get EXIF data if available
                exif = img.getexif()
                if exif:
                    info['has_exif'] = True
                    info['exif_keys'] = len(exif.keys())
                    
                    # Try to get some common EXIF tags
                    try:
                        if 306 in exif:  # DateTime
                            info['datetime'] = exif[306]
                        if 271 in exif:  # Make
                            info['camera_make'] = exif[271]
                        if 272 in exif:  # Model
                            info['camera_model'] = exif[272]
                    except:
                        pass
                else:
                    info['has_exif'] = False
                
                return info
                
        except Exception as e:
            raise Exception(f"Failed to get HEIC info: {str(e)}")
    
    def batch_convert_heic(self, input_paths, output_format='JPEG', quality=95):
        """Convert multiple HEIC files at once"""
        try:
            converted_files = []
            failed_files = []
            
            for input_path in input_paths:
                try:
                    if output_format.upper() == 'JPEG':
                        output_path = self.heic_to_jpg(input_path, quality)
                    else:
                        output_path = self.convert_heic_with_metadata(input_path, output_format, quality)
                    
                    converted_files.append({
                        'input': input_path,
                        'output': output_path,
                        'status': 'success'
                    })
                except Exception as e:
                    failed_files.append({
                        'input': input_path,
                        'error': str(e),
                        'status': 'failed'
                    })
            
            return {
                'converted': converted_files,
                'failed': failed_files,
                'total_processed': len(input_paths),
                'success_count': len(converted_files),
                'failure_count': len(failed_files)
            }
            
        except Exception as e:
            raise Exception(f"Batch HEIC conversion failed: {str(e)}")
    
    @staticmethod
    def is_heic_supported():
        """Check if HEIC support is available"""
        return HEIF_AVAILABLE
    
    def generate_preview(self, input_path):
        """Generate a web-compatible preview (JPG) from any supported image format"""
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                
                # Generate preview filename
                preview_filename = f"{uuid.uuid4().hex}_preview.jpg"
                preview_path = os.path.join(self.upload_folder, preview_filename)
                
                # Resize for web preview (max 1200px width while maintaining aspect ratio)
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
                
                # Save as optimized JPG for web preview
                img.save(preview_path, 'JPEG', quality=85, optimize=True)
                
                return preview_path
                
        except Exception as e:
            raise Exception(f"Preview generation failed: {str(e)}")
    
    @staticmethod
    def get_supported_formats():
        """Get list of supported input/output formats"""
        formats = {
            'input': ['HEIC', 'HEIF'],
            'output': ['JPEG', 'PNG', 'WEBP', 'BMP', 'TIFF']
        }
        
        if HEIF_AVAILABLE:
            formats['output'].append('HEIF')
        
        return formats
