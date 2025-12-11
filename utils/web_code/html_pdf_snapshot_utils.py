"""
HTML PDF Snapshot Converter Utilities
Handles HTML to PDF conversion with multiple backend support
"""

import os
import uuid
import tempfile
import requests
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re
import mimetypes
from pathlib import Path

class HTMLPDFProcessor:
    """Utility class for HTML to PDF processing"""
    
    def __init__(self):
        self.upload_folder = 'uploads'
        self.current_backend = None
        self.backend_info = None
        
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Initialize backend
        self._detect_backend()
    
    def _detect_backend(self):
        """Detect available PDF generation backend"""
        backends = []
        
        # Try WeasyPrint first (best CSS support)
        try:
            import weasyprint
            # Test if it actually works
            test_html = '<html><body><p>Test</p></body></html>'
            weasyprint.HTML(string=test_html).write_pdf()
            backends.append('weasyprint')
            if not self.current_backend:
                self.current_backend = 'weasyprint'
        except (ImportError, OSError):
            pass
        
        # Try pdfkit (wkhtmltopdf)
        try:
            import pdfkit
            # Test if wkhtmltopdf is available
            pdfkit.from_string('<html><body><p>Test</p></body></html>', False)
            backends.append('pdfkit')
            if not self.current_backend:
                self.current_backend = 'pdfkit'
        except (ImportError, OSError):
            pass
        
        # Try ReportLab (pure Python, most compatible)
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            backends.append('reportlab')
            if not self.current_backend:
                self.current_backend = 'reportlab'
        except ImportError:
            pass
        
        # Try Selenium (most reliable but slower)
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            backends.append('selenium')
            if not self.current_backend:
                self.current_backend = 'selenium'
        except ImportError:
            pass
        
        self.backend_info = {
            'available_backends': backends,
            'current_backend': self.current_backend,
            'supported_features': self._get_supported_features()
        }
    
    def _get_supported_features(self):
        """Get supported features for current backend"""
        if not self.current_backend:
            return {}
        
        features = {
            'weasyprint': {
                'custom_css': True,
                'custom_headers_footers': True,
                'javascript_support': False,
                'background_graphics': True,
                'viewport_control': True,
                'font_embedding': True
            },
            'pdfkit': {
                'custom_css': True,
                'custom_headers_footers': True,
                'javascript_support': True,
                'background_graphics': True,
                'viewport_control': True,
                'font_embedding': False
            },
            'reportlab': {
                'custom_css': False,
                'custom_headers_footers': True,
                'javascript_support': False,
                'background_graphics': False,
                'viewport_control': False,
                'font_embedding': True
            },
            'selenium': {
                'custom_css': True,
                'custom_headers_footers': False,
                'javascript_support': True,
                'background_graphics': True,
                'viewport_control': True,
                'font_embedding': False
            }
        }
        
        return features.get(self.current_backend, {})
    
    def is_backend_available(self):
        """Check if any PDF backend is available"""
        return self.current_backend is not None
    
    def get_current_backend(self):
        """Get current backend name"""
        return self.current_backend
    
    def get_backend_info(self):
        """Get backend information"""
        return self.backend_info
    
    def url_to_pdf(self, url, settings):
        """Convert URL to PDF"""
        if not self.is_backend_available():
            raise Exception("No PDF backend available. Please install a supported PDF library.")
        
        # Validate URL
        if not self._validate_url(url):
            raise Exception("Invalid or unsafe URL provided")
        
        try:
            if self.current_backend == 'weasyprint':
                return self._weasyprint_url_to_pdf(url, settings)
            elif self.current_backend == 'pdfkit':
                return self._pdfkit_url_to_pdf(url, settings)
            elif self.current_backend == 'selenium':
                return self._selenium_url_to_pdf(url, settings)
            elif self.current_backend == 'reportlab':
                # ReportLab can't directly convert URLs, fetch content first
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                html_content = response.text
                return self._reportlab_html_to_pdf(html_content, settings)
            else:
                raise Exception(f"Unsupported backend: {self.current_backend}")
                
        except Exception as e:
            raise Exception(f"URL to PDF conversion failed: {str(e)}")
    
    def content_to_pdf(self, html_content, settings):
        """Convert HTML content to PDF"""
        if not self.is_backend_available():
            raise Exception("No PDF backend available. Please install a supported PDF library.")
        
        try:
            if self.current_backend == 'weasyprint':
                return self._weasyprint_html_to_pdf(html_content, settings)
            elif self.current_backend == 'pdfkit':
                return self._pdfkit_html_to_pdf(html_content, settings)
            elif self.current_backend == 'selenium':
                return self._selenium_html_to_pdf(html_content, settings)
            elif self.current_backend == 'reportlab':
                return self._reportlab_html_to_pdf(html_content, settings)
            else:
                raise Exception(f"Unsupported backend: {self.current_backend}")
                
        except Exception as e:
            raise Exception(f"HTML content to PDF conversion failed: {str(e)}")
    
    def file_to_pdf(self, file_path, settings):
        """Convert HTML file to PDF"""
        if not os.path.exists(file_path):
            raise Exception("File not found")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    html_content = f.read()
            except Exception as e:
                raise Exception(f"Failed to read file: {str(e)}")
        
        return self.content_to_pdf(html_content, settings)
    
    def _weasyprint_url_to_pdf(self, url, settings):
        """Convert URL to PDF using WeasyPrint"""
        import weasyprint
        from weasyprint import HTML, CSS
        
        # Generate output filename
        output_filename = f"{uuid.uuid4().hex}_converted.pdf"
        output_path = os.path.join(self.upload_folder, output_filename)
        
        # Create CSS from settings
        css_content = self._build_css_from_settings(settings)
        
        html_doc = HTML(url=url)
        if css_content:
            css_doc = CSS(string=css_content)
            html_doc.write_pdf(output_path, stylesheets=[css_doc])
        else:
            html_doc.write_pdf(output_path)
        
        return output_path
    
    def _weasyprint_html_to_pdf(self, html_content, settings):
        """Convert HTML content to PDF using WeasyPrint"""
        import weasyprint
        from weasyprint import HTML, CSS
        
        # Generate output filename
        output_filename = f"{uuid.uuid4().hex}_converted.pdf"
        output_path = os.path.join(self.upload_folder, output_filename)
        
        # Create CSS from settings
        css_content = self._build_css_from_settings(settings)
        
        # Add custom CSS to HTML if provided
        if settings.get('custom_css'):
            html_content = self._inject_css(html_content, settings.get('custom_css', ''))
        
        html_doc = HTML(string=html_content)
        if css_content:
            css_doc = CSS(string=css_content)
            html_doc.write_pdf(output_path, stylesheets=[css_doc])
        else:
            html_doc.write_pdf(output_path)
        
        return output_path
    
    def _pdfkit_url_to_pdf(self, url, settings):
        """Convert URL to PDF using PDFKit"""
        import pdfkit
        
        # Generate output filename
        output_filename = f"{uuid.uuid4().hex}_converted.pdf"
        output_path = os.path.join(self.upload_folder, output_filename)
        
        # Build options
        options = self._build_pdfkit_options(settings)
        
        pdfkit.from_url(url, output_path, options=options)
        
        return output_path
    
    def _pdfkit_html_to_pdf(self, html_content, settings):
        """Convert HTML content to PDF using PDFKit"""
        import pdfkit
        
        # Generate output filename
        output_filename = f"{uuid.uuid4().hex}_converted.pdf"
        output_path = os.path.join(self.upload_folder, output_filename)
        
        # Add custom CSS to HTML if provided
        if settings.get('custom_css'):
            html_content = self._inject_css(html_content, settings.get('custom_css', ''))
        
        # Build options
        options = self._build_pdfkit_options(settings)
        
        pdfkit.from_string(html_content, output_path, options=options)
        
        return output_path
    
    def _selenium_url_to_pdf(self, url, settings):
        """Convert URL to PDF using Selenium"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        import base64
        import time
        
        # Generate output filename
        output_filename = f"{uuid.uuid4().hex}_converted.pdf"
        output_path = os.path.join(self.upload_folder, output_filename)
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--window-size={settings.get("viewport_width", 1366)},{settings.get("viewport_height", 768)}')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)
            
            # Wait for page load if specified
            if settings.get('wait_for_load', False):
                time.sleep(settings.get('wait_time', 3))
            
            # Inject custom CSS if provided
            if settings.get('custom_css'):
                driver.execute_script(f"""
                    var style = document.createElement('style');
                    style.textContent = `{settings.get('custom_css', '')}`;
                    document.head.appendChild(style);
                """)
            
            # Generate PDF
            pdf_options = {
                'paperFormat': settings.get('page_size', 'A4'),
                'landscape': settings.get('orientation', 'portrait') == 'landscape',
                'printBackground': settings.get('background_graphics', True),
                'scale': settings.get('scale_factor', 1.0)
            }
            
            pdf_base64 = driver.execute_cdp_cmd('Page.printToPDF', pdf_options)
            pdf_bytes = base64.b64decode(pdf_base64['data'])
            
            # Save PDF
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
            
            return output_path
            
        finally:
            if driver:
                driver.quit()
    
    def _selenium_html_to_pdf(self, html_content, settings):
        """Convert HTML content to PDF using Selenium"""
        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            if settings.get('custom_css'):
                html_content = self._inject_css(html_content, settings.get('custom_css', ''))
            temp_file.write(html_content)
            temp_file_path = temp_file.name
        
        try:
            file_url = f"file:///{temp_file_path.replace(os.sep, '/')}"
            return self._selenium_url_to_pdf(file_url, settings)
        finally:
            os.unlink(temp_file_path)
    
    def _reportlab_html_to_pdf(self, html_content, settings):
        """Convert HTML to PDF using ReportLab (basic HTML support)"""
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter, A4, A3, A5
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from io import BytesIO
        
        # Generate output filename
        output_filename = f"{uuid.uuid4().hex}_converted.pdf"
        output_path = os.path.join(self.upload_folder, output_filename)
        
        # Convert HTML to text (ReportLab has limited HTML support)
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract text content
        text_content = soup.get_text()
        title_tag = soup.find('title')
        title = title_tag.get_text() if title_tag else 'Converted Document'
        
        # Configure page size
        page_sizes = {
            'A4': A4,
            'A3': A3,
            'A5': A5,
            'Letter': letter
        }
        page_size = page_sizes.get(settings.get('page_size', 'A4'), A4)
        
        # Create document with metadata for better compatibility
        doc = SimpleDocTemplate(
            output_path,
            pagesize=page_size,
            topMargin=float(settings.get('margin_top', 2)) * cm,
            bottomMargin=float(settings.get('margin_bottom', 2)) * cm,
            leftMargin=float(settings.get('margin_left', 2)) * cm,
            rightMargin=float(settings.get('margin_right', 2)) * cm,
            title=title,
            author='HTML PDF Converter',
            creator='Cropio Converter Platform',
            subject='HTML to PDF Conversion'
        )
        
        # Create styles
        styles = getSampleStyleSheet()
        story = []
        
        # Add title with better styling
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=24,
            alignment=0  # Left align
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Process HTML elements for better formatting with proper error handling
        try:
            # Extract and process structured content
            elements = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'div'])
            
            if elements:
                for element in elements:
                    try:
                        element_text = element.get_text().strip()
                        if not element_text:
                            continue
                            
                        # Clean text to avoid ReportLab issues
                        element_text = element_text.replace('\u2022', '*').replace('\u2013', '-').replace('\u2014', '--')
                        
                        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            # Handle headings
                            level = int(element.name[1])
                            heading_style = ParagraphStyle(
                                f'Heading{level}',
                                parent=styles['Heading1'],
                                fontSize=max(12, 18 - (level-1)*2),
                                textColor=colors.HexColor('#2c3e50'),
                                spaceBefore=12,
                                spaceAfter=8,
                                keepWithNext=1
                            )
                            story.append(Paragraph(element_text, heading_style))
                            
                        elif element.name == 'p':
                            # Handle paragraphs
                            story.append(Paragraph(element_text, styles['Normal']))
                            story.append(Spacer(1, 6))
                            
                        elif element.name in ['ul', 'ol']:
                            # Handle lists
                            list_items = element.find_all('li')
                            for li in list_items:
                                li_text = li.get_text().strip()
                                if li_text:
                                    # Clean list item text
                                    li_text = li_text.replace('\u2022', '*')
                                    bullet_style = ParagraphStyle(
                                        'BulletText',
                                        parent=styles['Normal'],
                                        leftIndent=20,
                                        bulletIndent=10,
                                        spaceBefore=3,
                                        spaceAfter=3
                                    )
                                    story.append(Paragraph(f'• {li_text}', bullet_style))
                            story.append(Spacer(1, 6))
                            
                        elif element.name == 'div' and element_text:
                            # Handle div content as paragraphs
                            story.append(Paragraph(element_text, styles['Normal']))
                            story.append(Spacer(1, 6))
                            
                    except Exception as elem_error:
                        # Skip problematic elements but continue processing
                        print(f"Warning: Skipping element due to error: {elem_error}")
                        continue
            else:
                # Fallback to plain text processing
                text_lines = text_content.split('\n')
                for line in text_lines:
                    line = line.strip()
                    if line:
                        try:
                            # Clean text
                            line = line.replace('\u2022', '*').replace('\u2013', '-')
                            story.append(Paragraph(line, styles['Normal']))
                            story.append(Spacer(1, 3))
                        except:
                            continue
                            
        except Exception as processing_error:
            # Ultimate fallback - just use plain text
            print(f"Warning: HTML processing failed, using plain text: {processing_error}")
            text_lines = text_content.split('\n')
            for line in text_lines:
                line = line.strip()
                if line:
                    try:
                        story.append(Paragraph(line, styles['Normal']))
                        story.append(Spacer(1, 3))
                    except:
                        continue
        
        # Build PDF with error handling
        try:
            doc.build(story)
        except Exception as e:
            # Fallback to simple text if structured conversion fails
            story = []
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))
            
            # Simple text paragraphs
            simple_paragraphs = text_content.split('\n')
            for para in simple_paragraphs:
                if para.strip():
                    try:
                        story.append(Paragraph(para.strip(), styles['Normal']))
                    except:
                        # Skip problematic paragraphs
                        continue
                    story.append(Spacer(1, 6))
            
            doc.build(story)
        
        return output_path
    
    def _build_css_from_settings(self, settings):
        """Build CSS string from PDF settings"""
        css_parts = []
        
        # Page settings
        page_size = settings.get('page_size', 'A4')
        orientation = settings.get('orientation', 'portrait')
        
        css_parts.append(f"""
            @page {{
                size: {page_size} {orientation};
                margin-top: {settings.get('margin_top', 2)}cm;
                margin-bottom: {settings.get('margin_bottom', 2)}cm;
                margin-left: {settings.get('margin_left', 2)}cm;
                margin-right: {settings.get('margin_right', 2)}cm;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                color: #2c3e50;
                page-break-after: avoid;
            }}
            
            img {{
                max-width: 100%;
                height: auto;
                page-break-inside: avoid;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                page-break-inside: avoid;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            .no-break {{
                page-break-inside: avoid;
            }}
        """)
        
        return '\n'.join(css_parts)
    
    def _build_pdfkit_options(self, settings):
        """Build PDFKit options from settings"""
        options = {
            'page-size': settings.get('page_size', 'A4'),
            'orientation': settings.get('orientation', 'Portrait').title(),
            'margin-top': f"{settings.get('margin_top', 2)}cm",
            'margin-bottom': f"{settings.get('margin_bottom', 2)}cm",
            'margin-left': f"{settings.get('margin_left', 2)}cm",
            'margin-right': f"{settings.get('margin_right', 2)}cm",
            'encoding': 'UTF-8',
            'no-outline': None,
            'enable-local-file-access': None,
            'print-media-type': None
        }
        
        # Viewport settings
        if settings.get('viewport_width'):
            options['viewport-size'] = f"{settings['viewport_width']}x{settings.get('viewport_height', 768)}"
        
        # Background graphics
        if settings.get('background_graphics', True):
            options['background'] = None
        
        # Wait settings
        if settings.get('wait_for_load', False):
            options['javascript-delay'] = settings.get('wait_time', 3) * 1000
        
        return options
    
    def _inject_css(self, html_content, custom_css):
        """Inject custom CSS into HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Ensure HTML structure exists
        if not soup.html:
            new_soup = BeautifulSoup('<html></html>', 'html.parser')
            new_soup.html.append(soup)
            soup = new_soup
        
        if not soup.head:
            soup.html.insert(0, soup.new_tag('head'))
        
        # Add custom CSS
        style_tag = soup.new_tag('style', type='text/css')
        style_tag.string = custom_css
        soup.head.append(style_tag)
        
        return str(soup)
    
    def _validate_url(self, url):
        """Validate URL for security and accessibility"""
        try:
            parsed = urlparse(url)
            
            # Must be HTTP or HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Must have a hostname
            if not parsed.netloc:
                return False
            
            # Block localhost and private IPs for security
            hostname = parsed.netloc.split(':')[0]
            if hostname in ['localhost', '127.0.0.1', '0.0.0.0']:
                return False
            
            # Check for private IP ranges
            import ipaddress
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private:
                    return False
            except ValueError:
                # Not an IP address, which is fine
                pass
            
            return True
            
        except Exception:
            return False
    
    def get_url_preview(self, url):
        """Get preview information for a URL"""
        if not self._validate_url(url):
            raise Exception("Invalid or unsafe URL")
        
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            response.raise_for_status()
            
            # Parse HTML to extract metadata
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.find('title')
            title_text = title.get_text().strip() if title else 'Untitled'
            
            # Get meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            description = meta_desc.get('content', '').strip() if meta_desc else ''
            
            # Get favicon
            favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
            favicon_url = ''
            if favicon and favicon.get('href'):
                favicon_url = urljoin(url, favicon['href'])
            
            return {
                'url': url,
                'title': title_text,
                'description': description,
                'favicon': favicon_url,
                'content_length': len(response.text),
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'server': response.headers.get('server', '')
            }
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
    
    def get_html_file_info(self, file_path):
        """Get information about an HTML file"""
        if not os.path.exists(file_path):
            raise Exception("File not found")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    html_content = f.read()
            except Exception as e:
                raise Exception(f"Failed to read file: {str(e)}")
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        title = soup.find('title')
        title_text = title.get_text().strip() if title else os.path.basename(file_path)
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content', '').strip() if meta_desc else ''
        
        file_size = os.path.getsize(file_path)
        
        return {
            'filename': os.path.basename(file_path),
            'title': title_text,
            'description': description or 'HTML file for PDF conversion',
            'size': file_size,
            'content_length': len(html_content),
            'has_css': bool(soup.find_all(['style', 'link']) or 'style=' in html_content),
            'has_javascript': bool(soup.find_all('script') or 'javascript:' in html_content),
            'image_count': len(soup.find_all('img')),
            'link_count': len(soup.find_all('a'))
        }
    
    def validate_html_content(self, content):
        """Validate HTML content"""
        if not content.strip():
            return {
                'valid': True,
                'warnings': ['Content is empty'],
                'errors': [],
                'stats': {
                    'characters': 0,
                    'words': 0,
                    'lines': 0,
                    'estimated_pages': 0
                }
            }
        
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'stats': {
                'characters': len(content),
                'words': len(content.split()),
                'lines': content.count('\n') + 1,
                'estimated_pages': max(1, len(content) // 3000)  # Rough estimate
            }
        }
        
        # Basic HTML validation
        if not content.strip().startswith('<'):
            validation_result['warnings'].append('Content does not start with HTML tag')
        
        # Check for common HTML structure
        content_lower = content.lower()
        if '<html>' not in content_lower and '<body>' not in content_lower:
            validation_result['warnings'].append('Missing basic HTML structure (html/body tags)')
        
        # Check for unclosed tags (basic check)
        open_tags = re.findall(r'<([^/>\\s]+)', content)
        close_tags = re.findall(r'</([^>\\s]+)', content)
        
        # Simple tag balance check
        for tag in ['html', 'body', 'head', 'div', 'p', 'table', 'tr', 'td']:
            open_count = open_tags.count(tag)
            close_count = close_tags.count(tag)
            if open_count != close_count and open_count > 0:
                validation_result['warnings'].append(f'Potentially unbalanced {tag} tags')
        
        # Check content size
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            validation_result['errors'].append(f'Content exceeds {max_size // (1024 * 1024)}MB limit')
            validation_result['valid'] = False
        
        return validation_result
    
    def get_domain_from_url(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except Exception:
            return 'webpage'
    
    def batch_convert_html(self, file_paths, settings):
        """Convert multiple HTML files to PDF"""
        converted_files = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                pdf_path = self.file_to_pdf(file_path, settings)
                converted_files.append({
                    'input': file_path,
                    'output': pdf_path,
                    'status': 'success'
                })
            except Exception as e:
                failed_files.append({
                    'input': file_path,
                    'error': str(e),
                    'status': 'failed'
                })
        
        return {
            'converted': converted_files,
            'failed': failed_files,
            'total_processed': len(file_paths),
            'success_count': len(converted_files),
            'failure_count': len(failed_files)
        }
    
    @staticmethod
    def is_html_pdf_supported():
        """Check if HTML PDF conversion support is available"""
        processor = HTMLPDFProcessor()
        return processor.is_backend_available()
    
    @staticmethod
    def get_supported_backends():
        """Get list of supported PDF backends"""
        processor = HTMLPDFProcessor()
        return processor.backend_info.get('available_backends', [])
    
    def cleanup_old_files(self, max_age_hours=24):
        """Clean up old converted files"""
        try:
            if not os.path.exists(self.upload_folder):
                return
            
            current_time = time.time()
            cutoff_time = current_time - (max_age_hours * 3600)
            
            for filename in os.listdir(self.upload_folder):
                file_path = os.path.join(self.upload_folder, filename)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.unlink(file_path)
                except OSError:
                    pass  # File might be in use or permission denied
                    
        except Exception as e:
            print(f"Warning: Failed to cleanup old files: {e}")
    
    def get_pdf_info(self, pdf_path):
        """Get information about generated PDF"""
        if not os.path.exists(pdf_path):
            return None
        
        try:
            file_size = os.path.getsize(pdf_path)
            
            # Try to get PDF metadata if PyPDF2 is available
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    page_count = len(reader.pages)
                    metadata = reader.metadata if reader.metadata else {}
                    
                    return {
                        'file_size': file_size,
                        'page_count': page_count,
                        'title': metadata.get('/Title', ''),
                        'author': metadata.get('/Author', ''),
                        'creator': metadata.get('/Creator', ''),
                        'creation_date': metadata.get('/CreationDate', '')
                    }
            except ImportError:
                # PyPDF2 not available, return basic info
                pass
            
            return {
                'file_size': file_size,
                'page_count': 'Unknown',
                'title': '',
                'author': '',
                'creator': 'HTML PDF Converter',
                'creation_date': ''
            }
            
        except Exception as e:
            print(f"Warning: Failed to get PDF info: {e}")
            return None
