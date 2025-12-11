"""
RAW Image Processor Utility - Professional Edition
Advanced camera RAW file processing with metadata preservation and batch support
"""

import os
import uuid
import numpy as np
from PIL import Image, ImageEnhance, ExifTags
from datetime import datetime
import tempfile
import json

try:
    import rawpy
    RAW_AVAILABLE = True
    print(f"✅ rawpy loaded successfully from: {rawpy.__file__}")
except ImportError as e:
    RAW_AVAILABLE = False
    print(f"❌ rawpy not available: {e}")


class RAWProcessor:
    """Advanced RAW image processor with professional features"""
    
    # Supported RAW formats with camera brand mapping
    SUPPORTED_FORMATS = {
        'CR2': 'Canon',
        'CR3': 'Canon', 
        'NEF': 'Nikon',
        'ARW': 'Sony',
        'DNG': 'Adobe',
        'RAF': 'Fujifilm',
        'RW2': 'Panasonic',
        'ORF': 'Olympus',
        'PEF': 'Pentax',
        'SRW': 'Samsung',
        'X3F': 'Sigma',
        '3FR': 'Hasselblad',
        'FFF': 'Imacon',
        'MEF': 'Mamiya',
        'MOS': 'Leaf',
        'RAW': 'Generic'
    }
    
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        
        if not RAW_AVAILABLE:
            raise ImportError("rawpy is required for RAW processing. Install with: pip install rawpy")
        
        # Test rawpy functionality
        try:
            # Try to create a rawpy instance to test if it works
            import rawpy
            print(f"rawpy module attributes: {[attr for attr in dir(rawpy) if not attr.startswith('_')][:10]}")
        except Exception as e:
            print(f"⚠️  rawpy test failed: {e}")
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
    
    def raw_to_jpg(self, input_path, output_format='JPEG', quality=95, 
                   preserve_metadata=True, processing_params=None):
        """
        Convert RAW file to JPG/PNG with advanced processing options
        
        Args:
            input_path: Path to RAW file
            output_format: Output format ('JPEG', 'PNG', 'TIFF')
            quality: Quality level (50-100 for JPEG)
            preserve_metadata: Whether to preserve EXIF data
            processing_params: Custom processing parameters
        
        Returns:
            Path to converted file
        """
        try:
            # First, validate that the file exists and has a proper extension
            if not os.path.exists(input_path):
                raise Exception(f"Input file not found: {input_path}")
            
            # Check file extension
            file_ext = os.path.splitext(input_path)[1].upper().replace('.', '')
            if file_ext not in self.SUPPORTED_FORMATS:
                raise Exception(f"File extension '{file_ext}' is not a supported RAW format. Supported formats: {list(self.SUPPORTED_FORMATS.keys())}")
            
            # Add detailed file information for debugging
            print(f"📄 Processing file: {input_path}")
            print(f"📊 File size: {os.path.getsize(input_path)} bytes")
            print(f"📝 File extension: {file_ext}")
            
            # Check if file is actually readable as RAW (quick validation)
            try:
                print(f"🔍 Testing rawpy.imread on: {input_path}")
                with rawpy.imread(input_path) as test_raw:
                    # Just check if we can open it - don't process
                    if not hasattr(test_raw, 'sizes'):
                        raise Exception("File appears corrupt or is not a valid RAW file")
                    print(f"✅ RAW file validated successfully")
            except Exception as e:
                print(f"❌ rawpy.imread failed: {str(e)}")
                print(f"❌ Error type: {type(e).__name__}")
                
                # Check if it's a library issue vs file issue
                if "not RAW file" in str(e) or "Unsupported file format" in str(e):
                    # Try to provide more helpful error message
                    error_msg = f"The file '{os.path.basename(input_path)}' with extension '.{file_ext.lower()}' could not be processed as a RAW file. "
                    error_msg += f"This could be because:\n"
                    error_msg += f"1. The file is not actually a RAW file (despite the extension)\n"
                    error_msg += f"2. The file is corrupted\n"
                    error_msg += f"3. This RAW format is not supported by the current rawpy version\n"
                    error_msg += f"\nOriginal error: {str(e)}"
                    raise Exception(error_msg)
                else:
                    raise Exception(f"Unable to read RAW file: {str(e)}")
            
            # Default processing parameters optimized for proper exposure
            default_params = {
                'use_camera_wb': True,
                'use_auto_wb': False,
                'auto_bright_thr': 0.01,  # Will be overridden based on auto_brightness setting
                'user_wb': None,
                'output_color': rawpy.ColorSpace.sRGB,
                'output_bps': 8,
                'demosaic_algorithm': rawpy.DemosaicAlgorithm.AHD,
                'highlight_mode': rawpy.HighlightMode.Blend,  # Better highlight recovery
                'exp_shift': 1.2,  # Slight positive exposure compensation
                'exp_preserve_highlights': 0.8,  # Preserve highlights better
                'no_auto_scale': False,
                'gamma': (2.222, 4.5),  # Standard sRGB gamma curve
                'bright': 1.8,  # Increase brightness for better exposure
                'fbdd_noise_reduction': rawpy.FBDDNoiseReductionMode.Light
            }
            
            # Update with custom parameters if provided
            if processing_params:
                default_params.update(processing_params)
            
            with rawpy.imread(input_path) as raw:
                # Process RAW image with specified parameters
                rgb = raw.postprocess(**default_params)
                
                # Convert numpy array to PIL Image
                img = Image.fromarray(rgb)
                
                # Generate unique output filename
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_ext = 'jpg' if output_format.upper() == 'JPEG' else output_format.lower()
                output_filename = f"{uuid.uuid4().hex}_{base_name}_processed.{output_ext}"
                output_path = os.path.join(self.upload_folder, output_filename)
                
                # Save with format-specific options
                if output_format.upper() == 'JPEG':
                    img.save(output_path, 'JPEG', 
                           quality=quality, 
                           optimize=True,
                           progressive=True)
                elif output_format.upper() == 'PNG':
                    img.save(output_path, 'PNG', 
                           optimize=True,
                           compress_level=9)
                elif output_format.upper() == 'TIFF':
                    img.save(output_path, 'TIFF', 
                           compression='tiff_lzw')
                else:
                    img.save(output_path, output_format.upper(), quality=quality)
                
                # Preserve metadata if requested
                if preserve_metadata:
                    self._preserve_metadata(input_path, output_path, raw)
                
                return output_path
                
        except Exception as e:
            raise Exception(f"RAW to {output_format} conversion failed: {str(e)}")
    
    def batch_convert_raw(self, input_paths, output_format='JPEG', quality=95,
                         preserve_metadata=True, processing_params=None):
        """
        Batch convert multiple RAW files
        
        Returns:
            Dictionary with conversion results
        """
        results = {
            'converted': [],
            'failed': [],
            'total_processed': len(input_paths),
            'success_count': 0,
            'failure_count': 0
        }
        
        for input_path in input_paths:
            try:
                output_path = self.raw_to_jpg(
                    input_path, output_format, quality, 
                    preserve_metadata, processing_params
                )
                
                results['converted'].append({
                    'input': input_path,
                    'output': output_path,
                    'status': 'success',
                    'size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
                })
                results['success_count'] += 1
                
            except Exception as e:
                results['failed'].append({
                    'input': input_path,
                    'error': str(e),
                    'status': 'failed'
                })
                results['failure_count'] += 1
        
        return results
    
    def get_raw_metadata(self, input_path):
        """
        Extract comprehensive metadata from RAW file
        
        Returns:
            Dictionary with detailed RAW metadata (JSON serializable)
        """
        try:
            # Validate file before processing
            if not os.path.exists(input_path):
                raise Exception(f"Input file not found: {input_path}")
            
            file_ext = os.path.splitext(input_path)[1].upper().replace('.', '')
            if file_ext not in self.SUPPORTED_FORMATS:
                raise Exception(f"File extension '{file_ext}' is not a supported RAW format")
            
            with rawpy.imread(input_path) as raw:
                # Convert all values to JSON-serializable types
                metadata = {
                    'filename': os.path.basename(input_path),
                    'filesize': os.path.getsize(input_path),
                    'format': self._detect_raw_format(input_path),
                    'brand': self._get_camera_brand(input_path),
                    
                    # RAW-specific information - convert to strings/numbers
                    'raw_info': {
                        'raw_type': str(getattr(raw, 'raw_type', 'Unknown')),
                        'color_desc': raw.color_desc.decode('ascii') if hasattr(raw, 'color_desc') and raw.color_desc else 'Unknown',
                        'num_colors': int(getattr(raw, 'num_colors', 0)),
                        'raw_pattern': raw.raw_pattern.tolist() if hasattr(raw, 'raw_pattern') and hasattr(raw.raw_pattern, 'tolist') else [],
                    },
                    
                    # Image dimensions - ensure all are integers
                    'dimensions': {
                        'raw_width': int(raw.sizes.raw_width),
                        'raw_height': int(raw.sizes.raw_height),
                        'width': int(raw.sizes.width), 
                        'height': int(raw.sizes.height),
                        'top_margin': int(raw.sizes.top_margin),
                        'left_margin': int(raw.sizes.left_margin),
                        'iwidth': int(raw.sizes.iwidth),
                        'iheight': int(raw.sizes.iheight)
                    },
                    
                    # Color information - convert arrays to lists
                    'color_info': {},
                    
                    # Sensor information
                    'sensor_info': {}
                }
                
                # Safely extract color information
                try:
                    if hasattr(raw, 'color_matrix') and raw.color_matrix is not None:
                        metadata['color_info']['color_matrix'] = raw.color_matrix.tolist()
                except:
                    metadata['color_info']['color_matrix'] = None
                    
                try:
                    if hasattr(raw, 'daylight_whitebalance') and raw.daylight_whitebalance is not None:
                        metadata['color_info']['daylight_whitebalance'] = raw.daylight_whitebalance.tolist()
                except:
                    metadata['color_info']['daylight_whitebalance'] = None
                    
                try:
                    if hasattr(raw, 'camera_whitebalance') and raw.camera_whitebalance is not None:
                        metadata['color_info']['camera_whitebalance'] = raw.camera_whitebalance.tolist()
                except:
                    metadata['color_info']['camera_whitebalance'] = None
                
                # Safely extract sensor-specific information
                try:
                    if hasattr(raw, 'black_level_per_channel') and raw.black_level_per_channel is not None:
                        metadata['sensor_info']['black_level_per_channel'] = raw.black_level_per_channel.tolist()
                except:
                    metadata['sensor_info']['black_level_per_channel'] = None
                    
                try:
                    if hasattr(raw, 'white_level'):
                        metadata['sensor_info']['white_level'] = int(raw.white_level)
                except:
                    metadata['sensor_info']['white_level'] = None
                    
                try:
                    if hasattr(raw, 'camera_matrix') and raw.camera_matrix is not None:
                        metadata['sensor_info']['camera_matrix'] = raw.camera_matrix.tolist()
                except:
                    metadata['sensor_info']['camera_matrix'] = None
                
                # Test JSON serialization to catch any remaining issues
                import json
                json.dumps(metadata)  # This will raise an exception if not serializable
                
                return metadata
                
        except Exception as e:
            raise Exception(f"Failed to extract RAW metadata: {str(e)}")
    
    def enhance_image(self, image_path, brightness=1.0, contrast=1.0, 
                     saturation=1.0, sharpness=1.0, temperature_shift=0):
        """
        Apply enhancements to processed image
        
        Args:
            image_path: Path to image file
            brightness: Brightness adjustment (0.5-2.0)
            contrast: Contrast adjustment (0.5-2.0) 
            saturation: Saturation adjustment (0.0-2.0)
            sharpness: Sharpness adjustment (0.0-2.0)
            temperature_shift: Color temperature shift (-100 to +100)
        
        Returns:
            Path to enhanced image
        """
        try:
            with Image.open(image_path) as img:
                enhanced = img.copy()
                
                # Apply brightness
                if brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(enhanced)
                    enhanced = enhancer.enhance(brightness)
                
                # Apply contrast
                if contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(enhanced)
                    enhanced = enhancer.enhance(contrast)
                
                # Apply saturation
                if saturation != 1.0:
                    enhancer = ImageEnhance.Color(enhanced)
                    enhanced = enhancer.enhance(saturation)
                
                # Apply sharpness
                if sharpness != 1.0:
                    enhancer = ImageEnhance.Sharpness(enhanced)
                    enhanced = enhancer.enhance(sharpness)
                
                # Apply temperature shift (simplified)
                if temperature_shift != 0:
                    enhanced = self._apply_temperature_shift(enhanced, temperature_shift)
                
                # Save enhanced image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                enhanced_filename = f"{uuid.uuid4().hex}_{base_name}_enhanced.jpg"
                enhanced_path = os.path.join(self.upload_folder, enhanced_filename)
                
                enhanced.save(enhanced_path, 'JPEG', quality=95, optimize=True)
                
                return enhanced_path
                
        except Exception as e:
            raise Exception(f"Image enhancement failed: {str(e)}")
    
    def create_preview(self, input_path, max_size=(800, 600)):
        """
        Create a preview/thumbnail of RAW file
        
        Args:
            input_path: Path to RAW file
            max_size: Maximum dimensions for preview
            
        Returns:
            Path to preview image
        """
        try:
            # Validate file before processing
            if not os.path.exists(input_path):
                raise Exception(f"Input file not found: {input_path}")
            
            file_ext = os.path.splitext(input_path)[1].upper().replace('.', '')
            if file_ext not in self.SUPPORTED_FORMATS:
                raise Exception(f"File extension '{file_ext}' is not a supported RAW format")
                
            with rawpy.imread(input_path) as raw:
                # Quick processing for preview with improved exposure
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    output_color=rawpy.ColorSpace.sRGB,
                    output_bps=8,
                    no_auto_scale=False,
                    auto_bright_thr=0.01,
                    highlight_mode=rawpy.HighlightMode.Blend,
                    exp_shift=1.1,
                    exp_preserve_highlights=0.7,
                    gamma=(2.222, 4.5),
                    bright=1.6
                )
                
                # Convert to PIL Image
                img = Image.fromarray(rgb)
                
                # Resize to preview size
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save preview
                preview_filename = f"{uuid.uuid4().hex}_preview.jpg"
                preview_path = os.path.join(self.upload_folder, preview_filename)
                
                img.save(preview_path, 'JPEG', quality=85, optimize=True)
                
                return preview_path
                
        except Exception as e:
            raise Exception(f"Preview creation failed: {str(e)}")
    
    def _preserve_metadata(self, input_path, output_path, raw_obj):
        """Preserve metadata from RAW to output file"""
        try:
            # This is a simplified metadata preservation
            # In a full implementation, you'd extract and embed specific EXIF data
            pass
        except:
            pass
    
    def _detect_raw_format(self, filepath):
        """Detect RAW format from file extension"""
        ext = os.path.splitext(filepath)[1].upper().replace('.', '')
        return self.SUPPORTED_FORMATS.get(ext, 'Unknown RAW')
    
    def _get_camera_brand(self, filepath):
        """Get camera brand from RAW format"""
        ext = os.path.splitext(filepath)[1].upper().replace('.', '')
        return self.SUPPORTED_FORMATS.get(ext, 'Unknown')
    
    def _apply_temperature_shift(self, img, shift):
        """Apply color temperature shift to image"""
        try:
            # Simplified temperature adjustment
            # In practice, this would involve more complex color matrix operations
            if shift > 0:  # Warmer
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.0 + shift/200.0)
            elif shift < 0:  # Cooler
                enhancer = ImageEnhance.Color(img) 
                img = enhancer.enhance(1.0 - abs(shift)/200.0)
            return img
        except:
            return img
    
    def create_processing_report(self, input_path, output_path, processing_params):
        """Create detailed processing report"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'input_file': os.path.basename(input_path),
                'output_file': os.path.basename(output_path),
                'input_size': os.path.getsize(input_path),
                'output_size': os.path.getsize(output_path) if os.path.exists(output_path) else 0,
                'processing_parameters': processing_params,
                'metadata': self.get_raw_metadata(input_path)
            }
            
            report_filename = f"{uuid.uuid4().hex}_processing_report.json"
            report_path = os.path.join(self.upload_folder, report_filename)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            
            return report_path
            
        except Exception as e:
            raise Exception(f"Failed to create processing report: {str(e)}")
    
    @staticmethod
    def is_raw_supported():
        """Check if RAW processing is supported"""
        return RAW_AVAILABLE
    
    @staticmethod
    def get_supported_formats():
        """Get list of supported RAW formats"""
        return list(RAWProcessor.SUPPORTED_FORMATS.keys())
    
    @staticmethod
    def get_format_info():
        """Get detailed format information"""
        return RAWProcessor.SUPPORTED_FORMATS.copy()
    
    @staticmethod
    def validate_raw_file(filepath):
        """Validate if file is a supported RAW format"""
        if not os.path.exists(filepath):
            return False
        
        ext = os.path.splitext(filepath)[1].upper().replace('.', '')
        
        # First check extension
        if ext not in RAWProcessor.SUPPORTED_FORMATS:
            return False
            
        # For files with RAW extensions, try to actually read them with rawpy
        try:
            import rawpy
            with rawpy.imread(filepath):
                return True
        except Exception as e:
            print(f"RAW validation failed for {filepath}: {str(e)}")
            return False
    
    @staticmethod
    def check_file_format(filepath):
        """Check the actual format of a file regardless of extension with enhanced detection"""
        if not os.path.exists(filepath):
            return {'is_raw': False, 'is_image': False, 'format': 'unknown', 'error': 'File not found'}
        
        file_ext = os.path.splitext(filepath)[1].upper().replace('.', '')
        
        # First try to read as regular image to get detailed format info
        image_info = None
        try:
            from PIL import Image
            with Image.open(filepath) as img:
                image_info = {
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'has_exif': hasattr(img, '_getexif') and img._getexif() is not None
                }
        except Exception as img_error:
            pass
        
        # Then try to read as RAW
        try:
            import rawpy
            with rawpy.imread(filepath):
                # If successful, it's a true RAW file
                return {
                    'is_raw': True, 
                    'is_image': False, 
                    'format': 'RAW', 
                    'error': None,
                    'detected_format': f'RAW-{file_ext}',
                    'suggestion': 'file_is_true_raw'
                }
        except Exception as raw_error:
            # RAW reading failed, check if we have image info
            if image_info:
                suggestion = 'use_image_to_raw' if file_ext in ['DNG', 'CR2', 'CR3', 'NEF', 'ARW'] else 'file_is_image'
                return {
                    'is_raw': False, 
                    'is_image': True, 
                    'format': image_info['format'], 
                    'error': None,
                    'detected_format': image_info['format'],
                    'suggestion': suggestion,
                    'raw_error': str(raw_error)[:100] + '...' if len(str(raw_error)) > 100 else str(raw_error),
                    'image_info': image_info
                }
            else:
                return {
                    'is_raw': False, 
                    'is_image': False, 
                    'format': 'unknown',
                    'error': f'Cannot read as RAW: {str(raw_error)[:100]}... Cannot read as image: File appears corrupted',
                    'suggestion': 'file_corrupted_or_unsupported'
                }
    
    def png_to_raw(self, input_path, output_format='DNG', quality=95,
                   preserve_metadata=True, processing_params=None):
        """
        Convert PNG/JPG file to RAW format (primarily DNG)
        
        Args:
            input_path: Path to PNG/JPG file
            output_format: Output RAW format ('DNG' is most common)
            quality: Quality level for conversion
            preserve_metadata: Whether to preserve EXIF data
            processing_params: Custom processing parameters
        
        Returns:
            Path to converted RAW file
        """
        try:
            # Open the input image
            with Image.open(input_path) as img:
                # Convert to RGB if not already
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Convert PIL image to numpy array
                img_array = np.array(img)
                
                # Generate unique output filename
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_ext = output_format.lower()
                output_filename = f"{uuid.uuid4().hex}_{base_name}_converted.{output_ext}"
                output_path = os.path.join(self.upload_folder, output_filename)
                
                # For DNG format, we'll create a simulated RAW file
                # Note: This is a simplified conversion - real RAW conversion would require
                # complex color space transformations and sensor simulation
                
                if output_format.upper() == 'DNG':
                    # Create DNG-compatible image
                    # This is a simplified approach using TIFF with appropriate metadata
                    tiff_path = output_path.replace('.dng', '.tiff')
                    
                    # Save as TIFF without quality parameter (not supported for TIFF compression)
                    img.save(tiff_path, 'TIFF', compression='tiff_lzw')
                    
                    # Rename to DNG (simplified approach)
                    dng_path = output_path
                    os.rename(tiff_path, dng_path)
                    
                else:
                    # For other RAW formats, save as TIFF with appropriate metadata
                    # TIFF compression doesn't support quality parameter
                    img.save(output_path, 'TIFF', compression='tiff_lzw')
                
                # Preserve metadata if requested
                if preserve_metadata:
                    self._preserve_png_metadata(input_path, output_path)
                
                return output_path
                
        except Exception as e:
            raise Exception(f"PNG to {output_format} conversion failed: {str(e)}")
    
    def batch_convert_png_to_raw(self, input_paths, output_format='DNG', quality=95,
                                preserve_metadata=True, processing_params=None):
        """
        Batch convert multiple PNG files to RAW format
        
        Returns:
            Dictionary with conversion results
        """
        results = {
            'converted': [],
            'failed': [],
            'total_processed': len(input_paths),
            'success_count': 0,
            'failure_count': 0
        }
        
        for input_path in input_paths:
            try:
                output_path = self.png_to_raw(
                    input_path, output_format, quality,
                    preserve_metadata, processing_params
                )
                
                results['converted'].append({
                    'input': input_path,
                    'output': output_path,
                    'status': 'success',
                    'size': os.path.getsize(output_path) if os.path.exists(output_path) else 0
                })
                results['success_count'] += 1
                
            except Exception as e:
                results['failed'].append({
                    'input': input_path,
                    'error': str(e),
                    'status': 'failed'
                })
                results['failure_count'] += 1
        
        return results
    
    def _preserve_png_metadata(self, input_path, output_path):
        """Preserve metadata from PNG to RAW file"""
        try:
            # Extract EXIF data from PNG if available
            with Image.open(input_path) as img:
                if hasattr(img, '_getexif') and img._getexif():
                    # This is a simplified metadata preservation
                    # In practice, you'd need more sophisticated metadata handling
                    pass
        except:
            pass
    
    @staticmethod
    def validate_image_file(filepath):
        """Validate if file is a supported image format for conversion to RAW"""
        if not os.path.exists(filepath):
            return False
        
        ext = os.path.splitext(filepath)[1].upper().replace('.', '')
        supported_image_formats = ['PNG', 'JPG', 'JPEG', 'TIFF', 'TIF', 'BMP']
        return ext in supported_image_formats
    
    @staticmethod
    def get_supported_output_raw_formats():
        """Get list of supported output RAW formats"""
        return ['DNG', 'TIFF']  # DNG is most compatible, TIFF as fallback
    
    @staticmethod
    def estimate_processing_time(file_size_mb):
        """Estimate processing time based on file size"""
        # Rough estimates in seconds
        if file_size_mb < 10:
            return "5-15 seconds"
        elif file_size_mb < 25:
            return "15-30 seconds"
        elif file_size_mb < 50:
            return "30-60 seconds"
        else:
            return "1-2 minutes"
    
    def smart_convert(self, input_path, output_format='JPEG', quality=95, 
                     preserve_metadata=True, processing_params=None):
        """
        Smart conversion that automatically detects file type and routes to appropriate conversion method
        
        Args:
            input_path: Path to input file
            output_format: Desired output format
            quality: Quality level (50-100)
            preserve_metadata: Whether to preserve EXIF data
            processing_params: Custom processing parameters
        
        Returns:
            Dictionary with conversion result and metadata
        """
        try:
            # First, detect what type of file this actually is
            format_check = self.check_file_format(input_path)
            filename = os.path.basename(input_path)
            file_ext = os.path.splitext(input_path)[1].upper().replace('.', '')
            
            print(f"🔍 Smart conversion analysis for {filename}:")
            print(f"   Extension: .{file_ext.lower()}")
            print(f"   Detected format: {format_check.get('detected_format', 'unknown')}")
            print(f"   Is RAW: {format_check['is_raw']}")
            print(f"   Is Image: {format_check['is_image']}")
            print(f"   Suggestion: {format_check.get('suggestion', 'none')}")
            
            if format_check['is_raw']:
                # True RAW file - convert using RAW processor
                print(f"✅ Processing as true RAW file")
                output_path = self.raw_to_jpg(
                    input_path, output_format, quality, 
                    preserve_metadata, processing_params
                )
                conversion_type = f'RAW → {output_format}'
                
            elif format_check['is_image']:
                # Image file with potentially wrong extension
                detected_format = format_check.get('detected_format', 'IMAGE')
                print(f"✅ Processing as {detected_format} image file")
                
                # Check if user wants RAW output
                if output_format.upper() in ['DNG', 'RAW']:
                    # Convert image to RAW
                    output_path = self.png_to_raw(
                        input_path, 'DNG', quality, 
                        preserve_metadata, processing_params
                    )
                    conversion_type = f'{detected_format} → DNG'
                else:
                    # Convert image to another image format
                    output_path = self._convert_image_to_image(
                        input_path, output_format, quality, preserve_metadata
                    )
                    conversion_type = f'{detected_format} → {output_format}'
                    
            else:
                # Neither RAW nor standard image
                error_msg = f"File '{filename}' could not be processed. "
                if format_check.get('suggestion') == 'file_corrupted_or_unsupported':
                    error_msg += "The file appears to be corrupted or in an unsupported format."
                else:
                    error_msg += f"Error: {format_check.get('error', 'Unknown error')}"
                raise Exception(error_msg)
            
            return {
                'success': True,
                'output_path': output_path,
                'conversion_type': conversion_type,
                'detected_format': format_check.get('detected_format', 'unknown'),
                'original_extension': file_ext,
                'format_check': format_check
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'format_check': format_check if 'format_check' in locals() else None
            }
    
    def _convert_image_to_image(self, input_path, output_format='JPEG', quality=95, preserve_metadata=True):
        """
        Convert image file to another image format
        
        Args:
            input_path: Path to input image
            output_format: Output format ('JPEG', 'PNG', 'TIFF')
            quality: Quality level for JPEG
            preserve_metadata: Whether to preserve EXIF data
        
        Returns:
            Path to converted file
        """
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if needed for JPEG
                if output_format.upper() == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Generate unique output filename
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_ext = 'jpg' if output_format.upper() == 'JPEG' else output_format.lower()
                output_filename = f"{uuid.uuid4().hex}_{base_name}_converted.{output_ext}"
                output_path = os.path.join(self.upload_folder, output_filename)
                
                # Save with format-specific options
                if output_format.upper() == 'JPEG':
                    img.save(output_path, 'JPEG', 
                           quality=quality, 
                           optimize=True,
                           progressive=True)
                elif output_format.upper() == 'PNG':
                    img.save(output_path, 'PNG', 
                           optimize=True,
                           compress_level=9)
                elif output_format.upper() == 'TIFF':
                    img.save(output_path, 'TIFF', 
                           compression='tiff_lzw')
                else:
                    img.save(output_path, output_format.upper())
                
                return output_path
                
        except Exception as e:
            raise Exception(f"Image to {output_format} conversion failed: {str(e)}")


class RAWAnalyzer:
    """Separate class for RAW file analysis without conversion"""
    
    def __init__(self):
        if not RAW_AVAILABLE:
            raise ImportError("rawpy is required for RAW analysis")
    
    def analyze_raw_file(self, filepath):
        """Comprehensive RAW file analysis"""
        try:
            with rawpy.imread(filepath) as raw:
                analysis = {
                    'basic_info': {
                        'filename': os.path.basename(filepath),
                        'file_size': os.path.getsize(filepath),
                        'format': RAWProcessor._detect_raw_format(None, filepath),
                        'brand': RAWProcessor._get_camera_brand(None, filepath)
                    },
                    'image_info': {
                        'dimensions': f"{raw.sizes.width} x {raw.sizes.height}",
                        'raw_dimensions': f"{raw.sizes.raw_width} x {raw.sizes.raw_height}",
                        'aspect_ratio': round(raw.sizes.width / raw.sizes.height, 2),
                        'megapixels': round((raw.sizes.width * raw.sizes.height) / 1000000, 1)
                    },
                    'processing_info': {
                        'color_channels': getattr(raw, 'num_colors', 'Unknown'),
                        'bit_depth': '14-16 bit (estimated)',
                        'compression': 'Lossless RAW',
                        'white_balance': 'As shot' if hasattr(raw, 'camera_whitebalance') else 'Unknown'
                    },
                    'recommendations': [
                        'Use Camera White Balance for natural colors',
                        'Enable Auto Brightness for balanced exposure', 
                        'Choose JPEG for smaller files or PNG for highest quality',
                        'Consider batch processing for multiple files'
                    ]
                }
                
                return analysis
                
        except Exception as e:
            raise Exception(f"RAW file analysis failed: {str(e)}")
