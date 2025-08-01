# routes/pdf_editor_routes.py
from flask import Blueprint, render_template

pdf_editor_bp = Blueprint('pdf_editor', __name__)

@pdf_editor_bp.route('/pdf-editor')
def pdf_editor_page():
    """Renders the new PDF Editor page."""
    return render_template('pdf_editor.html')
