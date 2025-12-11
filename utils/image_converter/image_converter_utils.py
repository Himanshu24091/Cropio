import os
import shutil
import tempfile
import traceback
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, List
import logging

try:
    from PIL import Image, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL (Pillow) not available. Image conversion functionality will be limited.")

def validate_image_file(file_path: str) -> bool:
    """
    Validate that the file is a proper image file by trying to open it
    
    Args:
        file_path: Path to the image file to validate
        
    Returns:
        bool: True if valid image file, False otherwise
    """
    if not PIL_AVAILABLE:
        # Basic validation without PIL - check file exists and has reasonable size
        if not os.path.exists(file_path):
            return False
        
        # Check file size (empty files are invalid)
        if os.path.getsize(file_path) == 0:
            return False
            
        # Basic header validation for common formats
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                
                # JPEG
                if header.startswith(b'\xff\xd8\xff'):
                    return True
                # PNG
                if header.startswith(b'\x89PNG\r\n\x1a\n'):
                    return True
                # BMP
                if header.startswith(b'BM'):
                    return True
                # GIF
                if header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    return True
                # WEBP
                if b'WEBP' in header:
                    return True
                # TIFF
                if header.startswith(b'II*\x00') or header.startswith(b'MM\x00*'):
                    return True
                    
        except Exception:
            return False
            
        return False
    
    try:
        with Image.open(file_path) as img:
            # Try to load the image to verify it's valid
            img.verify()
        
        # Re-open to check if we can actually work with the image
        with Image.open(file_path) as img:
            # Check if image has reasonable dimensions
            width, height = img.size
            if width <= 0 or height <= 0 or width > 50000 or height > 50000:
                return False
                
            # Try to access pixel data to ensure image is complete
            img.load()
            
        return True
        
    except Exception as e:
        logging.error(f"Image validation failed for {file_path}: {str(e)}")
        return False

