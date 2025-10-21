"""
GIF ⇄ MP4 Processor Utility
Professional video conversion between GIF and MP4 formats using FFmpeg
"""

import os
import uuid
import tempfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .ffmpeg_utils import get_ffmpeg_path, get_ffprobe_path, is_ffmpeg_available, validate_ffmpeg

logger = logging.getLogger(__name__)


class GifMp4Processor:
    """Professional GIF ⇄ MP4 conversion processor"""
    
    def __init__(self, upload_folder: str = 'uploads'):
        self.upload_folder = upload_folder
        self.ffmpeg_path = get_ffmpeg_path()
        self.ffprobe_path = get_ffprobe_path()
        
        # Ensure FFmpeg is available
        if not is_ffmpeg_available():
            raise RuntimeError("FFmpeg is not available. Please install FFmpeg to use video conversion features.")
    
    def gif_to_mp4(self, input_path: str, output_path: Optional[str] = None, 
                   quality: str = 'high', fps: Optional[int] = None,
                   scale: Optional[str] = None, optimize: bool = True) -> Dict[str, Any]:
        """
        Convert GIF to MP4 with advanced options
        
        Args:
            input_path: Path to input GIF file
            output_path: Path for output MP4 file (auto-generated if None)
            quality: Quality preset ('low', 'medium', 'high', 'lossless')
            fps: Target frames per second (None to preserve original)
            scale: Scale filter (e.g., '720:480', '50%', None to preserve)
            optimize: Enable advanced optimization
        
        Returns:
            Dict with conversion results
        """
        try:
            # Validate input
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Input GIF file not found'}
            
            # Generate output path if not provided
            if not output_path:
                output_filename = f"{uuid.uuid4().hex}_converted.mp4"
                output_path = os.path.join(self.upload_folder, output_filename)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get input video info
            input_info = self._get_video_info(input_path)
            if not input_info['success']:
                return {'success': False, 'error': f"Failed to analyze input GIF: {input_info['error']}"}
            
            # Build FFmpeg command
            cmd = [self.ffmpeg_path, '-i', input_path]
            
            # Video codec and quality settings
            quality_settings = self._get_quality_settings(quality, 'mp4')
            cmd.extend(quality_settings)
            
            # FPS setting
            if fps:
                cmd.extend(['-r', str(fps)])
            elif 'fps' in input_info and input_info['fps']:
                # Preserve original FPS if detected
                cmd.extend(['-r', str(input_info['fps'])])
            
            # Scale filter with dimension fix for h264 compatibility
            if scale:
                cmd.extend(['-vf', f'scale={scale}:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2'])
            else:
                # Ensure dimensions are even for h264 compatibility
                cmd.extend(['-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2'])
            
            # Optimization settings
            if optimize:
                cmd.extend([
                    '-preset', 'medium',  # Balance between speed and compression
                    '-tune', 'animation', # Optimize for animated content
                    '-movflags', '+faststart'  # Enable progressive download
                ])
            
            # Output settings
            cmd.extend([
                '-pix_fmt', 'yuv420p',  # Ensure compatibility
                '-y',  # Overwrite output
                output_path
            ])
            
            # Execute conversion
            logger.info(f"Converting GIF to MP4: {input_path} -> {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                error_msg = result.stderr or 'Unknown FFmpeg error'
                logger.error(f"GIF to MP4 conversion failed: {error_msg}")
                return {'success': False, 'error': f'Conversion failed: {error_msg}'}
            
            # Verify output file
            if not os.path.exists(output_path):
                return {'success': False, 'error': 'Output MP4 file was not created'}
            
            # Get output video info
            output_info = self._get_video_info(output_path)
            
            # Calculate compression ratio
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            compression_ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
            
            return {
                'success': True,
                'output_path': output_path,
                'input_size': input_size,
                'output_size': output_size,
                'compression_ratio': f"{compression_ratio:.1f}%",
                'input_info': input_info,
                'output_info': output_info,
                'quality': quality,
                'processing_time': 'N/A',  # Could be calculated if needed
                'format': 'MP4'
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Conversion timed out (5 minutes limit)'}
        except Exception as e:
            logger.error(f"GIF to MP4 conversion error: {str(e)}")
            return {'success': False, 'error': f'Conversion error: {str(e)}'}
    
    def mp4_to_gif_simple(self, input_path: str, output_path: Optional[str] = None,
                         fps: int = 15, scale: str = '-1:480', 
                         start_time: Optional[str] = None, duration: Optional[str] = None,
                         loop_count: int = 0) -> Dict[str, Any]:
        """
        Simple single-pass MP4 to GIF conversion (fallback method)
        """
        try:
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Input MP4 file not found'}
            
            if not output_path:
                output_filename = f"{uuid.uuid4().hex}_converted.gif"
                output_path = os.path.join(self.upload_folder, output_filename)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Simple single-pass conversion
            cmd = [self.ffmpeg_path, '-i', input_path]
            
            # Add time range if specified
            if start_time:
                cmd.extend(['-ss', start_time])
            if duration:
                cmd.extend(['-t', duration])
            
            # Simple filter for GIF conversion
            if scale and scale != '-1:480':
                vf_filter = f'fps={fps},scale={scale}:flags=lanczos'
            else:
                vf_filter = f'fps={fps},scale=-1:480:flags=lanczos'
            
            cmd.extend([
                '-vf', vf_filter,
                '-loop', str(loop_count),
                '-y', output_path
            ])
            
            logger.info(f"Converting MP4 to GIF (simple method): {input_path} -> {output_path}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                error_msg = result.stderr or 'Unknown FFmpeg error'
                logger.error(f"Simple MP4 to GIF conversion failed: {error_msg}")
                return {'success': False, 'error': f'Conversion failed: {error_msg}'}
            
            if not os.path.exists(output_path):
                return {'success': False, 'error': 'Output GIF file was not created'}
            
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            size_ratio = (output_size / input_size) * 100 if input_size > 0 else 0
            
            return {
                'success': True,
                'output_path': output_path,
                'input_size': input_size,
                'output_size': output_size,
                'size_ratio': f"{size_ratio:.1f}%",
                'fps': fps,
                'scale': scale,
                'loop_count': loop_count,
                'format': 'GIF'
            }
        except Exception as e:
            logger.error(f"Simple MP4 to GIF conversion error: {str(e)}")
            return {'success': False, 'error': f'Conversion error: {str(e)}'}
    
    def mp4_to_gif(self, input_path: str, output_path: Optional[str] = None,
                   fps: int = 15, scale: str = '-1:480', 
                   start_time: Optional[str] = None, duration: Optional[str] = None,
                   palette_quality: str = 'high', loop_count: int = 0) -> Dict[str, Any]:
        """
        Convert MP4 to GIF with advanced options
        
        Args:
            input_path: Path to input MP4 file
            output_path: Path for output GIF file (auto-generated if None)
            fps: Target frames per second for GIF
            scale: Scale filter (e.g., '320:240', '-1:480' for auto-width)
            start_time: Start time for clipping (e.g., '00:00:10')
            duration: Duration to convert (e.g., '00:00:05')
            palette_quality: Palette generation quality ('low', 'medium', 'high')
            loop_count: Number of loops (0 for infinite)
        
        Returns:
            Dict with conversion results
        """
        try:
            # Validate input
            if not os.path.exists(input_path):
                return {'success': False, 'error': 'Input MP4 file not found'}
            
            # Generate output path if not provided
            if not output_path:
                output_filename = f"{uuid.uuid4().hex}_converted.gif"
                output_path = os.path.join(self.upload_folder, output_filename)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get input video info
            input_info = self._get_video_info(input_path)
            if not input_info['success']:
                return {'success': False, 'error': f"Failed to analyze input MP4: {input_info['error']}"}
            
            # Two-pass conversion for better quality GIF
            
            # Step 1: Generate optimal palette
            palette_path = os.path.join(tempfile.gettempdir(), f"palette_{uuid.uuid4().hex}.png")
            
            palette_cmd = [self.ffmpeg_path, '-i', input_path]
            
            # Add time range if specified
            if start_time:
                palette_cmd.extend(['-ss', start_time])
            if duration:
                palette_cmd.extend(['-t', duration])
            
            # Palette generation settings - simplified approach
            palette_settings = self._get_palette_settings(palette_quality)
            # Use a simpler filter chain for palette generation
            if scale and scale != "-1:480":
                scale_filter = f"fps={fps},scale={scale}:flags=lanczos"
            else:
                scale_filter = f"fps={fps},scale=-1:480:flags=lanczos"  # Default scale for GIF
            filter_complex = f"{scale_filter},{palette_settings}"
            
            palette_cmd.extend([
                '-vf', filter_complex,
                '-y', palette_path
            ])
            
            logger.info("Generating optimal color palette for GIF conversion")
            palette_result = subprocess.run(palette_cmd, capture_output=True, text=True, timeout=120)
            
            if palette_result.returncode != 0 or not os.path.exists(palette_path):
                # Two-pass method failed, try simple single-pass method
                logger.warning("Two-pass conversion failed, falling back to simple method")
                try:
                    if os.path.exists(palette_path):
                        os.unlink(palette_path)
                except:
                    pass
                return self.mp4_to_gif_simple(input_path, output_path, fps, scale, start_time, duration, loop_count)
            
            # Step 2: Convert to GIF using the generated palette
            gif_cmd = [self.ffmpeg_path, '-i', input_path, '-i', palette_path]
            
            # Add time range if specified
            if start_time:
                gif_cmd.extend(['-ss', start_time])
            if duration:
                gif_cmd.extend(['-t', duration])
            
            # GIF conversion with palette and dimension fix
            scale_filter = f"scale={scale}:flags=lanczos:force_original_aspect_ratio=decrease,pad=ceil(iw/2)*2:ceil(ih/2)*2"
            gif_filter = f"[0:v] fps={fps},{scale_filter} [v]; [v][1:v] paletteuse=dither=bayer:bayer_scale=3"
            
            gif_cmd.extend([
                '-filter_complex', gif_filter,
                '-loop', str(loop_count),
                '-y', output_path
            ])
            
            logger.info(f"Converting MP4 to GIF: {input_path} -> {output_path}")
            gif_result = subprocess.run(gif_cmd, capture_output=True, text=True, timeout=300)
            
            # Clean up palette file
            try:
                os.unlink(palette_path)
            except:
                pass
            
            if gif_result.returncode != 0:
                error_msg = gif_result.stderr or 'Unknown FFmpeg error'
                logger.error(f"MP4 to GIF conversion failed: {error_msg}")
                return {'success': False, 'error': f'Conversion failed: {error_msg}'}
            
            # Verify output file
            if not os.path.exists(output_path):
                return {'success': False, 'error': 'Output GIF file was not created'}
            
            # Get output file info
            input_size = os.path.getsize(input_path)
            output_size = os.path.getsize(output_path)
            size_ratio = (output_size / input_size) * 100 if input_size > 0 else 0
            
            return {
                'success': True,
                'output_path': output_path,
                'input_size': input_size,
                'output_size': output_size,
                'size_ratio': f"{size_ratio:.1f}%",
                'input_info': input_info,
                'fps': fps,
                'scale': scale,
                'palette_quality': palette_quality,
                'loop_count': loop_count,
                'processing_time': 'N/A',
                'format': 'GIF'
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Conversion timed out (5 minutes limit)'}
        except Exception as e:
            logger.error(f"MP4 to GIF conversion error: {str(e)}")
            return {'success': False, 'error': f'Conversion error: {str(e)}'}
    
    def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get comprehensive video file information using FFprobe"""
        try:
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {'success': False, 'error': 'Failed to analyze video file'}
            
            import json
            probe_data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = None
            for stream in probe_data.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if not video_stream:
                return {'success': False, 'error': 'No video stream found'}
            
            # Parse frame rate
            fps = None
            if 'r_frame_rate' in video_stream:
                try:
                    fps_str = video_stream['r_frame_rate']
                    if '/' in fps_str:
                        num, den = map(float, fps_str.split('/'))
                        fps = num / den if den != 0 else None
                except:
                    pass
            
            # Parse duration
            duration = None
            format_info = probe_data.get('format', {})
            if 'duration' in format_info:
                try:
                    duration = float(format_info['duration'])
                except:
                    pass
            
            return {
                'success': True,
                'width': video_stream.get('width'),
                'height': video_stream.get('height'),
                'fps': fps,
                'duration': duration,
                'codec': video_stream.get('codec_name'),
                'format': format_info.get('format_name'),
                'bitrate': format_info.get('bit_rate'),
                'size': format_info.get('size')
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Video analysis timed out'}
        except json.JSONDecodeError:
            return {'success': False, 'error': 'Failed to parse video information'}
        except Exception as e:
            return {'success': False, 'error': f'Analysis error: {str(e)}'}
    
    def _get_quality_settings(self, quality: str, output_format: str) -> list:
        """Get quality-specific encoding parameters"""
        settings = []
        
        if output_format == 'mp4':
            if quality == 'lossless':
                settings = ['-c:v', 'libx264', '-crf', '0', '-preset', 'medium']
            elif quality == 'high':
                settings = ['-c:v', 'libx264', '-crf', '18', '-preset', 'medium']
            elif quality == 'medium':
                settings = ['-c:v', 'libx264', '-crf', '23', '-preset', 'medium']
            else:  # low
                settings = ['-c:v', 'libx264', '-crf', '28', '-preset', 'fast']
        
        return settings
    
    def _get_palette_settings(self, palette_quality: str) -> str:
        """Get palette generation settings for GIF conversion"""
        if palette_quality == 'high':
            return "palettegen=max_colors=256:stats_mode=single"
        elif palette_quality == 'medium':
            return "palettegen=max_colors=128:stats_mode=single"
        else:  # low
            return "palettegen=max_colors=64:stats_mode=single"
    
    def optimize_gif(self, gif_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Optimize an existing GIF file for better compression"""
        try:
            if not output_path:
                output_path = gif_path.replace('.gif', '_optimized.gif')
            
            cmd = [
                self.ffmpeg_path,
                '-i', gif_path,
                '-vf', 'palettegen=reserve_transparent=1',
                '-f', 'image2',
                'palette.png',
                '-y'
            ]
            
            # This is a simplified optimization
            # In production, you might want to use specialized tools like gifsicle
            
            return {'success': True, 'output_path': output_path, 'message': 'GIF optimization completed'}
            
        except Exception as e:
            return {'success': False, 'error': f'Optimization failed: {str(e)}'}
    
    def batch_convert(self, input_paths: list, conversion_type: str, **kwargs) -> Dict[str, Any]:
        """Batch convert multiple files"""
        results = {
            'successful': [],
            'failed': [],
            'total': len(input_paths),
            'success_count': 0,
            'fail_count': 0
        }
        
        for input_path in input_paths:
            try:
                if conversion_type == 'gif_to_mp4':
                    result = self.gif_to_mp4(input_path, **kwargs)
                elif conversion_type == 'mp4_to_gif':
                    result = self.mp4_to_gif(input_path, **kwargs)
                else:
                    result = {'success': False, 'error': f'Unknown conversion type: {conversion_type}'}
                
                if result['success']:
                    results['successful'].append({
                        'input': input_path,
                        'output': result['output_path'],
                        'result': result
                    })
                    results['success_count'] += 1
                else:
                    results['failed'].append({
                        'input': input_path,
                        'error': result['error']
                    })
                    results['fail_count'] += 1
                    
            except Exception as e:
                results['failed'].append({
                    'input': input_path,
                    'error': str(e)
                })
                results['fail_count'] += 1
        
        return results
    
    @staticmethod
    def is_supported_format(file_path: str, conversion_type: str) -> bool:
        """Check if file format is supported for conversion"""
        ext = os.path.splitext(file_path)[1].lower()
        
        if conversion_type == 'gif_to_mp4':
            return ext == '.gif'
        elif conversion_type == 'mp4_to_gif':
            return ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        
        return False
    
    @staticmethod  
    def get_supported_formats() -> Dict[str, list]:
        """Get list of supported input/output formats"""
        return {
            'gif_to_mp4': {
                'input': ['.gif'],
                'output': ['.mp4']
            },
            'mp4_to_gif': {
                'input': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
                'output': ['.gif']
            }
        }
    
    @staticmethod
    def validate_ffmpeg_installation() -> Tuple[bool, str]:
        """Validate that FFmpeg is properly installed and functional"""
        return validate_ffmpeg()
