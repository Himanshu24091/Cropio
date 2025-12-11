# utils/text_ocr_converters/__init__.py
"""
Text & OCR Converters Utilities

This module provides comprehensive text extraction and OCR processing functionality
for various document and image formats.

Main Components:
- TextOCRProcessor: Core class for text extraction and OCR processing
- process_text_ocr: Convenience function for quick processing

Supported Input Formats:
- Images: PNG, JPG, JPEG (with OCR)
- Documents: PDF (text extraction + OCR fallback), DOCX, TXT
- Multi-language support including Hindi, English, Spanish, French, German, Arabic, Chinese, Japanese

Supported Output Formats:
- Plain Text (TXT)
- Word Document (DOCX)
- PDF Document

Features:
- Advanced OCR with Tesseract and EasyOCR support
- Multi-language text recognition
- Image preprocessing for better OCR accuracy
- Text cleaning and noise removal
- Confidence scoring for OCR results
- Format preservation options
"""

from .text_ocr_utils import TextOCRProcessor, process_text_ocr

__all__ = [
    "TextOCRProcessor",
    "process_text_ocr",
]

__version__ = "1.0.0"
__author__ = "Cropio Development Team"
__email__ = "dev@cropio.com"
__description__ = (
    "Text & OCR Processing utilities for document and image text extraction"
)