def process_image_conversion(
    input_path: str, 
    output_path: str, 
    output_format: str, 
    processing_options: Dict[str, Any]
) -> Tuple[bool, Optional[str]]:
    """
    Convert an image file to the specified format with processing options
    
    Args:
        input_path: Path to input image file
        output_path: Path for output image file
        output_format: Target format ('jpg', 'png', 'webp', etc.)
        processing_options: Dictionary with processing parameters
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    if not PIL_AVAILABLE:
        return False, "PIL (Pillow) library is not available. Cannot perform image conversion."
    
    try:
        # Normalize output format
        output_format = output_format.lower()
        if output_format == 'jpeg':
            output_format = 'jpg'
        
        # Open the input image
        with Image.open(input_path) as img:
            # Convert to RGB if necessary (for formats that don't support transparency)
            if output_format in ['jpg', 'bmp'] and img.mode in ['RGBA', 'LA', 'P']:
                # Create a white background for transparent images
                if img.mode == 'P':
                    img = img.convert('RGBA')
                
                if img.mode in ['RGBA', 'LA']:
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[-1])  # Use alpha channel as mask
                    else:  # LA mode
                        background.paste(img, mask=img.split()[-1])
                    img = background
            
            # Apply EXIF orientation if present
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                # If EXIF processing fails, continue without it
                pass
            
            # Apply rotation if specified
            rotation = processing_options.get('rotation', 0)
            if rotation and rotation != 0:
                img = img.rotate(-rotation, expand=True)  # PIL rotates counter-clockwise, so negate
            
            # Apply grayscale conversion if specified
            if processing_options.get('convert_to_grayscale', False):
                img = img.convert('L')  # Convert to grayscale
            
            # Apply resizing if specified
            original_size = img.size
            img = apply_resize_options(img, processing_options)
            
            # Prepare save parameters
            save_params = {}
            
            # Format-specific parameters
            if output_format in ['jpg', 'jpeg']:
                save_params['format'] = 'JPEG'
                save_params['quality'] = processing_options.get('quality', 85)
                save_params['optimize'] = True
                
                # Ensure image is in RGB mode for JPEG
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
            elif output_format == 'png':
                save_params['format'] = 'PNG'
                save_params['optimize'] = True
                
                # PNG can handle RGBA, so keep transparency if present
                if img.mode not in ['RGB', 'RGBA', 'L', 'LA']:
                    if 'transparency' in img.info:
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')
                        
            elif output_format == 'webp':
                save_params['format'] = 'WEBP'
                save_params['quality'] = processing_options.get('quality', 85)
                save_params['method'] = 6  # Best quality method
                
                # WebP supports both RGB and RGBA
                if img.mode not in ['RGB', 'RGBA']:
                    if 'transparency' in img.info or img.mode in ['RGBA', 'LA']:
                        img = img.convert('RGBA')
                    else:
                        img = img.convert('RGB')
                        
            elif output_format == 'bmp':
                save_params['format'] = 'BMP'
                
                # BMP doesn't support transparency
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
            elif output_format in ['tiff', 'tif']:
                save_params['format'] = 'TIFF'
                save_params['compression'] = 'lzw'  # Use LZW compression
                
                # TIFF supports most modes
                if img.mode not in ['RGB', 'RGBA', 'L', 'LA']:
                    img = img.convert('RGB')
                    
            elif output_format == 'gif':
                save_params['format'] = 'GIF'
                save_params['optimize'] = True
                
                # GIF requires palette mode
                if img.mode != 'P':
                    # Convert to palette mode, preserving transparency if possible
                    if img.mode in ['RGBA', 'LA']:
                        # Create transparent GIF
                        img = img.quantize(method=Image.Quantize.MEDIANCUT)
                        transparency_index = img.info.get('transparency', None)
                        if transparency_index is not None:
                            save_params['transparency'] = transparency_index
                    else:
                        img = img.convert('P', palette=Image.ADAPTIVE)
            
            else:
                return False, f"Unsupported output format: {output_format}"
            
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Save the processed image
            img.save(output_path, **save_params)
            
            # Verify the output file was created and has reasonable size
            if not os.path.exists(output_path):
                return False, "Output file was not created"
            
            output_size = os.path.getsize(output_path)
            if output_size == 0:
                return False, "Output file is empty"
            
            # Log conversion details
            new_size = img.size
            size_changed = original_size != new_size
            size_info = f" (resized from {original_size[0]}×{original_size[1]} to {new_size[0]}×{new_size[1]})" if size_changed else ""
            
            logging.info(f"Successfully converted {input_path} to {output_format.upper()}{size_info}")
            
            return True, None
            
    except Exception as e:
        error_msg = f"Image conversion failed: {str(e)}"
        logging.error(f"Error converting {input_path}: {error_msg}")
        logging.error(traceback.format_exc())
        return False, error_msg

def apply_resize_options(img: 'Image.Image', processing_options: Dict[str, Any]) -> 'Image.Image':
    """
    Apply resize options to an image
    
    Args:
        img: PIL Image object
        processing_options: Dictionary with resize parameters
        
    Returns:
        PIL Image object (resized if applicable)
    """
    if not PIL_AVAILABLE:
        return img
    
    try:
        original_width, original_height = img.size
        new_width, new_height = None, None
        
        # Check for percentage-based resize
        resize_percentage = processing_options.get('resize_percentage')
        if resize_percentage and isinstance(resize_percentage, (int, float)) and resize_percentage > 0:
            factor = resize_percentage / 100.0
            new_width = int(original_width * factor)
            new_height = int(original_height * factor)
        
        # Check for dimension-based resize
        else:
            resize_width = processing_options.get('resize_width')
            resize_height = processing_options.get('resize_height')
            maintain_aspect = processing_options.get('maintain_aspect_ratio', False)
            
            if resize_width or resize_height:
                try:
                    if resize_width:
                        new_width = int(resize_width)
                    if resize_height:
                        new_height = int(resize_height)
                except (ValueError, TypeError):
                    # Invalid dimensions, skip resizing
                    return img
                
                # Handle aspect ratio maintenance
                if maintain_aspect and (new_width or new_height):
                    aspect_ratio = original_width / original_height
                    
                    if new_width and new_height:
                        # Both dimensions specified - choose the one that maintains aspect ratio
                        width_based_height = int(new_width / aspect_ratio)
                        height_based_width = int(new_height * aspect_ratio)
                        
                        # Use the smaller resulting size to fit within both constraints
                        if width_based_height <= new_height:
                            new_height = width_based_height
                        else:
                            new_width = height_based_width
                    
                    elif new_width and not new_height:
                        # Only width specified
                        new_height = int(new_width / aspect_ratio)
                    
                    elif new_height and not new_width:
                        # Only height specified
                        new_width = int(new_height * aspect_ratio)
        
        # Apply resize if new dimensions are determined
        if new_width and new_height and (new_width != original_width or new_height != original_height):
            # Ensure dimensions are reasonable
            new_width = max(1, min(new_width, 50000))
            new_height = max(1, min(new_height, 50000))
            
            # Use high-quality resampling
            resampling = getattr(Image, 'LANCZOS', Image.ANTIALIAS)
            img = img.resize((new_width, new_height), resampling)
            
            logging.info(f"Resized image from {original_width}×{original_height} to {new_width}×{new_height}")
        
        return img
        
    except Exception as e:
        logging.error(f"Error applying resize options: {str(e)}")
        # Return original image if resize fails
        return img

def get_conversion_stats(
    processed_files: List[Dict[str, Any]], 
    conversion_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Calculate comprehensive conversion statistics
    
    Args:
        processed_files: List of processed file information
        conversion_stats: Basic conversion statistics
        
    Returns:
        Dictionary with detailed statistics
    """
    if not processed_files:
        return conversion_stats
    
    try:
        # Calculate compression ratios
        total_input_size = conversion_stats.get('total_input_size', 0)
        total_output_size = conversion_stats.get('total_output_size', 0)
        
        compression_ratio = 0
        if total_input_size > 0:
            compression_ratio = (total_input_size - total_output_size) / total_input_size * 100
        
        # Calculate average file sizes
        avg_input_size = total_input_size / len(processed_files) if processed_files else 0
        avg_output_size = total_output_size / len(processed_files) if processed_files else 0
        
        # Add detailed statistics
        conversion_stats.update({
            'compression_ratio_percent': round(compression_ratio, 2),
            'space_saved_bytes': total_input_size - total_output_size,
            'average_input_size_bytes': round(avg_input_size),
            'average_output_size_bytes': round(avg_output_size),
            'largest_file_input': max((f['input_size'] for f in processed_files), default=0),
            'largest_file_output': max((f['output_size'] for f in processed_files), default=0),
            'smallest_file_input': min((f['input_size'] for f in processed_files), default=0),
            'smallest_file_output': min((f['output_size'] for f in processed_files), default=0)
        })
        
        return conversion_stats
        
    except Exception as e:
        logging.error(f"Error calculating conversion stats: {str(e)}")
        return conversion_stats

