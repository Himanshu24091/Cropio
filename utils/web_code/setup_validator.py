"""
HTML PDF Setup Validator
Utility to validate system setup and check for required dependencies
"""

import os
import sys
import time
import subprocess
import importlib
import platform
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SetupValidator:
    """Validates system setup for HTML PDF conversion"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.validation_results = {}
    
    def validate_full_setup(self) -> Dict:
        """Perform full setup validation"""
        results = {
            'system_info': self.system_info,
            'python_version': self._check_python_version(),
            'dependencies': self._check_dependencies(),
            'backends': self._check_pdf_backends(),
            'binaries': self._check_external_binaries(),
            'permissions': self._check_permissions(),
            'recommendations': []
        }
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        # Overall status
        results['overall_status'] = self._get_overall_status(results)
        
        return results
    
    def _get_system_info(self) -> Dict:
        """Get basic system information"""
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': sys.version,
            'python_executable': sys.executable
        }
    
    def _check_python_version(self) -> Dict:
        """Check Python version compatibility"""
        version_info = sys.version_info
        
        # Minimum Python 3.8 required
        min_version = (3, 8)
        is_compatible = version_info[:2] >= min_version
        
        return {
            'version': f"{version_info.major}.{version_info.minor}.{version_info.micro}",
            'is_compatible': is_compatible,
            'minimum_required': f"{min_version[0]}.{min_version[1]}",
            'status': 'OK' if is_compatible else 'INCOMPATIBLE'
        }
    
    def _check_dependencies(self) -> Dict:
        """Check Python package dependencies"""
        dependencies = {
            'required': [
                ('requests', 'HTTP client for URL fetching'),
                ('beautifulsoup4', 'HTML parsing and manipulation'),
                ('Pillow', 'Image processing'),
                ('werkzeug', 'Security utilities')
            ],
            'pdf_backends': [
                ('weasyprint', 'CSS-based PDF generation'),
                ('pdfkit', 'wkhtmltopdf wrapper'),
                ('selenium', 'Browser automation')
            ],
            'optional': [
                ('PyMuPDF', 'PDF analysis and thumbnails'),
                ('lxml', 'Enhanced HTML parsing'),
                ('fonttools', 'Enhanced font support'),
                ('html5lib', 'Better HTML parsing')
            ]
        }
        
        results = {}
        
        for category, packages in dependencies.items():
            results[category] = []
            for package_name, description in packages:
                status = self._check_package(package_name)
                results[category].append({
                    'name': package_name,
                    'description': description,
                    'installed': status['installed'],
                    'version': status['version'],
                    'import_error': status.get('error')
                })
        
        return results
    
    def _check_package(self, package_name: str) -> Dict:
        """Check if a Python package is installed and importable"""
        try:
            module = importlib.import_module(package_name)
            version = getattr(module, '__version__', 'Unknown')
            return {
                'installed': True,
                'version': version
            }
        except ImportError as e:
            return {
                'installed': False,
                'version': None,
                'error': str(e)
            }
    
    def _check_pdf_backends(self) -> Dict:
        """Check PDF backend availability and functionality"""
        from .html_pdf_utils import WeasyPrintBackend, PDFKitBackend, SeleniumBackend
        
        backends = {
            'weasyprint': WeasyPrintBackend(),
            'pdfkit': PDFKitBackend(),
            'selenium': SeleniumBackend()
        }
        
        results = {}
        available_count = 0
        
        for name, backend in backends.items():
            is_available = backend.check_availability()
            if is_available:
                available_count += 1
            
            results[name] = {
                'available': is_available,
                'features': backend.get_supported_features(),
                'description': self._get_backend_description(name)
            }
        
        results['summary'] = {
            'total_backends': len(backends),
            'available_backends': available_count,
            'recommended_minimum': 1,
            'status': 'OK' if available_count > 0 else 'ERROR'
        }
        
        return results
    
    def _get_backend_description(self, backend_name: str) -> str:
        """Get description for PDF backend"""
        descriptions = {
            'weasyprint': 'Best CSS support and styling, pure Python implementation',
            'pdfkit': 'Fast processing with wkhtmltopdf, good compatibility',
            'selenium': 'Modern browser engine with full JavaScript support'
        }
        return descriptions.get(backend_name, 'PDF generation backend')
    
    def _check_external_binaries(self) -> Dict:
        """Check for external binary dependencies"""
        binaries = {
            'wkhtmltopdf': {
                'required_for': 'pdfkit backend',
                'install_url': 'https://wkhtmltopdf.org/downloads.html',
                'test_command': ['wkhtmltopdf', '--version']
            },
            'chrome': {
                'required_for': 'selenium backend',
                'install_url': 'https://www.google.com/chrome/',
                'test_command': ['google-chrome', '--version']
            },
            'chromedriver': {
                'required_for': 'selenium backend',
                'install_url': 'https://chromedriver.chromium.org/',
                'test_command': ['chromedriver', '--version']
            }
        }
        
        results = {}
        
        for binary_name, info in binaries.items():
            status = self._check_binary(info['test_command'])
            results[binary_name] = {
                'available': status['available'],
                'version': status['version'],
                'required_for': info['required_for'],
                'install_url': info['install_url'],
                'error': status.get('error')
            }
        
        return results
    
    def _check_binary(self, command: List[str]) -> Dict:
        """Check if external binary is available"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version from output
                version = result.stdout.strip().split('\n')[0]
                return {
                    'available': True,
                    'version': version
                }
            else:
                return {
                    'available': False,
                    'version': None,
                    'error': result.stderr.strip()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'version': None,
                'error': 'Command timeout'
            }
        except FileNotFoundError:
            return {
                'available': False,
                'version': None,
                'error': 'Binary not found in PATH'
            }
        except Exception as e:
            return {
                'available': False,
                'version': None,
                'error': str(e)
            }
    
    def _check_permissions(self) -> Dict:
        """Check file system permissions"""
        import tempfile
        
        results = {
            'temp_directory': {'writable': False, 'path': ''},
            'upload_directory': {'writable': False, 'path': ''},
            'log_directory': {'writable': False, 'path': ''}
        }
        
        # Test temp directory
        try:
            temp_dir = tempfile.gettempdir()
            test_file = os.path.join(temp_dir, f'test_{os.getpid()}.tmp')
            
            with open(test_file, 'w') as f:
                f.write('test')
            
            os.unlink(test_file)
            
            results['temp_directory'] = {
                'writable': True,
                'path': temp_dir
            }
            
        except Exception as e:
            results['temp_directory']['error'] = str(e)
        
        # Test upload directory (if it exists)
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        if os.path.exists(upload_dir):
            try:
                test_file = os.path.join(upload_dir, f'test_{os.getpid()}.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.unlink(test_file)
                
                results['upload_directory'] = {
                    'writable': True,
                    'path': upload_dir
                }
            except Exception as e:
                results['upload_directory']['error'] = str(e)
        
        # Test log directory
        log_dir = os.path.join(os.getcwd(), 'logs')
        try:
            os.makedirs(log_dir, exist_ok=True)
            test_file = os.path.join(log_dir, f'test_{os.getpid()}.tmp')
            
            with open(test_file, 'w') as f:
                f.write('test')
            
            os.unlink(test_file)
            
            results['log_directory'] = {
                'writable': True,
                'path': log_dir
            }
            
        except Exception as e:
            results['log_directory']['error'] = str(e)
        
        return results
    
    def _generate_recommendations(self, results: Dict) -> List[str]:
        """Generate setup recommendations based on validation results"""
        recommendations = []
        
        # Python version
        if not results['python_version']['is_compatible']:
            recommendations.append(
                f"⚠️  Upgrade Python to version {results['python_version']['minimum_required']} or higher"
            )
        
        # PDF backends
        backend_summary = results['backends']['summary']
        if backend_summary['available_backends'] == 0:
            recommendations.append(
                "❌ No PDF backends available! Install at least one:"
                "\n   • WeasyPrint: pip install weasyprint"
                "\n   • pdfkit: pip install pdfkit + install wkhtmltopdf binary"
                "\n   • Selenium: pip install selenium + install Chrome + ChromeDriver"
            )
        elif backend_summary['available_backends'] == 1:
            recommendations.append(
                "💡 Consider installing additional PDF backends for redundancy and feature variety"
            )
        
        # Check individual backend issues
        for backend_name, backend_info in results['backends'].items():
            if backend_name == 'summary':
                continue
                
            if not backend_info['available']:
                if backend_name == 'weasyprint':
                    recommendations.append(
                        "💡 Install WeasyPrint for best CSS support: pip install weasyprint"
                    )
                elif backend_name == 'pdfkit':
                    if not results['binaries']['wkhtmltopdf']['available']:
                        recommendations.append(
                            "💡 Install wkhtmltopdf binary for pdfkit backend: https://wkhtmltopdf.org/downloads.html"
                        )
                elif backend_name == 'selenium':
                    missing = []
                    if not results['binaries']['chrome']['available']:
                        missing.append('Chrome browser')
                    if not results['binaries']['chromedriver']['available']:
                        missing.append('ChromeDriver')
                    
                    if missing:
                        recommendations.append(
                            f"💡 Install {' and '.join(missing)} for Selenium backend"
                        )
        
        # Dependencies
        for category, deps in results['dependencies'].items():
            missing = [dep for dep in deps if not dep['installed']]
            if missing and category == 'required':
                dep_names = [dep['name'] for dep in missing]
                recommendations.append(
                    f"❌ Install required dependencies: pip install {' '.join(dep_names)}"
                )
            elif missing and category == 'optional':
                dep_names = [dep['name'] for dep in missing]
                recommendations.append(
                    f"💡 Install optional dependencies for enhanced features: pip install {' '.join(dep_names)}"
                )
        
        # Permissions
        perm_issues = []
        for dir_type, perm_info in results['permissions'].items():
            if not perm_info['writable']:
                perm_issues.append(dir_type.replace('_', ' '))
        
        if perm_issues:
            recommendations.append(
                f"⚠️  Check write permissions for: {', '.join(perm_issues)}"
            )
        
        # System-specific recommendations
        if self.system_info['platform'] == 'Windows':
            recommendations.append(
                "💡 Windows users: Consider using Windows Subsystem for Linux (WSL) for better compatibility"
            )
        elif self.system_info['platform'] == 'Linux':
            recommendations.append(
                "💡 Linux users: Install system packages for WeasyPrint:\n"
                "   sudo apt-get install python3-dev python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev"
            )
        elif self.system_info['platform'] == 'Darwin':
            recommendations.append(
                "💡 macOS users: Install system dependencies:\n"
                "   brew install cairo pango gdk-pixbuf libffi"
            )
        
        return recommendations
    
    def _get_overall_status(self, results: Dict) -> Dict:
        """Determine overall setup status"""
        issues = []
        warnings = []
        
        # Critical issues
        if not results['python_version']['is_compatible']:
            issues.append("Incompatible Python version")
        
        if results['backends']['summary']['available_backends'] == 0:
            issues.append("No PDF backends available")
        
        # Required dependencies
        required_deps = results['dependencies']['required']
        missing_required = [dep['name'] for dep in required_deps if not dep['installed']]
        if missing_required:
            issues.append(f"Missing required dependencies: {', '.join(missing_required)}")
        
        # Warnings
        if results['backends']['summary']['available_backends'] == 1:
            warnings.append("Only one PDF backend available")
        
        # Permission issues
        perm_issues = []
        for dir_type, perm_info in results['permissions'].items():
            if not perm_info['writable']:
                perm_issues.append(dir_type)
        
        if perm_issues:
            warnings.append(f"Permission issues: {', '.join(perm_issues)}")
        
        # Determine status
        if issues:
            status = 'ERROR'
            message = f"Setup has critical issues: {'; '.join(issues)}"
        elif warnings:
            status = 'WARNING'
            message = f"Setup has warnings: {'; '.join(warnings)}"
        else:
            status = 'OK'
            message = "Setup is ready for HTML PDF conversion"
        
        return {
            'status': status,
            'message': message,
            'issues': issues,
            'warnings': warnings,
            'ready_for_production': status == 'OK'
        }
    
    def print_validation_report(self, results: Dict = None):
        """Print a formatted validation report"""
        if results is None:
            results = self.validate_full_setup()
        
        print("\n" + "="*70)
        print("🔍 HTML PDF CONVERTER - SETUP VALIDATION REPORT")
        print("="*70)
        
        # System Info
        print(f"\n📋 SYSTEM INFORMATION")
        print(f"   Platform: {results['system_info']['platform']} {results['system_info']['architecture']}")
        print(f"   Python: {results['python_version']['version']} ({'✅ Compatible' if results['python_version']['is_compatible'] else '❌ Incompatible'})")
        
        # Overall Status
        status_icon = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌"}
        overall = results['overall_status']
        print(f"\n🎯 OVERALL STATUS: {status_icon.get(overall['status'], '❓')} {overall['status']}")
        print(f"   {overall['message']}")
        
        # PDF Backends
        print(f"\n🖨️  PDF BACKENDS ({results['backends']['summary']['available_backends']}/{results['backends']['summary']['total_backends']} available)")
        for backend_name, backend_info in results['backends'].items():
            if backend_name == 'summary':
                continue
            
            icon = "✅" if backend_info['available'] else "❌"
            print(f"   {icon} {backend_name.title()}: {backend_info['description']}")
            
            if backend_info['available']:
                features = [k for k, v in backend_info['features'].items() if v]
                if features:
                    print(f"      Features: {', '.join(features)}")
        
        # Dependencies
        print(f"\n📦 DEPENDENCIES")
        for category, deps in results['dependencies'].items():
            print(f"   {category.title()}:")
            for dep in deps:
                icon = "✅" if dep['installed'] else "❌"
                version_info = f" (v{dep['version']})" if dep['version'] else ""
                print(f"      {icon} {dep['name']}{version_info}")
        
        # External Binaries
        print(f"\n🔧 EXTERNAL BINARIES")
        for binary_name, binary_info in results['binaries'].items():
            icon = "✅" if binary_info['available'] else "❌"
            version_info = f" ({binary_info['version']})" if binary_info['version'] else ""
            print(f"   {icon} {binary_name}{version_info}")
            if not binary_info['available']:
                print(f"      Required for: {binary_info['required_for']}")
                print(f"      Install from: {binary_info['install_url']}")
        
        # Permissions
        print(f"\n🔒 PERMISSIONS")
        for dir_type, perm_info in results['permissions'].items():
            icon = "✅" if perm_info['writable'] else "❌"
            path_info = f" ({perm_info['path']})" if perm_info['path'] else ""
            print(f"   {icon} {dir_type.replace('_', ' ').title()}{path_info}")
        
        # Recommendations
        if results['recommendations']:
            print(f"\n💡 RECOMMENDATIONS")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*70)
        
        return results
    
    def test_conversion(self) -> Dict:
        """Test actual PDF conversion functionality"""
        print("\n🧪 TESTING PDF CONVERSION...")
        
        test_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Document</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 2cm; }
                h1 { color: #2c3e50; }
                .test-box { 
                    background: #ecf0f1; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h1>HTML PDF Converter Test</h1>
            <div class="test-box">
                <p>This is a test document to verify PDF conversion functionality.</p>
                <ul>
                    <li>Basic HTML structure ✓</li>
                    <li>CSS styling ✓</li>
                    <li>UTF-8 encoding: 你好 🌍</li>
                </ul>
            </div>
            <p>Generated on: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
        </body>
        </html>
        """
        
        test_results = {}
        
        try:
            from .html_pdf_utils import get_converter
            converter = get_converter()
            
            if not converter.backends:
                test_results['status'] = 'FAILED'
                test_results['error'] = 'No PDF backends available'
                return test_results
            
            # Test conversion
            start_time = time.time()
            pdf_bytes, metadata = converter.convert_content_to_pdf(test_html)
            conversion_time = time.time() - start_time
            
            test_results.update({
                'status': 'SUCCESS',
                'backend_used': metadata['backend'],
                'pdf_size': len(pdf_bytes),
                'conversion_time': round(conversion_time, 2),
                'metadata': metadata
            })
            
            # Test thumbnail generation
            try:
                thumbnail = converter.generate_thumbnail(pdf_bytes)
                test_results['thumbnail_generated'] = thumbnail is not None
                if thumbnail:
                    test_results['thumbnail_size'] = len(thumbnail)
            except Exception as e:
                test_results['thumbnail_error'] = str(e)
            
            print(f"   ✅ Conversion successful!")
            print(f"   📄 PDF Size: {self._format_size(len(pdf_bytes))}")
            print(f"   ⏱️  Time: {conversion_time:.2f}s")
            print(f"   🔧 Backend: {metadata['backend']}")
            
        except Exception as e:
            test_results.update({
                'status': 'FAILED',
                'error': str(e)
            })
            print(f"   ❌ Conversion failed: {e}")
        
        return test_results
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def generate_setup_script(self, platform: str = None) -> str:
        """Generate setup script for the current platform"""
        if platform is None:
            platform = self.system_info['platform'].lower()
        
        scripts = {
            'windows': self._generate_windows_setup(),
            'linux': self._generate_linux_setup(),
            'darwin': self._generate_macos_setup()
        }
        
        return scripts.get(platform, self._generate_generic_setup())
    
    def _generate_windows_setup(self) -> str:
        """Generate Windows setup script"""
        return """
# Windows Setup Script for HTML PDF Converter
# Run in PowerShell as Administrator

# Install Python dependencies
pip install weasyprint pdfkit selenium PyMuPDF beautifulsoup4 lxml Pillow requests

# Download and install wkhtmltopdf
# Visit: https://wkhtmltopdf.org/downloads.html
# Download Windows installer and run it

# Download and install Chrome browser
# Visit: https://www.google.com/chrome/

# Download ChromeDriver
# Visit: https://chromedriver.chromium.org/
# Extract chromedriver.exe to a directory in your PATH

# Verify installation
python -c "from utils.web_code.setup_validator import SetupValidator; SetupValidator().print_validation_report()"
        """.strip()
    
    def _generate_linux_setup(self) -> str:
        """Generate Linux setup script"""
        return """
#!/bin/bash
# Linux Setup Script for HTML PDF Converter

# Update package list
sudo apt-get update

# Install system dependencies for WeasyPrint
sudo apt-get install -y python3-dev python3-cffi libcairo2 libpango-1.0-0 \\
    libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info

# Install wkhtmltopdf
sudo apt-get install -y wkhtmltopdf

# Install Chrome browser
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE)
wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip"
sudo unzip /tmp/chromedriver.zip -d /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Install Python dependencies
pip3 install weasyprint pdfkit selenium PyMuPDF beautifulsoup4 lxml Pillow requests

# Verify installation
python3 -c "from utils.web_code.setup_validator import SetupValidator; SetupValidator().print_validation_report()"
        """.strip()
    
    def _generate_macos_setup(self) -> str:
        """Generate macOS setup script"""
        return """
#!/bin/bash
# macOS Setup Script for HTML PDF Converter

# Install Homebrew if not present
if ! command -v brew &> /dev/null; then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install system dependencies for WeasyPrint
brew install cairo pango gdk-pixbuf libffi

# Install wkhtmltopdf
brew install wkhtmltopdf

# Install Chrome browser
brew install --cask google-chrome

# Install ChromeDriver
brew install chromedriver

# Install Python dependencies
pip3 install weasyprint pdfkit selenium PyMuPDF beautifulsoup4 lxml Pillow requests

# Verify installation
python3 -c "from utils.web_code.setup_validator import SetupValidator; SetupValidator().print_validation_report()"
        """.strip()
    
    def _generate_generic_setup(self) -> str:
        """Generate generic setup instructions"""
        return """
# Generic Setup Instructions for HTML PDF Converter

# 1. Install Python dependencies
pip install weasyprint pdfkit selenium PyMuPDF beautifulsoup4 lxml Pillow requests

# 2. Install external binaries:
#    - wkhtmltopdf: https://wkhtmltopdf.org/downloads.html
#    - Chrome browser: https://www.google.com/chrome/
#    - ChromeDriver: https://chromedriver.chromium.org/

# 3. Verify installation
python -c "from utils.web_code.setup_validator import SetupValidator; SetupValidator().print_validation_report()"
        """.strip()


def validate_setup():
    """Quick setup validation function"""
    validator = SetupValidator()
    return validator.validate_full_setup()


def print_setup_report():
    """Print setup validation report"""
    validator = SetupValidator()
    validator.print_validation_report()


def test_pdf_conversion():
    """Test PDF conversion functionality"""
    validator = SetupValidator()
    return validator.test_conversion()


if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description='HTML PDF Converter Setup Validator')
    parser.add_argument('--test', action='store_true', help='Run conversion test')
    parser.add_argument('--generate-script', choices=['windows', 'linux', 'macos'], 
                       help='Generate setup script for platform')
    parser.add_argument('--quiet', action='store_true', help='Suppress detailed output')
    
    args = parser.parse_args()
    
    validator = SetupValidator()
    
    if args.generate_script:
        script = validator.generate_setup_script(args.generate_script)
        print(script)
    else:
        results = validator.validate_full_setup()
        
        if not args.quiet:
            validator.print_validation_report(results)
        
        if args.test:
            test_results = validator.test_conversion()
            if test_results['status'] == 'SUCCESS':
                print("\n✅ PDF conversion test PASSED")
                sys.exit(0)
            else:
                print(f"\n❌ PDF conversion test FAILED: {test_results.get('error', 'Unknown error')}")
                sys.exit(1)
        
        # Exit with appropriate code
        overall_status = results['overall_status']['status']
        if overall_status == 'OK':
            sys.exit(0)
        elif overall_status == 'WARNING':
            sys.exit(1)
        else:
            sys.exit(2)
