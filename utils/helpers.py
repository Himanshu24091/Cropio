# utils/helpers.py
import time
import os
import concurrent.futures
import threading
from flask import current_app
from PIL import Image, ImageFile
import fitz  # PyMuPDF
import io
import zipfile
from typing import Dict, List, Tuple, Optional

# Enable loading of truncated images
ImageFile.LOAD_TRUNCATED_IMAGES = True

def allowed_file(filename, allowed_extensions):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size(file):
    """Get the size of an uploaded file object"""
    try:
        # Save current position
        current_position = file.tell()
        # Move to end
        file.seek(0, 2)
        size = file.tell()
        # Return to original position
        file.seek(current_position)
        return size
    except Exception as e:
        current_app.logger.error(f"Error getting file size: {e}")
        return 0

def get_optimal_dimensions(img: Image.Image, max_size: int = 1920) -> Tuple[int, int]:
    """Calculate optimal dimensions for image compression"""
    width, height = img.size
    if max(width, height) <= max_size:
        return width, height
    
    ratio = min(max_size / width, max_size / height)
    return int(width * ratio), int(height * ratio)

def compress_image_advanced(input_path: str, output_path: str, level: str, max_dimension: int = None) -> bool:
    """Advanced image compression with multiple optimization techniques"""
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if saving as JPEG
            if img.mode in ('RGBA', 'LA', 'P') and output_path.lower().endswith(('.jpg', '.jpeg')):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if needed
            if max_dimension:
                new_size = get_optimal_dimensions(img, max_dimension)
                if new_size != img.size:
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            file_format = img.format or 'JPEG'
            original_ext = os.path.splitext(output_path)[1].lower()
            
            # Enhanced quality mapping
            quality_settings = {
                'low': {'quality': 30, 'optimize': True, 'progressive': True},
                'medium': {'quality': 65, 'optimize': True, 'progressive': True},
                'high': {'quality': 85, 'optimize': True, 'progressive': False}
            }
            settings = quality_settings.get(level, quality_settings['medium'])
            
            if original_ext == '.png':
                # PNG optimization
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            elif original_ext in ['.jpg', '.jpeg']:
                # JPEG optimization
                img.save(output_path, 'JPEG', **settings)
            elif original_ext == '.webp':
                # WebP optimization with lossless option for high quality
                if level == 'high':
                    img.save(output_path, 'WebP', lossless=True, quality=100)
                else:
                    img.save(output_path, 'WebP', quality=settings['quality'], method=6)
            else:
                # Default to JPEG for other formats
                img.convert('RGB').save(output_path, 'JPEG', **settings)
                
        return True
    except Exception as e:
        current_app.logger.error(f"Error compressing image {input_path}: {e}")
        return False

def compress_image(input_path: str, output_path: str, level: str) -> bool:
    """Enhanced image compression wrapper"""
    max_dimensions = {'low': 1280, 'medium': 1920, 'high': None}
    return compress_image_advanced(input_path, output_path, level, max_dimensions.get(level))

def compress_pdf_advanced(input_path: str, output_path: str, level: str) -> bool:
    """Advanced PDF compression with image optimization"""
    try:
        doc = fitz.open(input_path)
        
        # Compression settings based on level
        compression_settings = {
            'low': {'garbage': 1, 'image_quality': 30},
            'medium': {'garbage': 2, 'image_quality': 60},
            'high': {'garbage': 4, 'image_quality': 80}
        }
        settings = compression_settings.get(level, compression_settings['medium'])
        
        # Process each page to optimize images
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Get image list from page
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                try:
                    # Extract image
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Compress image in memory
                    if image_ext in ['png', 'jpg', 'jpeg']:
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        
                        # Resize large images
                        if max(pil_image.size) > 1024:
                            new_size = get_optimal_dimensions(pil_image, 1024)
                            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
                        
                        # Compress and save back
                        output_buffer = io.BytesIO()
                        if image_ext == 'png':
                            pil_image.save(output_buffer, 'PNG', optimize=True)
                        else:
                            if pil_image.mode in ('RGBA', 'LA', 'P'):
                                pil_image = pil_image.convert('RGB')
                            pil_image.save(output_buffer, 'JPEG', 
                                         quality=settings['image_quality'], optimize=True)
                        
                        # Replace image in PDF
                        compressed_image = output_buffer.getvalue()
                        if len(compressed_image) < len(image_bytes):  # Only if smaller
                            doc._update_stream(xref, compressed_image)
                            
                except Exception as img_error:
                    # Skip this image if compression fails
                    current_app.logger.warning(f"Failed to compress image in PDF: {img_error}")
                    continue
        
        # Save with compression settings
        doc.save(output_path, 
                garbage=settings['garbage'], 
                deflate=True, 
                clean=True,
                linear=True,  # Optimize for web viewing
                pretty=False)  # Remove pretty formatting to save space
        doc.close()
        return True
        
    except Exception as e:
        current_app.logger.error(f"Error compressing PDF {input_path}: {e}")
        return False

