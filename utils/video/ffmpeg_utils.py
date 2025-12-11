"""
FFmpeg Utilities - Robust FFmpeg Detection and Path Resolution
Handles environment variables, config, local bin, and system PATH resolution
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import platform

logger = logging.getLogger(__name__)

class FFmpegManager:
    """Centralized FFmpeg path resolution and availability checking"""
    
    def __init__(self):
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self._availability_cache = None
        self._paths_resolved = False
    
    def _get_executable_name(self, base_name: str) -> str:
        """Get correct executable name for current platform"""
        if platform.system() == 'Windows':
            return f"{base_name}.exe"
        return base_name
    
    def _resolve_paths(self) -> None:
        """Resolve FFmpeg and FFprobe paths using multiple strategies"""
        if self._paths_resolved:
            return
            
        ffmpeg_exe = self._get_executable_name('ffmpeg')
        ffprobe_exe = self._get_executable_name('ffprobe')
        
        # Strategy 1: Environment variables (highest priority)
        if os.environ.get('FFMPEG_PATH'):
            env_path = Path(os.environ['FFMPEG_PATH'])
            if env_path.is_file() and env_path.exists():
                self.ffmpeg_path = str(env_path)
                self.ffprobe_path = str(env_path.parent / ffprobe_exe)
                logger.info(f"FFmpeg found via FFMPEG_PATH: {self.ffmpeg_path}")
                self._paths_resolved = True
                return
                
        # Strategy 2: Local project bin directory
        try:
            project_root = Path(__file__).parent.parent.parent
            local_ffmpeg = project_root / 'bin' / ffmpeg_exe
            local_ffprobe = project_root / 'bin' / ffprobe_exe
            
            if local_ffmpeg.exists() and local_ffprobe.exists():
                self.ffmpeg_path = str(local_ffmpeg.resolve())
                self.ffprobe_path = str(local_ffprobe.resolve())
                logger.info(f"FFmpeg found in local bin: {self.ffmpeg_path}")
                self._paths_resolved = True
                return
        except Exception as e:
            logger.debug(f"Local bin check failed: {e}")
        
        # Strategy 3: System PATH
        try:
            ffmpeg_system = subprocess.run(['where' if platform.system() == 'Windows' else 'which', ffmpeg_exe], 
                                         capture_output=True, text=True, timeout=5)
            if ffmpeg_system.returncode == 0:
                self.ffmpeg_path = ffmpeg_system.stdout.strip().split('\n')[0]
                
                ffprobe_system = subprocess.run(['where' if platform.system() == 'Windows' else 'which', ffprobe_exe],
                                              capture_output=True, text=True, timeout=5)
                if ffprobe_system.returncode == 0:
                    self.ffprobe_path = ffprobe_system.stdout.strip().split('\n')[0]
                    logger.info(f"FFmpeg found in system PATH: {self.ffmpeg_path}")
                    self._paths_resolved = True
                    return
        except Exception as e:
            logger.debug(f"System PATH check failed: {e}")
        
        # Strategy 4: Common installation paths (fallback)
        common_paths = []
        if platform.system() == 'Windows':
            common_paths = [
                Path('C:/ffmpeg/bin'),
                Path('C:/Program Files/ffmpeg/bin'),
                Path('C:/Program Files (x86)/ffmpeg/bin'),
                Path(os.path.expanduser('~/AppData/Local/Microsoft/WinGet/Packages/*/ffmpeg-*-essentials_build/bin'))
            ]
        else:
            common_paths = [
                Path('/usr/bin'),
                Path('/usr/local/bin'),
                Path('/opt/homebrew/bin'),
                Path('/snap/bin')
            ]
        
        for path_dir in common_paths:
            try:
                if '*' in str(path_dir):
                    # Handle wildcard paths (like WinGet)
                    from glob import glob
                    for expanded_path in glob(str(path_dir)):
                        expanded_path = Path(expanded_path)
                        if (expanded_path / ffmpeg_exe).exists():
                            self.ffmpeg_path = str(expanded_path / ffmpeg_exe)
                            self.ffprobe_path = str(expanded_path / ffprobe_exe)
                            logger.info(f"FFmpeg found in common path: {self.ffmpeg_path}")
                            self._paths_resolved = True
                            return
                else:
                    if path_dir.exists() and (path_dir / ffmpeg_exe).exists():
                        self.ffmpeg_path = str(path_dir / ffmpeg_exe)
                        self.ffprobe_path = str(path_dir / ffprobe_exe)
                        logger.info(f"FFmpeg found in common path: {self.ffmpeg_path}")
                        self._paths_resolved = True
                        return
            except Exception as e:
                logger.debug(f"Common path check failed for {path_dir}: {e}")
        
        # No paths found
        logger.warning("FFmpeg not found in any location")
        self.ffmpeg_path = ffmpeg_exe  # Fallback to bare command
        self.ffprobe_path = ffprobe_exe
        self._paths_resolved = True
    
    def get_ffmpeg_path(self) -> str:
        """Get resolved FFmpeg executable path"""
        self._resolve_paths()
        return self.ffmpeg_path or self._get_executable_name('ffmpeg')
    
    def get_ffprobe_path(self) -> str:
        """Get resolved FFprobe executable path"""
        self._resolve_paths()
        return self.ffprobe_path or self._get_executable_name('ffprobe')
    
    def check_availability(self, force_recheck: bool = False) -> bool:
        """Check if FFmpeg is available and working"""
        if self._availability_cache is not None and not force_recheck:
            return self._availability_cache
        
        try:
            ffmpeg_path = self.get_ffmpeg_path()
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and 'ffmpeg version' in result.stdout.lower():
                logger.info("FFmpeg availability confirmed")
                self._availability_cache = True
                return True
            else:
                logger.warning(f"FFmpeg version check failed: {result.stderr}")
                self._availability_cache = False
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg availability check timed out")
            self._availability_cache = False
            return False
        except FileNotFoundError:
            logger.error("FFmpeg executable not found")
            self._availability_cache = False
            return False
        except Exception as e:
            logger.error(f"FFmpeg availability check failed: {e}")
            self._availability_cache = False
            return False
    
    def get_version_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed FFmpeg version and codec information"""
        if not self.check_availability():
            return None
        
        try:
            result = subprocess.run([self.get_ffmpeg_path(), '-version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                version_line = lines[0] if lines else ""
                
                # Extract version number
                version = "unknown"
                if 'version' in version_line.lower():
                    parts = version_line.split()
                    for i, part in enumerate(parts):
                        if part.lower() == 'version' and i + 1 < len(parts):
                            version = parts[i + 1]
                            break
                
                return {
                    'version': version,
                    'full_version': version_line,
                    'ffmpeg_path': self.get_ffmpeg_path(),
                    'ffprobe_path': self.get_ffprobe_path()
                }
        except Exception as e:
            logger.error(f"Failed to get FFmpeg version info: {e}")
        
        return None
    
    def validate_installation(self) -> Tuple[bool, str]:
        """Comprehensive validation of FFmpeg installation"""
        if not self.check_availability():
            return False, "FFmpeg not available or not working"
        
        try:
            # Test FFprobe
            ffprobe_result = subprocess.run([self.get_ffprobe_path(), '-version'],
                                          capture_output=True, text=True, timeout=10)
            if ffprobe_result.returncode != 0:
                return False, "FFprobe not working correctly"
            
            # Test basic encoding capability with libx264
            test_cmd = [self.get_ffmpeg_path(), '-f', 'lavfi', '-i', 'testsrc2=duration=1:size=320x240:rate=1',
                       '-c:v', 'libx264', '-preset', 'ultrafast', '-f', 'null', '-']
            
            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=15)
            
            if test_result.returncode != 0:
                return False, f"FFmpeg encoding test failed: {test_result.stderr}"
            
            version_info = self.get_version_info()
            return True, f"FFmpeg {version_info['version'] if version_info else 'unknown'} fully functional"
            
        except subprocess.TimeoutExpired:
            return False, "FFmpeg validation timed out"
        except Exception as e:
            return False, f"Validation error: {str(e)}"


# Global instance
ffmpeg_manager = FFmpegManager()

# Convenience functions
def get_ffmpeg_path() -> str:
    """Get FFmpeg executable path"""
    return ffmpeg_manager.get_ffmpeg_path()

def get_ffprobe_path() -> str:
    """Get FFprobe executable path"""
    return ffmpeg_manager.get_ffprobe_path()

def is_ffmpeg_available() -> bool:
    """Check if FFmpeg is available"""
    return ffmpeg_manager.check_availability()

def get_ffmpeg_info() -> Optional[Dict[str, Any]]:
    """Get FFmpeg version and installation info"""
    return ffmpeg_manager.get_version_info()

def validate_ffmpeg() -> Tuple[bool, str]:
    """Validate FFmpeg installation comprehensively"""
    return ffmpeg_manager.validate_installation()
