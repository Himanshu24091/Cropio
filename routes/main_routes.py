# routes/main_routes.py - Phase 1.5 Dynamic Homepage Implementation
import os
from datetime import date, datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from flask_login import current_user
from sqlalchemy import func

from models import ConversionHistory, SystemSettings, UsageTracking, db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Dynamic homepage that changes based on authentication status"""

    # Define tool categories and configurations
    tools_config = {
        "free": [
            {
                "id": "image_converter",
                "title": "Image Converter",
                "description": "Convert between PNG, JPG, WEBP, PDF, ICO and more formats",
                "icon": "image",
                "url": "/image-converter",
                "category": "Images",
                "features": ["High Quality", "Batch Convert"],
                "card_class": "card-image",
            },
            {
                "id": "pdf_converter",
                "title": "PDF Converter",
                "description": "Convert PDFs to DOCX, TXT, HTML and many other formats",
                "icon": "pdf",
                "url": "/pdf-converter",
                "category": "PDF",
                "features": ["OCR Support", "Multi-format"],
                "card_class": "card-pdf",
            },
            {
                "id": "document_converter",
                "title": "Document Converter",
                "description": "Transform documents between various formats seamlessly",
                "icon": "document",
                "url": "/convert/documents/",
                "category": "Documents",
                "features": ["Smart Convert", "Preserve Format"],
                "card_class": "card-doc",
            },
            {
                "id": "excel_converter",
                "title": "Excel Converter",
                "description": "Convert Excel files to CSV, JSON, HTML and more",
                "icon": "excel",
                "url": "/excel-converter",
                "category": "Spreadsheets",
                "features": ["Data Intact", "Multiple Sheets"],
                "card_class": "card-excel",
            },
            {
                "id": "text_ocr",
                "title": "Text & OCR",
                "description": "Extract text from images and convert text files",
                "icon": "text",
                "url": "/text-ocr",
                "category": "Text",
                "features": ["AI Powered", "High Accuracy"],
                "card_class": "card-doc",
            },
        ],
        "free_with_login": [
            {
                "id": "markdown_html",
                "title": "Markdown ⇄ HTML",
                "description": "Convert between Markdown and HTML formats with live preview",
                "icon": "markdown",
                "url": "/markdown-html-converter",
                "category": "Documents",
                "features": ["Live Preview", "Syntax Highlighting"],
                "card_class": "card-doc",
                "new_feature": True,
            },
            {
                "id": "latex_pdf",
                "title": "LaTeX ⇄ PDF",
                "description": "Compile LaTeX to PDF and extract LaTeX from PDFs",
                "icon": "latex",
                "url": "/latex-pdf",
                "category": "Academic",
                "features": ["Math Support", "Bibliography"],
                "card_class": "card-academic",
                "new_feature": True,
            },
            {
                "id": "heic_jpg",
                "title": "HEIC ⇄ JPG",
                "description": "Convert Apple HEIC images to JPG and vice versa",
                "icon": "heic",
                "url": "/heic-jpg",
                "category": "Images",
                "features": ["iOS Compatible", "Quality Preserve"],
                "card_class": "card-image",
                "new_feature": True,
            },
            {
                "id": "raw_jpg",
                "title": "RAW ⇄ JPG",
                "description": "Convert camera RAW files to JPG with optimal settings",
                "icon": "raw",
                "url": "/raw-jpg",
                "category": "Photography",
                "features": ["Pro Quality", "Metadata Preserve"],
                "card_class": "card-image",
                "new_feature": True,
            },
            {
                "id": "gif_png_sequence",
                "title": "GIF ⇄ PNG Sequence",
                "description": "Extract PNG frames from GIF or create GIF from PNG sequence",
                "icon": "gif",
                "url": "/gif-png-sequence/",
                "category": "Animation",
                "features": ["Frame Control", "Quality Options"],
                "card_class": "card-animation",
                "new_feature": True,
            },
            {
                "id": "gif_mp4",
                "title": "GIF ⇄ MP4",
                "description": "Convert animated GIFs to MP4 video and vice versa",
                "icon": "video",
                "url": "/gif-mp4",
                "category": "Video",
                "features": ["Smaller Size", "Better Quality"],
                "card_class": "card-video",
                "new_feature": True,
            },
            {
                "id": "yaml_json",
                "title": "YAML ⇄ JSON",
                "description": "Convert between YAML and JSON configuration formats",
                "icon": "config",
                "url": "/yaml-json",
                "category": "Config",
                "features": ["Syntax Validate", "Format Preserve"],
                "card_class": "card-config",
                "new_feature": True,
            },
            {
                "id": "html_pdf_snapshot",
                "title": "HTML ⇄ PDF Snapshot",
                "description": "Create PDF snapshots of web pages and HTML content",
                "icon": "snapshot",
                "url": "/html-pdf-snapshot",
                "category": "Web",
                "features": ["Full Page", "Responsive"],
                "card_class": "card-web",
                "new_feature": True,
            },
        ],
        "premium": [
            {
                "id": "ai_watermark_remover",
                "title": "AI Watermark Remover",
                "description": "Remove watermarks from images using AI technology",
                "icon": "ai",
                "url": "#premium",
                "category": "AI Tools",
                "features": ["AI Powered", "Smart Detection"],
                "card_class": "card-premium",
                "premium_only": True,
            },
            {
                "id": "ai_background_changer",
                "title": "AI Background Changer",
                "description": "Change or remove image backgrounds with AI precision",
                "icon": "background",
                "url": "#premium",
                "category": "AI Tools",
                "features": ["Auto Detect", "HD Quality"],
                "card_class": "card-premium",
                "premium_only": True,
            },
            {
                "id": "ai_image_enhancer",
                "title": "AI Image Enhancer",
                "description": "Enhance image quality and resolution using AI",
                "icon": "enhance",
                "url": "#premium",
                "category": "AI Tools",
                "features": ["4K Upscale", "Noise Reduction"],
                "card_class": "card-premium",
                "premium_only": True,
            },
            {
                "id": "batch_processor",
                "title": "Batch Processor",
                "description": "Process hundreds of files simultaneously",
                "icon": "batch",
                "url": "#premium",
                "category": "Enterprise",
                "features": ["Bulk Processing", "Queue Management"],
                "card_class": "card-premium",
                "premium_only": True,
            },
        ],
    }

    # Get user context and usage data
    user_context = {
        "is_authenticated": current_user.is_authenticated,
        "is_premium": current_user.is_premium()
        if current_user.is_authenticated
        else False,
        "username": current_user.username if current_user.is_authenticated else None,
        "usage": None,
        "daily_limit": 5,
    }

    # Get usage data for authenticated users
    if current_user.is_authenticated:
        today_usage = UsageTracking.get_or_create_today(current_user.id)
        user_context["usage"] = {
            "conversions_used": today_usage.conversions_count,
            "daily_limit": 5 if not current_user.is_premium() else "unlimited",
            "percentage": (today_usage.conversions_count / 5 * 100)
            if not current_user.is_premium()
            else 0,
            "can_convert": current_user.can_convert(),
            "time_until_reset": _get_time_until_reset(),
        }

    # Additional tools that are always shown (not in free/premium categories)
    additional_tools = [
        {
            "title": "File Compressor",
            "description": "Reduce file sizes while maintaining quality",
            "url": "/file-compressor",
            "category": "Compression",
            "features": ["Lossless", "Fast"],
            "card_class": "card-excel",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>',
        },
        {
            "title": "Image Cropper",
            "description": "Crop images with pixel-perfect precision",
            "url": "/image-cropper",
            "category": "Editing",
            "features": ["Precise", "Easy to Use"],
            "card_class": "card-image",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
        },
        {
            "title": "PDF Editor",
            "description": "Add text, drawings, and annotations to PDFs",
            "url": "/pdf-editor",
            "category": "Editing",
            "features": ["Rich Editor", "Annotations"],
            "card_class": "card-pdf",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>',
        },
        {
            "title": "Secure PDFs",
            "description": "Password protection and advanced security features",
            "url": "/secure-pdf",
            "category": "Security",
            "features": ["Encrypted", "QR Unlock"],
            "card_class": "card-doc",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>',
        },
        {
            "title": "PDF Merge",
            "description": "Combine multiple PDFs with drag-and-drop reorder",
            "url": "/pdf-merge",
            "category": "PDF",
            "features": ["Drag-Drop", "Preview"],
            "card_class": "card-pdf",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>',
        },
        {
            "title": "PDF Signature",
            "description": "Create and apply digital signatures to your PDFs",
            "url": "/pdf-signature",
            "category": "PDF",
            "features": ["Digital Sign", "Easy Apply"],
            "card_class": "card-pdf",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>',
        },
        {
            "title": "PDF Page Delete",
            "description": "Remove unwanted pages from PDFs with precision",
            "url": "/pdf-page-delete",
            "category": "PDF",
            "features": ["Multi-Select", "Batch Process"],
            "card_class": "card-pdf",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>',
        },
        {
            "title": "Notebook Converter",
            "description": "Convert Jupyter Notebooks to various formats",
            "url": "/notebook-converter",
            "category": "Academic",
            "features": ["Multiple Formats", "Easy Export"],
            "card_class": "card-academic",
            "icon_svg": '<svg class="card-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path></svg>',
        },
    ]

    # Prepare tools based on authentication status
    if current_user.is_authenticated:
        # Logged-in users see all free tools + free-with-login tools + premium previews
        available_tools = tools_config["free"] + tools_config["free_with_login"]
        premium_tools = tools_config["premium"]
    else:
        # Anonymous users see only basic free tools
        available_tools = tools_config["free"]
        premium_tools = []

    return render_template(
        "index.html",
        tools=available_tools,
        premium_tools=premium_tools,
        additional_tools=additional_tools,  # Additional tools are now enabled
        user_context=user_context,
        show_upgrade_prompt=current_user.is_authenticated
        and not current_user.is_premium(),
    )


def _get_time_until_reset():
    """Calculate time until daily usage resets"""
    now = datetime.now()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    diff = tomorrow - now
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    return f"{hours}h {minutes}m"


@main_bp.route("/image-cropper")
def image_cropper_redirect():
    """Redirect to the actual image cropper route"""
    return redirect(url_for("image_cropper.image_cropper"))


@main_bp.route("/api/user-status")
def api_user_status():
    """API endpoint to get current user status for dynamic UI updates"""
    if not current_user.is_authenticated:
        return jsonify(
            {
                "authenticated": False,
                "show_login_prompt": True,
                "total_tools_available": 13,  # 5 free + 8 free-with-login
            }
        )

    today_usage = UsageTracking.get_or_create_today(current_user.id)

    return jsonify(
        {
            "authenticated": True,
            "username": current_user.username,
            "is_premium": current_user.is_premium(),
            "usage": {
                "conversions_used": today_usage.conversions_count,
                "daily_limit": 5 if not current_user.is_premium() else "unlimited",
                "percentage": (today_usage.conversions_count / 5 * 100)
                if not current_user.is_premium()
                else 0,
                "can_convert": current_user.can_convert(),
                "time_until_reset": _get_time_until_reset(),
            },
            "new_tools_count": 8,  # Number of free-with-login tools
            "show_welcome_message": True,
        }
    )


@main_bp.route("/api/usage-update")
def api_usage_update():
    """API endpoint to get updated usage information"""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    today_usage = UsageTracking.get_or_create_today(current_user.id)

    return jsonify(
        {
            "conversions_used": today_usage.conversions_count,
            "daily_limit": 5 if not current_user.is_premium() else "unlimited",
            "percentage": (today_usage.conversions_count / 5 * 100)
            if not current_user.is_premium()
            else 0,
            "can_convert": current_user.can_convert(),
            "time_until_reset": _get_time_until_reset(),
            "quota_exceeded": today_usage.conversions_count >= 5
            and not current_user.is_premium(),
        }
    )


@main_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


# Legacy redirects for old URLs
@main_bp.route("/presentation-converter/")
@main_bp.route("/presentation-converter")
def presentation_converter_redirect():
    """Redirect old presentation converter URLs to new location"""
    return redirect("/convert/presentation")


@main_bp.route("/document-converter/")
@main_bp.route("/document-converter")
def document_converter_redirect():
    """Redirect old document converter URLs to new location"""
    return redirect("/convert/documents/")


@main_bp.route("/excel-converter/")
@main_bp.route("/excel-converter")
def excel_converter_redirect():
    """Redirect old Excel converter URLs to new location"""
    return redirect("/convert/excel/")


@main_bp.route("/notebook-converter/")
@main_bp.route("/notebook-converter")
def notebook_converter_redirect():
    """Redirect old notebook converter URLs to new location"""
    return redirect("/convert/notebook/")


@main_bp.route("/text-ocr-converters/")
@main_bp.route("/text-ocr-converters")
def text_ocr_converters_redirect():
    """Redirect old text OCR converters URLs to new location"""
    return redirect("/convert/text-ocr/")


# Legacy redirect for old File Compressor URL
@main_bp.route("/compressor/")
@main_bp.route("/compressor")
def compressor_redirect():
    """Redirect old /compressor URLs to new /file-compressor location"""
    return redirect("/file-compressor/")


# @main_bp.route('/text-ocr-converters/')
# @main_bp.route('/text-ocr-converters')
# def text_ocr_converters_redirect():
#     """Redirect old text OCR converters URLs to new location"""
#     return redirect('/convert/text-ocr/')


@main_bp.route("/text-ocr")
def text_ocr_redirect():
    """Redirect /text-ocr to the correct text & OCR processor path"""
    return redirect("/convert/text-ocr/")


# @main_bp.route('/text-ocr-converters/')
# @main_bp.route('/text-ocr-converters')
# def text_ocr_converters_redirect():
#     """Redirect old text OCR converters URLs to new location"""
#     return redirect('/convert/text-ocr/')