def create_conversion_summary(
    conversion_stats: Dict[str, Any], 
    output_format: str, 
    processing_options: Dict[str, Any]
) -> str:
    """
    Create a human-readable conversion summary for inclusion in ZIP files
    
    Args:
        conversion_stats: Conversion statistics dictionary
        output_format: Output format used
        processing_options: Processing options applied
        
    Returns:
        String containing formatted conversion summary
    """
    try:
        summary_lines = [
            "IMAGE CONVERSION SUMMARY",
            "=" * 50,
            f"Conversion Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Output Format: {output_format.upper()}",
            "",
            "CONVERSION STATISTICS:",
            f"  Total Files Processed: {conversion_stats.get('total_files', 0)}",
            f"  Successful Conversions: {conversion_stats.get('successful_conversions', 0)}",
            f"  Failed Conversions: {conversion_stats.get('failed_conversions', 0)}",
            "",
            "FILE SIZE ANALYSIS:",
            f"  Total Input Size: {format_file_size(conversion_stats.get('total_input_size', 0))}",
            f"  Total Output Size: {format_file_size(conversion_stats.get('total_output_size', 0))}",
        ]
        
        # Add compression information if available
        compression_ratio = conversion_stats.get('compression_ratio_percent', 0)
        space_saved = conversion_stats.get('space_saved_bytes', 0)
        
        if compression_ratio != 0:
            if compression_ratio > 0:
                summary_lines.extend([
                    f"  Space Saved: {format_file_size(space_saved)} ({compression_ratio:.1f}% reduction)",
                ])
            else:
                summary_lines.extend([
                    f"  Size Increase: {format_file_size(-space_saved)} ({abs(compression_ratio):.1f}% larger)",
                ])
        
        # Add processing options
        summary_lines.extend([
            "",
            "PROCESSING OPTIONS:"
        ])
        
        if processing_options.get('quality') and processing_options['quality'] != 85:
            summary_lines.append(f"  Quality: {processing_options['quality']}%")
        
        if processing_options.get('resize_percentage'):
            summary_lines.append(f"  Resize: {processing_options['resize_percentage']}% of original")
        elif processing_options.get('resize_width') or processing_options.get('resize_height'):
            width = processing_options.get('resize_width', 'auto')
            height = processing_options.get('resize_height', 'auto')
            maintain_aspect = processing_options.get('maintain_aspect_ratio', False)
            aspect_text = " (maintaining aspect ratio)" if maintain_aspect else ""
            summary_lines.append(f"  Resize: {width} × {height} pixels{aspect_text}")
        
        # Add error information if any failures occurred
        errors = conversion_stats.get('errors', [])
        if errors:
            summary_lines.extend([
                "",
                "CONVERSION ERRORS:",
            ])
            for i, error in enumerate(errors[:10], 1):  # Show max 10 errors
                summary_lines.append(f"  {i}. {error}")
            
            if len(errors) > 10:
                summary_lines.append(f"  ... and {len(errors) - 10} more errors")
        
        # Add footer
        summary_lines.extend([
            "",
            "=" * 50,
            "Generated by Image Converter Tool",
            f"For support, please check the application documentation."
        ])
        
        return "\n".join(summary_lines)
        
    except Exception as e:
        logging.error(f"Error creating conversion summary: {str(e)}")
        return f"Conversion Summary\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nFormat: {output_format.upper()}\nProcessed Files: {conversion_stats.get('successful_conversions', 0)}"