def compress_pdf(input_path: str, output_path: str, level: str) -> bool:
    """Enhanced PDF compression wrapper"""
    return compress_pdf_advanced(input_path, output_path, level)

def batch_compress_files(file_tasks: List[Dict], task_id: str) -> List[Dict]:
    """Compress multiple files in parallel"""
    results = []
    total_files = len(file_tasks)
    
    def compress_single_file(task_data: Dict, index: int) -> Dict:
        try:
            input_path = task_data['input_path']
            output_path = task_data['output_path']
            level = task_data['level']
            filename = task_data['filename']
            is_image = task_data['is_image']
            
            # Update progress
            progress = int((index / total_files) * 100)
            
            original_size = os.path.getsize(input_path)
            
            # Compress file
            if is_image:
                success = compress_image(input_path, output_path, level)
            else:
                success = compress_pdf(input_path, output_path, level)
            
            if success and os.path.exists(output_path):
                compressed_size = os.path.getsize(output_path)
                reduction_percent = ((original_size - compressed_size) / original_size * 100) if original_size > 0 else 0
                
                return {
                    'filename': filename,
                    'original_size': original_size,
                    'compressed_size': compressed_size,
                    'reduction_percent': round(reduction_percent, 2),
                    'success': True
                }
            else:
                return {
                    'filename': filename,
                    'error': 'Failed to compress file',
                    'success': False
                }
                
        except Exception as e:
            return {
                'filename': task_data.get('filename', 'Unknown'),
                'error': f'Error during compression: {str(e)}',
                'success': False
            }
    
    # Use ThreadPoolExecutor for I/O bound operations
    max_workers = min(4, len(file_tasks))  # Limit concurrent operations
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {executor.submit(compress_single_file, task, i): i 
                         for i, task in enumerate(file_tasks)}
        
        for future in concurrent.futures.as_completed(future_to_task):
            result = future.result()
            results.append(result)
    
    return results

def create_zip_archive(file_paths: List[str], zip_path: str, base_names: List[str] = None) -> bool:
    """Create a ZIP archive from multiple files"""
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for i, file_path in enumerate(file_paths):
                if os.path.exists(file_path):
                    arc_name = base_names[i] if base_names and i < len(base_names) else os.path.basename(file_path)
                    zipf.write(file_path, arc_name)
        return True
    except Exception as e:
        current_app.logger.error(f"Error creating ZIP archive: {e}")
        return False

def cleanup_old_files(max_age_hours=1):
    """Cleanup old files from upload directories"""
    try:
        now = time.time()
        cutoff = now - (max_age_hours * 3600)  # Convert hours to seconds
        
        # Common upload directories
        upload_dirs = ['uploads', 'outputs', 'compressed']
        
        for upload_dir in upload_dirs:
            if os.path.exists(upload_dir):
                try:
                    for filename in os.listdir(upload_dir):
                        file_path = os.path.join(upload_dir, filename)
                        if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                            os.remove(file_path)
                            current_app.logger.info(f"Cleaned up old file: {filename}")
                except Exception as e:
                    current_app.logger.error(f"Error during cleanup in {upload_dir}: {e}")
                    
    except Exception as e:
        current_app.logger.error(f"Error during file cleanup: {e}")

def cleanup_files():
    """Background cleanup function for old files - Fixed for APScheduler"""
    try:
        now = time.time()
        cutoff = now - 3600  # 1 hour
        
        # Define cleanup directories relative to current working directory
        cleanup_dirs = ['uploads', 'compressed', 'outputs']
        
        for dir_name in cleanup_dirs:
            if os.path.exists(dir_name):
                try:
                    for filename in os.listdir(dir_name):
                        file_path = os.path.join(dir_name, filename)
                        if os.path.isfile(file_path):
                            file_age = now - os.path.getmtime(file_path)
                            if file_age > 3600:  # Older than 1 hour
                                os.remove(file_path)
                                print(f"APScheduler: Cleaned up old file: {filename} from {dir_name}")
                except Exception as e:
                    print(f"APScheduler: Error during cleanup in {dir_name}: {e}")
                    
    except Exception as e:
        print(f"APScheduler: Error during file cleanup: {e}")
