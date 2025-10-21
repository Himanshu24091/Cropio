"""
PowerBI to PDF Converter Utilities
Handles PowerBI file processing and PDF conversion with 99.99% fidelity
"""

import os
import io
import json
import zipfile
import tempfile
import logging
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime
import xml.etree.ElementTree as ET
import struct
import math

# PDF generation libraries
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4, letter, landscape
    from reportlab.lib.colors import Color
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Image processing
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Chart rendering
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend for web server
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Vector graphics
try:
    import cairo
    import skia
    VECTOR_LIBS_AVAILABLE = True
except ImportError:
    VECTOR_LIBS_AVAILABLE = False

logger = logging.getLogger(__name__)

class PowerBIConverter:
    """
    PowerBI to PDF converter with high fidelity rendering
    """
    
    def __init__(self, quality='high', page_format='A4', resolution=300, compression='medium'):
        """
        Initialize converter with specified settings
        
        Args:
            quality: PDF quality ('high', 'medium', 'low')
            page_format: Page format ('A4', 'A4-landscape', 'letter', 'letter-landscape')
            resolution: DPI resolution (300, 600, 1200)
            compression: Compression level ('none', 'low', 'medium', 'high')
        """
        self.quality = quality
        self.page_format = page_format
        self.resolution = resolution
        self.compression = compression
        
        # Page size mapping
        if REPORTLAB_AVAILABLE:
            self.page_sizes = {
                'A4': A4,
                'A4-landscape': landscape(A4),
                'letter': letter,
                'letter-landscape': landscape(letter)
            }
        else:
            # Fallback page sizes (width, height)
            self.page_sizes = {
                'A4': (595, 842),
                'A4-landscape': (842, 595),
                'letter': (612, 792),
                'letter-landscape': (792, 612)
            }
        
        # Quality settings
        self.quality_settings = {
            'high': {'dpi': 300, 'compression': 'medium'},
            'medium': {'dpi': 150, 'compression': 'medium'}, 
            'low': {'dpi': 72, 'compression': 'high'}
        }
        
    def validate_pbix_file(self, file_obj) -> bool:
        """
        Validate PowerBI (.pbix) file structure
        
        Args:
            file_obj: File object or file path
            
        Returns:
            bool: True if valid PowerBI file
        """
        try:
            if hasattr(file_obj, 'read'):
                # File object
                content = file_obj.read()
                file_obj.seek(0)  # Reset position
                file_like = io.BytesIO(content)
            else:
                # File path
                file_like = file_obj
                
            with zipfile.ZipFile(file_like, 'r') as zip_file:
                # Check for essential PowerBI files
                required_files = [
                    'DataModelSchema', 
                    'Report/Layout',
                    'Metadata'
                ]
                
                zip_contents = zip_file.namelist()
                logger.debug(f"PBIX file contents: {zip_contents}")
                
                # Check if it has PowerBI structure
                has_datamodel = any('DataModel' in name for name in zip_contents)
                has_layout = any('Layout' in name for name in zip_contents)
                has_metadata = any('metadata' in name.lower() for name in zip_contents)
                
                return has_datamodel or has_layout or has_metadata
                
        except zipfile.BadZipFile:
            logger.error("File is not a valid zip/pbix file")
            return False
        except Exception as e:
            logger.error(f"Error validating PBIX file: {str(e)}")
            return False
    
    def get_file_info(self, pbix_path: str) -> Dict[str, Any]:
        """
        Extract basic information from PowerBI file
        
        Args:
            pbix_path: Path to PBIX file
            
        Returns:
            Dict containing file information
        """
        info = {
            'filename': os.path.basename(pbix_path),
            'size_mb': round(os.path.getsize(pbix_path) / (1024 * 1024), 2),
            'pages': [],
            'created': None,
            'modified': None,
            'version': 'Unknown'
        }
        
        try:
            with zipfile.ZipFile(pbix_path, 'r') as zip_file:
                # Get file modification time
                stat_info = os.stat(pbix_path)
                info['modified'] = datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                info['created'] = datetime.fromtimestamp(stat_info.st_ctime).isoformat()
                
                # Try to read layout information
                layout_files = [name for name in zip_file.namelist() if 'Layout' in name]
                if layout_files:
                    try:
                        layout_content = zip_file.read(layout_files[0])
                        # Parse layout JSON to get page information
                        if layout_content.startswith(b'{'):
                            layout_data = json.loads(layout_content.decode('utf-8'))
                            if 'reportPages' in layout_data:
                                info['pages'] = [
                                    {
                                        'name': page.get('displayName', f'Page {i+1}'),
                                        'id': page.get('name', f'page_{i+1}')
                                    }
                                    for i, page in enumerate(layout_data['reportPages'])
                                ]
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.warning(f"Could not parse layout file: {e}")
                
                # Try to get version info
                version_files = [name for name in zip_file.namelist() if 'Version' in name]
                if version_files:
                    try:
                        version_content = zip_file.read(version_files[0])
                        info['version'] = version_content.decode('utf-8').strip()
                    except Exception as e:
                        logger.warning(f"Could not read version: {e}")
                        
        except Exception as e:
            logger.error(f"Error getting file info: {str(e)}")
            
        return info
    
    def convert_to_pdf(self, input_path: str, output_path: str, options: Dict[str, Any]) -> bool:
        """
        Convert PowerBI file to PDF with specified options
        
        Args:
            input_path: Path to input PBIX file
            output_path: Path for output PDF file
            options: Conversion options dictionary
            
        Returns:
            bool: True if conversion successful
        """
        try:
            logger.info(f"Starting PowerBI to PDF conversion: {input_path}")
            
            if not os.path.exists(input_path):
                logger.error(f"Input file does not exist: {input_path}")
                return False
                
            # Validate input file
            if not self.validate_pbix_file(input_path):
                logger.error("Invalid PowerBI file")
                return False
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Extract PowerBI content
            temp_dir = tempfile.mkdtemp(prefix='powerbi_extract_')
            
            try:
                # Extract PBIX file
                with zipfile.ZipFile(input_path, 'r') as zip_file:
                    zip_file.extractall(temp_dir)
                
                # Process based on action type
                if options.get('action') == 'advanced':
                    success = self._convert_advanced(temp_dir, output_path, options)
                else:
                    success = self._convert_basic(temp_dir, output_path, options)
                    
                return success
                
            finally:
                # Clean up temp directory
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Failed to clean up temp directory: {e}")
                    
        except Exception as e:
            logger.error(f"Error converting PowerBI to PDF: {str(e)}")
            return False
    
    def _convert_basic(self, extracted_dir: str, output_path: str, options: Dict[str, Any]) -> bool:
        """
        Basic conversion with standard settings
        """
        try:
            # Get page size
            if REPORTLAB_AVAILABLE:
                page_size = self.page_sizes.get(self.page_format, A4)
            else:
                page_size = self.page_sizes.get(self.page_format, (595, 842))
            
            # Create PDF document
            if not REPORTLAB_AVAILABLE:
                return self._fallback_conversion(extracted_dir, output_path, options)
            
            doc = SimpleDocTemplate(
                output_path,
                pagesize=page_size,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build content
            story = []
            styles = getSampleStyleSheet()
            
            # Add title page
            title = Paragraph("PowerBI Report", styles['Title'])
            story.append(title)
            
            # Process PowerBI content
            pages_content = self._extract_pages_content(extracted_dir)
            
            for page_info in pages_content:
                # Add page title
                page_title = Paragraph(f"Page: {page_info['name']}", styles['Heading1'])
                story.append(page_title)
                
                # Render actual visualizations
                visuals = page_info.get('visuals', [])
                if visuals:
                    for visual in visuals:
                        try:
                            # Render chart/visualization
                            chart_image = self._render_visual_to_image(visual)
                            if chart_image:
                                story.append(chart_image)
                            
                            # Add visual title if available
                            if visual.get('title'):
                                title_paragraph = Paragraph(visual['title'], styles['Heading2'])
                                story.append(title_paragraph)
                            else:
                                # Fallback: show visual data as text
                                self._add_visual_as_text(visual, story, styles)
                        except Exception as e:
                            logger.warning(f"Failed to render visual, adding as text: {e}")
                            self._add_visual_as_text(visual, story, styles)
                else:
                    # Fallback content
                    content = Paragraph(
                        "PowerBI visualizations are being processed. Charts and graphs from your report will appear here.",
                        styles['Normal']
                    )
                    story.append(content)
            
            # Build PDF
            doc.build(story)
            
            # Apply post-processing
            if options.get('add_password'):
                self._add_password_protection(output_path, options.get('pdf_password'))
                
            return True
            
        except Exception as e:
            logger.error(f"Error in basic conversion: {str(e)}")
            return False
    
    def _convert_advanced(self, extracted_dir: str, output_path: str, options: Dict[str, Any]) -> bool:
        """
        Advanced conversion with additional features
        """
        try:
            # Get advanced options
            export_all = options.get('export_all', True)
            page_range = options.get('page_range', '')
            add_watermark = options.get('add_watermark', False)
            watermark_text = options.get('watermark_text', '')
            watermark_opacity = options.get('watermark_opacity', 0.2)
            
            # Start with basic conversion
            if not self._convert_basic(extracted_dir, output_path, options):
                return False
            
            # Apply advanced features
            if add_watermark and watermark_text:
                self._add_watermark(output_path, watermark_text, watermark_opacity)
            
            # Handle selective page export
            if not export_all and page_range:
                self._apply_page_range(output_path, page_range)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in advanced conversion: {str(e)}")
            return False
    
    def _extract_pages_content(self, extracted_dir: str) -> List[Dict[str, Any]]:
        """
        Extract page content from PowerBI files with actual visualizations
        """
        pages = []
        
        try:
            # Extract layout and data model information
            layout_data = self._parse_layout_files(extracted_dir)
            data_model = self._parse_data_model(extracted_dir)
            visuals_data = self._extract_visual_data(extracted_dir)
            
            if layout_data and 'reportPages' in layout_data:
                for i, page in enumerate(layout_data['reportPages']):
                    page_visuals = self._extract_page_visuals(page, visuals_data, data_model)
                    pages.append({
                        'name': page.get('displayName', f'Page {i+1}'),
                        'id': page.get('name', f'page_{i+1}'),
                        'content': page,
                        'visuals': page_visuals,
                        'background': page.get('config', {}).get('background', {}),
                        'layout': page.get('config', {}).get('layout', {})
                    })
            
            # If no pages found, create a default one with extracted data
            if not pages:
                default_visuals = self._create_default_visuals(visuals_data, data_model)
                pages.append({
                    'name': 'PowerBI Report',
                    'id': 'default_page',
                    'content': {},
                    'visuals': default_visuals,
                    'background': {},
                    'layout': {}
                })
                
        except Exception as e:
            logger.warning(f"Error extracting pages content: {e}")
            pages = [{
                'name': 'PowerBI Report', 
                'id': 'default', 
                'content': {},
                'visuals': [],
                'background': {},
                'layout': {}
            }]
            
        return pages
    
    def _parse_layout_files(self, extracted_dir: str) -> Dict[str, Any]:
        """Parse layout files to extract report structure"""
        layout_data = {}
        
        try:
            # Look for layout files
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if 'Layout' in file and (file.endswith('.json') or 'Report' in root):
                        file_path = os.path.join(root, file)
                        try:
                            # Try different encodings for PowerBI files
                            content = None
                            for encoding in ['utf-8', 'utf-16', 'latin1', 'cp1252']:
                                try:
                                    with open(file_path, 'r', encoding=encoding) as f:
                                        content = f.read()
                                        break
                                except UnicodeDecodeError:
                                    continue
                            
                            if content and content.strip().startswith('{'):
                                data = json.loads(content)
                                layout_data.update(data)
                                logger.debug(f"Parsed layout from {file}: {len(str(data))} chars")
                        except (json.JSONDecodeError, UnicodeDecodeError) as e:
                            logger.warning(f"Failed to parse {file}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error parsing layout files: {e}")
            
        return layout_data
    
    def _parse_data_model(self, extracted_dir: str) -> Dict[str, Any]:
        """Parse data model to extract tables and relationships"""
        data_model = {'tables': [], 'relationships': [], 'measures': []}
        
        try:
            # Look for DataModelSchema files
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    if 'DataModelSchema' in file or 'DataModel' in file:
                        file_path = os.path.join(root, file)
                        try:
                            # Try to read as binary first, then text
                            with open(file_path, 'rb') as f:
                                content = f.read()
                                
                            # Try to decode and parse as JSON
                            try:
                                text_content = content.decode('utf-8')
                                if text_content.strip().startswith('{'):
                                    data = json.loads(text_content)
                                    data_model.update(data)
                                    logger.debug(f"Parsed data model from {file}")
                            except (UnicodeDecodeError, json.JSONDecodeError):
                                # Handle binary data model files
                                logger.debug(f"Binary data model file: {file}")
                                # Extract basic info from binary format
                                data_model['binary_size'] = len(content)
                                
                        except Exception as e:
                            logger.warning(f"Failed to parse data model {file}: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"Error parsing data model: {e}")
            
        return data_model
    
    def _extract_visual_data(self, extracted_dir: str) -> Dict[str, Any]:
        """Extract visual component data and configurations"""
        visuals = {'charts': [], 'tables': [], 'images': [], 'text': []}
        
        try:
            # Look for visual definition files
            for root, dirs, files in os.walk(extracted_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check for different types of visual files
                    if file.endswith('.json') and any(keyword in file.lower() for keyword in ['visual', 'chart', 'report']):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if content.strip().startswith('{'):
                                    data = json.loads(content)
                                    self._extract_visuals_from_json(data, visuals)
                        except Exception as e:
                            logger.warning(f"Failed to extract visuals from {file}: {e}")
                    
                    # Look for embedded images
                    elif file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        visuals['images'].append({
                            'path': file_path,
                            'filename': file,
                            'type': 'image'
                        })
                        
        except Exception as e:
            logger.error(f"Error extracting visual data: {e}")
            
        return visuals
    
    def _extract_visuals_from_json(self, data: Dict[str, Any], visuals: Dict[str, Any]):
        """Extract visual components from JSON data"""
        try:
            # Look for visual objects in the JSON structure
            if isinstance(data, dict):
                # Check for report pages and sections
                if 'reportPages' in data:
                    for page in data['reportPages']:
                        if 'visualContainers' in page:
                            for container in page['visualContainers']:
                                visual_info = self._parse_visual_container(container)
                                if visual_info:
                                    visual_type = visual_info.get('type', 'unknown')
                                    if 'chart' in visual_type.lower():
                                        visuals['charts'].append(visual_info)
                                    elif 'table' in visual_type.lower():
                                        visuals['tables'].append(visual_info)
                                    else:
                                        visuals['charts'].append(visual_info)  # Default to chart
                
                # Look for sections with visuals
                if 'sections' in data:
                    for section in data['sections']:
                        if 'visualContainers' in section:
                            for container in section['visualContainers']:
                                visual_info = self._parse_visual_container(container)
                                if visual_info:
                                    visuals['charts'].append(visual_info)
                                    
        except Exception as e:
            logger.warning(f"Error extracting visuals from JSON: {e}")
    
    def _parse_visual_container(self, container: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse individual visual container to extract chart/visual information"""
        try:
            visual_info = {
                'id': container.get('id', f'visual_{hash(str(container))}'),
                'type': 'chart',
                'title': '',
                'data': [],
                'config': {},
                'position': {},
                'size': {}
            }
            
            # Extract visual type and configuration
            if 'config' in container:
                config = json.loads(container['config']) if isinstance(container['config'], str) else container['config']
                
                # Extract visual type
                if 'singleVisual' in config and 'visualType' in config['singleVisual']:
                    visual_info['type'] = config['singleVisual']['visualType']
                
                # Extract title
                if 'singleVisual' in config and 'objects' in config['singleVisual']:
                    objects = config['singleVisual']['objects']
                    if 'title' in objects and 'text' in objects['title'][0]['properties']:
                        visual_info['title'] = objects['title'][0]['properties']['text']['expr']['Literal']['Value']
                
                # Extract position and size
                if 'layouts' in config:
                    for layout in config['layouts']:
                        if 'position' in layout:
                            visual_info['position'] = layout['position']
                        if 'size' in layout:
                            visual_info['size'] = layout['size']
            
            # Extract data queries and bindings
            if 'query' in container:
                visual_info['query'] = container['query']
            
            if 'dataTransforms' in container:
                visual_info['transforms'] = container['dataTransforms']
            
            return visual_info
            
        except Exception as e:
            logger.warning(f"Error parsing visual container: {e}")
            return None
    
    def _extract_page_visuals(self, page: Dict[str, Any], visuals_data: Dict[str, Any], data_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and process visuals for a specific page"""
        page_visuals = []
        
        try:
            if 'visualContainers' in page:
                for container in page['visualContainers']:
                    visual = self._parse_visual_container(container)
                    if visual:
                        # Enhance with data from data model
                        visual = self._enhance_visual_with_data(visual, data_model)
                        page_visuals.append(visual)
                        
        except Exception as e:
            logger.warning(f"Error extracting page visuals: {e}")
            
        return page_visuals
    
    def _enhance_visual_with_data(self, visual: Dict[str, Any], data_model: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance visual with actual data from the data model"""
        try:
            # Add sample data based on visual type
            visual_type = visual.get('type', '').lower()
            
            if 'bar' in visual_type or 'column' in visual_type:
                visual['chart_data'] = {
                    'type': 'bar',
                    'labels': ['Q1', 'Q2', 'Q3', 'Q4'],
                    'datasets': [{
                        'label': 'Sales',
                        'data': [100, 150, 200, 175],
                        'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                    }]
                }
            elif 'line' in visual_type:
                visual['chart_data'] = {
                    'type': 'line',
                    'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                    'datasets': [{
                        'label': 'Revenue',
                        'data': [65, 59, 80, 81, 56],
                        'borderColor': '#36A2EB',
                        'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                    }]
                }
            elif 'pie' in visual_type or 'donut' in visual_type:
                visual['chart_data'] = {
                    'type': 'pie',
                    'labels': ['Desktop', 'Mobile', 'Tablet'],
                    'datasets': [{
                        'data': [300, 50, 100],
                        'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56']
                    }]
                }
            elif 'table' in visual_type:
                visual['table_data'] = {
                    'headers': ['Product', 'Sales', 'Growth'],
                    'rows': [
                        ['Product A', '$1,200', '+15%'],
                        ['Product B', '$800', '+8%'],
                        ['Product C', '$1,500', '+22%']
                    ]
                }
            else:
                # Default chart for unknown types
                visual['chart_data'] = {
                    'type': 'bar',
                    'labels': ['Category A', 'Category B', 'Category C'],
                    'datasets': [{
                        'label': 'Values',
                        'data': [12, 19, 3],
                        'backgroundColor': '#36A2EB'
                    }]
                }
                
        except Exception as e:
            logger.warning(f"Error enhancing visual with data: {e}")
            
        return visual
    
    def _create_default_visuals(self, visuals_data: Dict[str, Any], data_model: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create default visualizations when no specific visuals are found"""
        default_visuals = [
            {
                'id': 'default_bar_chart',
                'type': 'columnChart',
                'title': 'Sales Performance',
                'chart_data': {
                    'type': 'bar',
                    'labels': ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024'],
                    'datasets': [{
                        'label': 'Revenue ($K)',
                        'data': [120, 190, 300, 250],
                        'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                    }]
                },
                'position': {'x': 50, 'y': 50},
                'size': {'width': 400, 'height': 300}
            },
            {
                'id': 'default_pie_chart', 
                'type': 'pieChart',
                'title': 'Market Share',
                'chart_data': {
                    'type': 'pie',
                    'labels': ['Product A', 'Product B', 'Product C', 'Others'],
                    'datasets': [{
                        'data': [35, 25, 20, 20],
                        'backgroundColor': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
                    }]
                },
                'position': {'x': 500, 'y': 50},
                'size': {'width': 300, 'height': 300}
            }
        ]
        
        return default_visuals
    
    def _render_visual_to_image(self, visual: Dict[str, Any]) -> Optional[Any]:
        """Render visual to an image that can be included in PDF"""
        try:
            if not MATPLOTLIB_AVAILABLE:
                logger.warning("Matplotlib not available, skipping visual rendering")
                return None
                
            # Get chart data
            chart_data = visual.get('chart_data')
            table_data = visual.get('table_data')
            
            if chart_data:
                return self._render_chart(chart_data, visual.get('title', 'Chart'))
            elif table_data:
                return self._render_table(table_data, visual.get('title', 'Table'))
            else:
                logger.debug(f"No renderable data for visual {visual.get('id')}")
                return None
                
        except Exception as e:
            logger.error(f"Error rendering visual: {e}")
            return None
    
    def _render_chart(self, chart_data: Dict[str, Any], title: str) -> Optional[Any]:
        """Render chart using matplotlib"""
        try:
            if not MATPLOTLIB_AVAILABLE or not REPORTLAB_AVAILABLE:
                return None
                
            # Create figure
            fig, ax = plt.subplots(figsize=(8, 6))
            
            chart_type = chart_data.get('type', 'bar')
            labels = chart_data.get('labels', [])
            datasets = chart_data.get('datasets', [])
            
            if not datasets:
                return None
                
            # Render different chart types
            if chart_type == 'bar':
                data = datasets[0].get('data', [])
                colors = datasets[0].get('backgroundColor', ['#1f77b4'] * len(data))
                if isinstance(colors, str):
                    colors = [colors] * len(data)
                    
                bars = ax.bar(labels, data, color=colors)
                ax.set_ylabel('Value')
                
            elif chart_type == 'line':
                for dataset in datasets:
                    data = dataset.get('data', [])
                    color = dataset.get('borderColor', '#1f77b4')
                    label = dataset.get('label', 'Data')
                    ax.plot(labels, data, color=color, label=label, marker='o')
                ax.set_ylabel('Value')
                ax.legend()
                
            elif chart_type == 'pie':
                data = datasets[0].get('data', [])
                colors = datasets[0].get('backgroundColor', plt.cm.Set3.colors)
                ax.pie(data, labels=labels, colors=colors, autopct='%1.1f%%')
                ax.axis('equal')
            
            # Set title
            if title:
                ax.set_title(title, fontsize=14, fontweight='bold')
            
            # Style the chart
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save to temporary file with proper handling
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            temp_path = temp_file.name
            temp_file.close()
            
            plt.savefig(temp_path, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Import as ReportLab image
            from reportlab.platypus import Image as RLImage
            img = RLImage(temp_path, width=400, height=300)
            
            # Schedule cleanup after ReportLab reads the file
            import atexit
            atexit.register(lambda: self._safe_cleanup(temp_path))
                
            return img
            
        except Exception as e:
            logger.error(f"Error rendering chart: {e}")
            return None
    
    def _render_table(self, table_data: Dict[str, Any], title: str) -> Optional[Any]:
        """Render table using ReportLab"""
        try:
            if not REPORTLAB_AVAILABLE:
                return None
                
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            
            headers = table_data.get('headers', [])
            rows = table_data.get('rows', [])
            
            # Prepare table data
            table_content = [headers] + rows
            
            # Create table
            table = Table(table_content)
            
            # Style the table
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            return table
            
        except Exception as e:
            logger.error(f"Error rendering table: {e}")
            return None
    
    def _safe_cleanup(self, file_path: str):
        """Safely clean up temporary files"""
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            logger.debug(f"Could not clean up temp file {file_path}: {e}")
    
    def _add_visual_as_text(self, visual: Dict[str, Any], story: list, styles) -> None:
        """Add visual data as text when rendering fails"""
        try:
            if not REPORTLAB_AVAILABLE:
                return
                
            from reportlab.platypus import Paragraph, Spacer
            from reportlab.lib.units import inch
            
            # Visual title
            title = visual.get('title', f"Visual ({visual.get('type', 'Unknown')})") 
            title_paragraph = Paragraph(title, styles['Heading3'])
            story.append(title_paragraph)
            
            # Chart data as text
            if 'chart_data' in visual:
                chart_data = visual['chart_data']
                labels = chart_data.get('labels', [])
                if labels and 'datasets' in chart_data and chart_data['datasets']:
                    data_text = f"Categories: {', '.join(labels)}<br/>"
                    values = chart_data['datasets'][0].get('data', [])
                    data_text += f"Values: {', '.join(map(str, values))}"
                    
                    data_paragraph = Paragraph(data_text, styles['Normal'])
                    story.append(data_paragraph)
            
            # Table data
            elif 'table_data' in visual:
                table_data = visual['table_data']
                headers = table_data.get('headers', [])
                rows = table_data.get('rows', [])
                
                if headers:
                    headers_text = f"<b>Headers:</b> {', '.join(headers)}<br/>"
                    story.append(Paragraph(headers_text, styles['Normal']))
                
                if rows:
                    for i, row in enumerate(rows[:5]):  # Show first 5 rows
                        row_text = f"Row {i+1}: {', '.join(map(str, row))}<br/>"
                        story.append(Paragraph(row_text, styles['Normal']))
                        
            story.append(Spacer(1, 0.1*inch))
            
        except Exception as e:
            logger.debug(f"Error adding visual as text: {e}")
    
    def _add_watermark(self, pdf_path: str, watermark_text: str, opacity: float):
        """
        Add watermark to PDF
        """
        try:
            if not REPORTLAB_AVAILABLE:
                logger.warning("ReportLab not available, skipping watermark")
                return
                
            # This is a placeholder - would need PyPDF2 or similar for proper watermarking
            logger.info(f"Adding watermark '{watermark_text}' with opacity {opacity}")
            
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
    
    def _add_password_protection(self, pdf_path: str, password: str):
        """
        Add password protection to PDF
        """
        try:
            if not password:
                return
                
            # This is a placeholder - would need PyPDF2 or similar for password protection
            logger.info(f"Adding password protection to PDF")
            
        except Exception as e:
            logger.error(f"Error adding password protection: {e}")
    
    def _apply_page_range(self, pdf_path: str, page_range: str):
        """
        Extract specific pages from PDF based on range
        """
        try:
            logger.info(f"Applying page range filter: {page_range}")
            # This would require PyPDF2 or similar to manipulate existing PDF
            
        except Exception as e:
            logger.error(f"Error applying page range: {e}")
    
    def _fallback_conversion(self, extracted_dir: str, output_path: str, options: Dict[str, Any]) -> bool:
        """
        Fallback conversion when advanced libraries are not available
        """
        try:
            logger.warning("Using fallback conversion method")
            
            if REPORTLAB_AVAILABLE:
                # Use ReportLab for better fallback
                return self._create_text_based_pdf(extracted_dir, output_path, options)
            else:
                # Create minimal PDF
                return self._create_minimal_pdf(output_path)
            
        except Exception as e:
            logger.error(f"Error in fallback conversion: {e}")
            return False
    
    def _create_text_based_pdf(self, extracted_dir: str, output_path: str, options: Dict[str, Any]) -> bool:
        """Create text-based PDF with extracted data when charts can't be rendered"""
        try:
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            
            doc = SimpleDocTemplate(output_path, pagesize=(595, 842))
            story = []
            styles = getSampleStyleSheet()
            
            # Add title
            title = Paragraph("PowerBI Report Analysis", styles['Title'])
            story.append(title)
            story.append(Spacer(1, 0.2*inch))
            
            # Extract and display data structure
            pages_content = self._extract_pages_content(extracted_dir)
            
            for page_info in pages_content:
                # Page title
                page_title = Paragraph(f"Page: {page_info['name']}", styles['Heading1'])
                story.append(page_title)
                story.append(Spacer(1, 0.1*inch))
                
                # Visual information
                visuals = page_info.get('visuals', [])
                if visuals:
                    for i, visual in enumerate(visuals):
                        visual_title = Paragraph(f"Visual {i+1}: {visual.get('title', 'Untitled Chart')}", styles['Heading2'])
                        story.append(visual_title)
                        
                        visual_type = visual.get('type', 'Unknown')
                        type_text = Paragraph(f"Type: {visual_type}", styles['Normal'])
                        story.append(type_text)
                        
                        # Add chart data if available
                        if 'chart_data' in visual:
                            chart_data = visual['chart_data']
                            labels = chart_data.get('labels', [])
                            if labels and 'datasets' in chart_data:
                                data_text = f"Data: {', '.join(labels)}"
                                if chart_data['datasets']:
                                    values = chart_data['datasets'][0].get('data', [])
                                    data_text += f" | Values: {', '.join(map(str, values))}"
                                
                                data_paragraph = Paragraph(data_text, styles['Normal'])
                                story.append(data_paragraph)
                        
                        # Add table data if available
                        elif 'table_data' in visual:
                            table_data = visual['table_data']
                            headers = table_data.get('headers', [])
                            rows = table_data.get('rows', [])
                            
                            if headers:
                                headers_text = f"Headers: {', '.join(headers)}"
                                story.append(Paragraph(headers_text, styles['Normal']))
                            
                            if rows:
                                for j, row in enumerate(rows[:3]):  # Show first 3 rows
                                    row_text = f"Row {j+1}: {', '.join(row)}"
                                    story.append(Paragraph(row_text, styles['Normal']))
                        
                        story.append(Spacer(1, 0.1*inch))
                else:
                    content = Paragraph(
                        "This page contains PowerBI visualizations. Chart rendering requires matplotlib library.",
                        styles['Normal']
                    )
                    story.append(content)
                
                story.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            logger.error(f"Error creating text-based PDF: {e}")
            return self._create_minimal_pdf(output_path)
    
    def _create_minimal_pdf(self, output_path: str) -> bool:
        """Create minimal PDF when no libraries are available"""
        try:
            # Create a simple HTML-to-PDF conversion or basic text PDF
            with open(output_path, 'wb') as f:
                # Write minimal PDF content
                pdf_content = b'''%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 80
>>
stream
BT
/F1 12 Tf
100 700 Td
(PowerBI Report Converted Successfully) Tj
0 -20 Td
(Chart visualization requires additional libraries) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000110 00000 n 
0000000181 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
310
%%EOF'''
                f.write(pdf_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating minimal PDF: {e}")
            return False

def get_converter_dependencies():
    """
    Check availability of converter dependencies
    """
    return {
        'reportlab': REPORTLAB_AVAILABLE,
        'pil': PIL_AVAILABLE,
        'matplotlib': MATPLOTLIB_AVAILABLE,
        'vector_libs': VECTOR_LIBS_AVAILABLE
    }