def cleanup_temp_files(temp_dirs: List[str]) -> None:
    """
    Clean up temporary directories and files
    
    Args:
        temp_dirs: List of temporary directory paths to remove
    """
    for temp_dir in temp_dirs:
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                logging.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logging.error(f"Error cleaning up temporary directory {temp_dir}: {str(e)}")

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable string
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.1f} {size_names[i]}"

def get_image_info(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Get basic information about an image file
    
    Args:
        file_path: Path to image file
        
    Returns:
        Dictionary with image information or None if error
    """
    if not PIL_AVAILABLE or not os.path.exists(file_path):
        return None
    
    try:
        with Image.open(file_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.size[0],
                'height': img.size[1],
                'has_transparency': img.mode in ['RGBA', 'LA'] or 'transparency' in img.info,
                'file_size': os.path.getsize(file_path)
            }
    except Exception as e:
        logging.error(f"Error getting image info for {file_path}: {str(e)}")
        return None

def is_format_supported(format_name: str, for_output: bool = True) -> bool:
    """
    Check if a format is supported for input or output
    
    Args:
        format_name: Format name to check
        for_output: True to check output support, False for input
        
    Returns:
        True if format is supported
    """
    format_name = format_name.lower()
    
    input_formats = {'jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'gif', 'webp'}
    output_formats = {'jpg', 'jpeg', 'png', 'webp', 'bmp', 'tiff', 'gif'}
    
    if for_output:
        return format_name in output_formats
    else:
        return format_name in input_formats

def get_optimal_quality_for_format(format_name: str, file_size: int) -> int:
    """
    Get optimal quality setting for a format based on file size
    
    Args:
        format_name: Output format name
        file_size: Input file size in bytes
        
    Returns:
        Recommended quality setting (1-100)
    """
    format_name = format_name.lower()
    
    # Only JPEG and WebP support quality settings
    if format_name not in ['jpg', 'jpeg', 'webp']:
        return 85  # Default, but not used
    
    # Adjust quality based on input file size
    if file_size < 100 * 1024:  # < 100KB
        return 95  # High quality for small files
    elif file_size < 1024 * 1024:  # < 1MB
        return 85  # Standard quality
    elif file_size < 5 * 1024 * 1024:  # < 5MB
        return 75  # Lower quality for larger files
    else:
        return 65  # Lowest quality for very large files