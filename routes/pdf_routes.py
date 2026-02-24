"""
PDF generation routes - API endpoints for PDF rendering with WeasyPrint
"""
import base64
from flask import Blueprint, request, jsonify, Response

from services.template_service import TemplateService
from services.pdf_service import PdfService


pdf_bp = Blueprint('pdf', __name__)

# Initialize services
template_service = TemplateService()
pdf_service = PdfService()


# ==========================================
# Core Rendering & PDF Generation Routes
# ==========================================

@pdf_bp.route('/render', methods=['POST'])
def render_template():
    """
    Render a Jinja2 template with data and return HTML
    
    Request body:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string"
    }
    
    Returns: Rendered HTML
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        template_html = data.get('template')
        if not template_html:
            return jsonify({'error': 'Template HTML is required'}), 400
        
        template_data = data.get('data', {})
        css = data.get('css', '')
        
        # Render the template
        rendered_html = template_service.render_template(
            template_html=template_html,
            data=template_data,
            css=css
        )
        
        return jsonify({
            'success': True,
            'html': rendered_html
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/generate', methods=['POST'])
def generate_pdf():
    """
    Generate a PDF from a Jinja2 template with data
    
    Request body:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string",
        "options": {
            "page_size": "A4",
            "orientation": "portrait"
        }
    }
    
    Returns: PDF as base64 encoded string
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        template_html = data.get('template')
        if not template_html:
            return jsonify({'error': 'Template HTML is required'}), 400
        
        template_data = data.get('data', {})
        css = data.get('css', '')
        options = data.get('options', {})
        
        # Render the template first
        rendered_html = template_service.render_template(
            template_html=template_html,
            data=template_data,
            css=css
        )
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            html=rendered_html,
            page_size=options.get('page_size', 'A4'),
            orientation=options.get('orientation', 'portrait')
        )
        
        # Return as base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'pdf': pdf_base64,
            'size': len(pdf_bytes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/generate-file', methods=['POST'])
def generate_pdf_file():
    """
    Generate a PDF from a Jinja2 template and return as file download
    
    Request body:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string",
        "options": {
            "page_size": "A4",
            "orientation": "portrait"
        },
        "filename": "output.pdf"
    }
    
    Returns: PDF file as binary response
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        template_html = data.get('template')
        if not template_html:
            return jsonify({'error': 'Template HTML is required'}), 400
        
        template_data = data.get('data', {})
        css = data.get('css', '')
        options = data.get('options', {})
        filename = data.get('filename', 'report.pdf')
        
        # Render the template first
        rendered_html = template_service.render_template(
            template_html=template_html,
            data=template_data,
            css=css
        )
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_pdf(
            html=rendered_html,
            page_size=options.get('page_size', 'A4'),
            orientation=options.get('orientation', 'portrait')
        )
        
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/preview', methods=['POST'])
def preview_html():
    """
    Generate preview HTML from a Jinja2 template with data
    Returns fully rendered HTML suitable for browser preview
    
    Request body:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string"
    }
    
    Returns: Rendered HTML as response
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        template_html = data.get('template')
        if not template_html:
            return jsonify({'error': 'Template HTML is required'}), 400
        
        template_data = data.get('data', {})
        css = data.get('css', '')
        
        # Render the template
        rendered_html = template_service.render_template(
            template_html=template_html,
            data=template_data,
            css=css
        )
        
        return Response(rendered_html, mimetype='text/html')
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
