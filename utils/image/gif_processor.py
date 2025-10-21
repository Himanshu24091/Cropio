"""
Fresh GIF ⇄ PNG Sequence Processor Utility
Handles GIF frame extraction and PNG sequence to GIF conversion
"""

import os
import uuid
import tempfile
import shutil
from PIL import Image, ImageSequence
import zipfile
from typing import List, Dict, Tuple, Optional, Any
import logging
from datetime import datetime


class GIFProcessor:
    """Professional-grade utility class for GIF and PNG sequence processing"""
    
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.temp_dir = tempfile.gettempdir()
        self.logger = logging.getLogger(__name__)
        
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
    
    def gif_to_png_sequence(self, gif_path: str, output_dir: str = None, 
                           preserve_timing: bool = True, optimize: bool = True) -> Dict[str, Any]:
        """
        Extract frames from GIF file to PNG images
        
        Args:
            gif_path: Path to input GIF file
            output_dir: Directory for extracted frames (auto-created if None)
            preserve_timing: Whether to preserve original frame timing
            optimize: Whether to optimize PNG compression
            
        Returns:
            Dictionary with extraction results
        """
        try:
            with Image.open(gif_path) as gif:
                # Validate GIF
                if gif.format != 'GIF':
                    return {
                        'success': False,
                        'message': f'File format is {gif.format}, expected GIF'
                    }
                
                frames = []
                durations = []
                frame_info = []
                
                # Create output directory if not provided
                if output_dir is None:
                    temp_id = str(uuid.uuid4())
                    output_dir = os.path.join(self.temp_dir, f'gif_frames_{temp_id}')
                
                os.makedirs(output_dir, exist_ok=True)
                
                # Process each frame
                frame_count = 0
                for i, frame in enumerate(ImageSequence.Iterator(gif)):
                    try:
                        # Convert to RGBA to preserve transparency
                        if frame.mode != 'RGBA':
                            frame = frame.convert('RGBA')
                        
                        # Generate frame filename
                        frame_filename = f"frame_{i:04d}.png"
                        frame_path = os.path.join(output_dir, frame_filename)
                        
                        # Save frame as PNG
                        save_kwargs = {
                            'format': 'PNG',
                            'optimize': optimize,
                            'compress_level': 6 if optimize else 1
                        }
                        frame.save(frame_path, **save_kwargs)
                        
                        frames.append(frame_path)
                        frame_count += 1
                        
                        # Get frame duration (default 100ms if not specified)
                        duration = frame.info.get('duration', 100)
                        durations.append(duration)
                        
                        # Collect frame information
                        frame_info.append({
                            'index': i,
                            'filename': frame_filename,
                            'path': frame_path,
                            'duration': duration,
                            'size': frame.size,
                            'mode': frame.mode,
                            'file_size': os.path.getsize(frame_path) if os.path.exists(frame_path) else 0
                        })
                        
                    except Exception as frame_error:
                        self.logger.warning(f"Failed to process frame {i}: {frame_error}")
                        continue
                
                if frame_count == 0:
                    return {
                        'success': False,
                        'message': 'No frames could be extracted from the GIF'
                    }
                
                # Get GIF metadata
                gif_info = self._get_gif_info(gif_path)
                
                # Calculate timing information
                total_duration = sum(durations)
                average_duration = total_duration / len(durations) if durations else 100
                
                return {
                    'success': True,
                    'message': f'Successfully extracted {frame_count} frames from GIF',
                    'frames': frames,
                    'output_dir': output_dir,
                    'frame_count': frame_count,
                    'durations': durations,
                    'total_duration': total_duration,
                    'average_duration': average_duration,
                    'frame_info': frame_info,
                    'gif_info': gif_info,
                    'preserve_timing': preserve_timing,
                    'timing_info': durations if preserve_timing else None
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to extract GIF frames: {str(e)}'
            }
        finally:
            # Note: We don't clean up the output directory here as the caller needs the frames
            pass
    
    def png_sequence_to_gif(self, image_paths: List[str], output_path: str = None,
                           frame_duration: int = 100, loop_count: int = 0, 
                           optimize: bool = True, dithering: bool = False,
                           quality_settings: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create GIF from PNG/JPG image sequence
        
        Args:
            image_paths: List of paths to input images
            output_path: Path for output GIF (auto-generated if None)
            frame_duration: Duration per frame in milliseconds
            loop_count: Number of loops (0 = infinite)
            optimize: Whether to optimize GIF
            dithering: Whether to enable dithering
            quality_settings: Quality settings dict with colors count, etc.
            
        Returns:
            Dictionary with creation results
        """
        try:
            if not image_paths:
                return {
                    'success': False,
                    'message': 'No images provided'
                }
            
            # Apply default quality settings if not provided
            if quality_settings is None:
                quality_settings = {'colors': 128, 'optimize': True}
            
            # Generate output path if not provided
            if not output_path:
                output_filename = f"sequence_{uuid.uuid4().hex}.gif"
                output_path = os.path.join(self.upload_folder, output_filename)
            
            images = []
            
            # Load and process images
            for i, image_path in enumerate(sorted(image_paths)):
                try:
                    with Image.open(image_path) as img:
                        # Convert to RGBA for consistency
                        if img.mode not in ('RGBA', 'RGB'):
                            img = img.convert('RGBA')
                        
                        # Create a copy to avoid issues with file handles
                        img_copy = img.copy()
                        images.append(img_copy)
                        
                except Exception as img_error:
                    self.logger.warning(f"Failed to load image {image_path}: {img_error}")
                    continue
            
            if not images:
                return {
                    'success': False,
                    'message': 'No valid images could be loaded'
                }
            
            # Ensure all images have the same size (resize to first image size)
            base_size = images[0].size
            resized_images = []
            
            for img in images:
                if img.size != base_size:
                    img_resized = img.resize(base_size, Image.Resampling.LANCZOS)
                    resized_images.append(img_resized)
                else:
                    resized_images.append(img)
            
            # Prepare save parameters
            save_kwargs = {
                'save_all': True,
                'append_images': resized_images[1:] if len(resized_images) > 1 else [],
                'duration': frame_duration,
                'loop': loop_count,
                'disposal': 2,  # Restore background
                'optimize': optimize and quality_settings.get('optimize', True)
            }
            
            # Apply quality settings
            if 'colors' in quality_settings and quality_settings['colors'] < 256:
                # Convert to palette mode for color reduction
                first_image = resized_images[0]
                if dithering:
                    first_image = first_image.convert('P', dither=Image.Dither.FLOYDSTEINBERG, colors=quality_settings['colors'])
                else:
                    first_image = first_image.convert('P', colors=quality_settings['colors'])
                
                palette = first_image.getpalette()
                
                # Apply palette to all images
                palette_images = [first_image]
                for img in resized_images[1:]:
                    if dithering:
                        img_p = img.quantize(palette=first_image, dither=Image.Dither.FLOYDSTEINBERG)
                    else:
                        img_p = img.quantize(palette=first_image)
                    palette_images.append(img_p)
                
                # Update images and save parameters
                resized_images = palette_images
                save_kwargs['append_images'] = palette_images[1:] if len(palette_images) > 1 else []
            
            # Save GIF
            resized_images[0].save(output_path, 'GIF', **save_kwargs)
            
            # Get file information
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            # Verify the created GIF
            gif_info = self._get_gif_info(output_path)
            
            return {
                'success': True,
                'message': f'Successfully created GIF from {len(resized_images)} frames',
                'output_path': output_path,
                'output_filename': os.path.basename(output_path),
                'frame_count': len(resized_images),
                'file_size': file_size,
                'duration': frame_duration,
                'loop': loop_count,
                'optimize': optimize,
                'dithering': dithering,
                'gif_info': gif_info,
                'settings': {
                    'duration': frame_duration,
                    'loop': loop_count,
                    'optimize': optimize,
                    'dithering': dithering,
                    'quality_settings': quality_settings
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to create GIF: {str(e)}'
            }
    
    def get_gif_preview_data(self, gif_path: str, max_frames: int = 10) -> Dict[str, Any]:
        """
        Get preview data for a GIF file
        
        Args:
            gif_path: Path to GIF file
            max_frames: Maximum number of frames to include in preview
            
        Returns:
            Dictionary with preview data
        """
        try:
            with Image.open(gif_path) as gif:
                preview_frames = []
                frame_count = 0
                
                for i, frame in enumerate(ImageSequence.Iterator(gif)):
                    if i >= max_frames:
                        break
                    
                    # Convert frame to base64 for preview
                    import base64
                    import io
                    
                    if frame.mode != 'RGBA':
                        frame = frame.convert('RGBA')
                    
                    buffer = io.BytesIO()
                    frame.save(buffer, format='PNG')
                    frame_data = base64.b64encode(buffer.getvalue()).decode()
                    
                    preview_frames.append({
                        'index': i,
                        'duration': frame.info.get('duration', 100),
                        'data': f"data:image/png;base64,{frame_data}",
                        'size': frame.size
                    })
                    frame_count += 1
                
                return {
                    'success': True,
                    'frames': preview_frames,
                    'total_frames': getattr(gif, 'n_frames', frame_count),
                    'size': gif.size,
                    'is_animated': getattr(gif, 'is_animated', False)
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to generate preview: {str(e)}'
            }
    
    def _get_gif_info(self, gif_path: str) -> Dict[str, Any]:
        """Get detailed information about GIF file"""
        try:
            with Image.open(gif_path) as gif:
                # Basic info
                info = {
                    'format': gif.format,
                    'mode': gif.mode,
                    'size': gif.size,
                    'width': gif.width,
                    'height': gif.height,
                    'is_animated': getattr(gif, 'is_animated', False),
                    'n_frames': getattr(gif, 'n_frames', 1)
                }
                
                # Animation info
                if hasattr(gif, 'is_animated') and gif.is_animated:
                    durations = []
                    frame_count = 0
                    
                    for frame in ImageSequence.Iterator(gif):
                        durations.append(frame.info.get('duration', 100))
                        frame_count += 1
                    
                    info.update({
                        'frame_count': frame_count,
                        'durations': durations,
                        'total_duration': sum(durations),
                        'average_duration': sum(durations) / len(durations) if durations else 100,
                        'loop_count': gif.info.get('loop', 0)
                    })
                
                # File info
                file_size = os.path.getsize(gif_path) if os.path.exists(gif_path) else 0
                info['file_size'] = file_size
                
                return info
                
        except Exception as e:
            return {'error': f"Failed to get GIF info: {str(e)}"}
    
    def validate_gif(self, gif_path: str) -> Tuple[bool, str]:
        """
        Validate GIF file
        
        Args:
            gif_path: Path to GIF file
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(gif_path):
                return False, "File does not exist"
            
            with Image.open(gif_path) as gif:
                if gif.format != 'GIF':
                    return False, f"File format is {gif.format}, expected GIF"
                
                # Check if it has frames
                frame_count = getattr(gif, 'n_frames', 1)
                if frame_count == 0:
                    return False, "GIF has no frames"
                
                # Check file size (50MB limit)
                file_size = os.path.getsize(gif_path)
                max_size = 50 * 1024 * 1024
                if file_size > max_size:
                    return False, f"File too large ({self.format_file_size(file_size)}), maximum 50MB"
                
                return True, f"Valid GIF file with {frame_count} frames"
                
        except Exception as e:
            return False, f"Error validating GIF: {str(e)}"
    
    def validate_image_sequence(self, image_paths: List[str]) -> Tuple[bool, str]:
        """
        Validate image sequence for GIF creation
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not image_paths:
                return False, "No images provided"
            
            if len(image_paths) > 500:  # Max frames limit
                return False, f"Too many images ({len(image_paths)}), maximum 500 allowed"
            
            valid_images = 0
            total_size = 0
            
            for image_path in image_paths:
                try:
                    if not os.path.exists(image_path):
                        continue
                    
                    with Image.open(image_path) as img:
                        # Check if it's a valid image
                        img.verify()
                        valid_images += 1
                        total_size += os.path.getsize(image_path)
                        
                except Exception:
                    continue
            
            if valid_images == 0:
                return False, "No valid images found"
            
            if valid_images < len(image_paths):
                return False, f"Only {valid_images} out of {len(image_paths)} images are valid"
            
            # Check total size (100MB total limit)
            max_total_size = 100 * 1024 * 1024
            if total_size > max_total_size:
                return False, f"Total file size too large ({self.format_file_size(total_size)}), maximum 100MB"
            
            return True, f"Valid image sequence with {valid_images} images"
            
        except Exception as e:
            return False, f"Error validating image sequence: {str(e)}"
    
    @staticmethod
    def get_supported_image_formats() -> List[str]:
        """Get list of supported image formats for sequence creation"""
        return ['PNG', 'JPEG', 'JPG', 'BMP', 'TIFF', 'WebP']
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
    
    def cleanup_temp_files(self, directory: str) -> None:
        """Clean up temporary files and directories"""
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory, ignore_errors=True)
                self.logger.info(f"Cleaned up temporary directory: {directory}")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup directory {directory}: {e}")
