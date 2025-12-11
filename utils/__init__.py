# utils/__init__.py

# Web code conversion utilities
try:
    from .web_code import (
        HTMLPDFConverter,
        get_converter,
        get_config_manager,
        get_tracker,
        format_file_size,
        PDFGenerationError,
        HTMLPDFError
    )
except ImportError:
    # Handle cases where dependencies might not be installed
    pass
