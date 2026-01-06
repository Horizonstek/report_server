"""
PDF generation routes
"""
import base64
import os
from flask import Blueprint, request, jsonify, Response
from werkzeug.utils import secure_filename
from services.pdf_service import PdfService
from services.template_service import TemplateService
from services.database_service import get_database_service
from config import get_config

pdf_bp = Blueprint('pdf', __name__)
config = get_config()
pdf_service = PdfService()
template_service = TemplateService(templates_dir=config.TEMPLATES_DIR)
db_service = get_database_service(config)


@pdf_bp.route('/upload', methods=['POST'])
def upload_template():
    """
    Upload a template file
    
    Request: multipart/form-data
    - file: HTML template file
    - code: Optional template code (filename without .html)
            If not provided, uses the original filename
    - query_id: Optional linked query ID/code
    """
    try:
        # Check if file was provided
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Get template code
        code = request.form.get('code', '')
        if not code:
            # Use filename without extension as code
            code = os.path.splitext(file.filename or '')[0]
        
        # Get linked query ID (optional)
        query_id = request.form.get('query_id', '')
        
        # Validate file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > config.MAX_TEMPLATE_SIZE:
            return jsonify({
                'error': f'File size exceeds maximum allowed size ({config.MAX_TEMPLATE_SIZE} bytes)'
            }), 413
        
        # Read file content
        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'File must be valid UTF-8 text'}), 400
        
        # Save template
        try:
            template_path = template_service.save_template(code, content)
            
            # Save linked query association if provided
            if query_id:
                template_service.save_template_query_link(code, query_id)
            
            return jsonify({
                'success': True,
                'code': code,
                'path': template_path,
                'query_id': query_id if query_id else None,
                'message': f'Template "{code}" uploaded successfully'
            }), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except IOError as e:
            return jsonify({'error': f'Failed to save template: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/templates', methods=['GET'])
def list_templates():
    """
    List all available templates with their linked queries
    
    Returns: List of template objects with code and linkedQueryId
    """
    try:
        template_codes = template_service.list_templates()
        templates_with_links = []
        
        for code in template_codes:
            linked_query = template_service.get_template_query_link(code)
            templates_with_links.append({
                'code': code,
                'linkedQueryId': linked_query
            })
        
        return jsonify({
            'success': True,
            'templates': templates_with_links,
            'count': len(templates_with_links)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/templates/<code>', methods=['GET'])
def get_template(code):
    """
    Get a template's HTML content by code
    
    Args:
        code: Template code (filename without .html)
    
    Returns:
        Template HTML content
    """
    try:
        content = template_service.load_template_by_code(code)
        return jsonify({
            'success': True,
            'code': code,
            'content': content
        })
    except FileNotFoundError:
        return jsonify({'error': 'Template not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/templates/<code>', methods=['DELETE'])
def delete_template(code):
    """
    Delete a template by code
    
    Args:
        code: Template code (filename without .html)
    """
    try:
        template_service.delete_template(code)
        # Also try to delete linked query
        try:
            template_service.delete_query(code)
        except FileNotFoundError:
            pass  # No query linked, ignore
        return jsonify({
            'success': True,
            'message': f'Template "{code}" deleted successfully'
        })
    except FileNotFoundError:
        return jsonify({'error': 'Template not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==========================================
# Query Management Routes
# ==========================================

@pdf_bp.route('/queries', methods=['GET'])
def list_queries():
    """
    List all saved queries
    
    Returns: List of queries with their template codes
    """
    try:
        queries = template_service.list_queries()
        return jsonify({
            'success': True,
            'queries': queries,
            'count': len(queries)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/queries/<code>', methods=['GET'])
def get_query(code):
    """
    Get a SQL query by template code
    
    Args:
        code: Template code
    
    Returns:
        Query SQL and metadata
    """
    try:
        query_data = template_service.load_query(code)
        if not query_data:
            return jsonify({'error': f'No query linked to template "{code}"'}), 404
        return jsonify({
            'success': True,
            **query_data
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/queries/<code>', methods=['POST', 'PUT'])
def save_query(code):
    """
    Save/Update a SQL query linked to a template
    
    Args:
        code: Template code to link the query to
    
    Request body:
    {
        "sql": "SELECT * FROM table WHERE ...",
        "description": "Optional description"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        sql = data.get('sql')
        if not sql:
            return jsonify({'error': 'SQL query is required'}), 400
        
        description = data.get('description', '')
        
        query_path = template_service.save_query(code, sql, description)
        
        return jsonify({
            'success': True,
            'code': code,
            'path': query_path,
            'message': f'Query for "{code}" saved successfully'
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/queries/<code>', methods=['DELETE'])
def delete_query(code):
    """
    Delete a SQL query
    
    Args:
        code: Template code
    """
    try:
        template_service.delete_query(code)
        return jsonify({
            'success': True,
            'message': f'Query for "{code}" deleted successfully'
        })
    except FileNotFoundError:
        return jsonify({'error': f'No query linked to template "{code}"'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/templates/<code>/full', methods=['GET'])
def get_template_with_query(code):
    """
    Get a template with its linked query
    
    Args:
        code: Template code
    
    Returns:
        Template HTML and linked query (if any)
    """
    try:
        result = template_service.get_template_with_query(code)
        return jsonify({
            'success': True,
            **result
        })
    except FileNotFoundError:
        return jsonify({'error': 'Template not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/render', methods=['POST'])
def render_template():
    """
    Render a Jinja2 template with data and return HTML
    
    Request body can use either:
    1. Inline template:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string"
    }
    
    2. Saved template by code:
    {
        "code": "filename",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Check if using code-based template
        code = data.get('code')
        template_html = data.get('template')
        
        if code:
            # Load template from file
            try:
                template_html = template_service.load_template_by_code(code)
            except FileNotFoundError:
                return jsonify({'error': f'Template "{code}" not found'}), 404
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif not template_html:
            return jsonify({'error': 'Either "code" or "template" is required'}), 400
        
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
    
    Request body can use either:
    1. Inline template:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string",
        "options": {
            "page_size": "A4",
            "orientation": "portrait"
        }
    }
    
    2. Saved template by code:
    {
        "code": "filename",
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
        
        # Check if using code-based template
        code = data.get('code')
        template_html = data.get('template')
        
        if code:
            # Load template from file
            try:
                template_html = template_service.load_template_by_code(code)
            except FileNotFoundError:
                return jsonify({'error': f'Template "{code}" not found'}), 404
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif not template_html:
            return jsonify({'error': 'Either "code" or "template" is required'}), 400
        
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
    
    Request body can use either:
    1. Inline template:
    {
        "template": "<html>{{ variable }}</html>",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string",
        "options": {...},
        "filename": "output.pdf"
    }
    
    2. Saved template by code:
    {
        "code": "filename",
        "data": {"variable": "value", "rows": [...]},
        "css": "optional css string",
        "options": {...},
        "filename": "output.pdf"
    }
    
    Returns: PDF file as binary response
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Check if using code-based template
        code = data.get('code')
        template_html = data.get('template')
        
        if code:
            # Load template from file
            try:
                template_html = template_service.load_template_by_code(code)
            except FileNotFoundError:
                return jsonify({'error': f'Template "{code}" not found'}), 404
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        elif not template_html:
            return jsonify({'error': 'Either "code" or "template" is required'}), 400
        
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
    This returns fully rendered HTML suitable for browser preview
    
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


# ==========================================
# Oracle Database Integration Routes
# ==========================================

@pdf_bp.route('/db/status', methods=['GET'])
def database_status():
    """
    Check Oracle database connection status
    
    Returns:
        Database availability and connection status
    """
    try:
        available = db_service.is_available()
        enabled = db_service.is_enabled()
        configured = db_service.is_configured()
        
        result = {
            'success': True,
            'oracle_driver_available': available,
            'oracle_enabled': enabled,
            'oracle_configured': configured,
            'connection_status': 'not_tested'
        }
        
        if available and configured:
            success, message = db_service.test_connection()
            result['connection_status'] = 'connected' if success else 'failed'
            result['connection_message'] = message
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/db/test-query', methods=['POST'])
def test_query():
    """
    Test execute a SQL query and return results
    
    Request body:
    {
        "sql": "SELECT * FROM table WHERE id = :id",
        "params": {"id": 123}
    }
    
    Returns:
        Query results with metadata
    """
    try:
        if not db_service.is_available():
            return jsonify({'error': 'Oracle database driver not available'}), 503
        
        if not db_service.is_configured():
            return jsonify({'error': 'Oracle database not configured'}), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        sql = data.get('sql')
        if not sql:
            return jsonify({'error': 'SQL query is required'}), 400
        
        params = data.get('params', {})
        
        # Execute query
        result = db_service.execute_query_with_metadata(sql, params)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/db/generate', methods=['POST'])
def generate_pdf_from_db():
    """
    Generate a PDF using a template and data from Oracle database
    
    Request body:
    {
        "code": "template_code",
        "sql": "SELECT * FROM table WHERE ...",  // Optional, uses linked query if not provided
        "params": {"param1": "value1"},  // Query parameters
        "extra_data": {"title": "Report Title"},  // Additional template data
        "css": "optional css string",
        "options": {
            "page_size": "A4",
            "orientation": "portrait"
        }
    }
    
    Returns: PDF as base64 encoded string
    """
    try:
        if not db_service.is_available():
            return jsonify({'error': 'Oracle database driver not available'}), 503
        
        if not db_service.is_configured():
            return jsonify({'error': 'Oracle database not configured'}), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({'error': 'Template code is required'}), 400
        
        # Load template
        try:
            template_html = template_service.load_template_by_code(code)
        except FileNotFoundError:
            return jsonify({'error': f'Template "{code}" not found'}), 404
        
        # Get SQL query - either from request or linked query
        sql = data.get('sql')
        if not sql:
            # Try to load linked query
            query_data = template_service.load_query(code)
            if query_data and query_data.get('sql'):
                sql = query_data['sql']
            else:
                return jsonify({
                    'error': 'No SQL query provided and no linked query found for template'
                }), 400
        
        params = data.get('params', {})
        extra_data = data.get('extra_data', {})
        css = data.get('css', '')
        options = data.get('options', {})
        
        # Execute query and get data
        query_result = db_service.execute_query_with_metadata(sql, params)
        
        # Prepare template data
        template_data = {
            'rows': query_result['rows'],
            'columns': query_result['columns'],
            'row_count': query_result['row_count'],
            **extra_data
        }
        
        # Render template
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
        
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'pdf': pdf_base64,
            'size': len(pdf_bytes),
            'rows_processed': query_result['row_count']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/db/generate-file', methods=['POST'])
def generate_pdf_file_from_db():
    """
    Generate a PDF file using a template and data from Oracle database
    
    Request body:
    {
        "code": "template_code",
        "sql": "SELECT * FROM table WHERE ...",  // Optional, uses linked query if not provided
        "params": {"param1": "value1"},
        "extra_data": {"title": "Report Title"},
        "css": "optional css string",
        "options": {
            "page_size": "A4",
            "orientation": "portrait"
        },
        "filename": "report.pdf"
    }
    
    Returns: PDF file as binary response
    """
    try:
        if not db_service.is_available():
            return jsonify({'error': 'Oracle database driver not available'}), 503
        
        if not db_service.is_configured():
            return jsonify({'error': 'Oracle database not configured'}), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({'error': 'Template code is required'}), 400
        
        # Load template
        try:
            template_html = template_service.load_template_by_code(code)
        except FileNotFoundError:
            return jsonify({'error': f'Template "{code}" not found'}), 404
        
        # Get SQL query
        sql = data.get('sql')
        if not sql:
            query_data = template_service.load_query(code)
            if query_data and query_data.get('sql'):
                sql = query_data['sql']
            else:
                return jsonify({
                    'error': 'No SQL query provided and no linked query found for template'
                }), 400
        
        params = data.get('params', {})
        extra_data = data.get('extra_data', {})
        css = data.get('css', '')
        options = data.get('options', {})
        filename = data.get('filename', 'report.pdf')
        
        # Execute query
        query_result = db_service.execute_query_with_metadata(sql, params)
        
        # Prepare template data
        template_data = {
            'rows': query_result['rows'],
            'columns': query_result['columns'],
            'row_count': query_result['row_count'],
            **extra_data
        }
        
        # Render template
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
                'Content-Disposition': f'attachment; filename="{filename}"',
                'X-Rows-Processed': str(query_result['row_count'])
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/db/render', methods=['POST'])
def render_from_db():
    """
    Render a template with data from Oracle database (HTML output)
    
    Request body:
    {
        "code": "template_code",
        "sql": "SELECT * FROM table WHERE ...",
        "params": {"param1": "value1"},
        "extra_data": {"title": "Report Title"},
        "css": "optional css string"
    }
    
    Returns: Rendered HTML
    """
    try:
        if not db_service.is_available():
            return jsonify({'error': 'Oracle database driver not available'}), 503
        
        if not db_service.is_configured():
            return jsonify({'error': 'Oracle database not configured'}), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({'error': 'Template code is required'}), 400
        
        # Load template
        try:
            template_html = template_service.load_template_by_code(code)
        except FileNotFoundError:
            return jsonify({'error': f'Template "{code}" not found'}), 404
        
        # Get SQL query
        sql = data.get('sql')
        if not sql:
            query_data = template_service.load_query(code)
            if query_data and query_data.get('sql'):
                sql = query_data['sql']
            else:
                return jsonify({
                    'error': 'No SQL query provided and no linked query found for template'
                }), 400
        
        params = data.get('params', {})
        extra_data = data.get('extra_data', {})
        css = data.get('css', '')
        
        # Execute query
        query_result = db_service.execute_query_with_metadata(sql, params)
        
        # Prepare template data
        template_data = {
            'rows': query_result['rows'],
            'columns': query_result['columns'],
            'row_count': query_result['row_count'],
            **extra_data
        }
        
        # Render template
        rendered_html = template_service.render_template(
            template_html=template_html,
            data=template_data,
            css=css
        )
        
        return jsonify({
            'success': True,
            'html': rendered_html,
            'rows_processed': query_result['row_count']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pdf_bp.route('/db/preview', methods=['POST'])
def preview_from_db():
    """
    Generate HTML preview using template and data from Oracle database
    
    Request body:
    {
        "code": "template_code",
        "sql": "SELECT * FROM table WHERE ...",
        "params": {"param1": "value1"},
        "extra_data": {"title": "Report Title"},
        "css": "optional css string"
    }
    
    Returns: Rendered HTML as response (for browser preview)
    """
    try:
        if not db_service.is_available():
            return jsonify({'error': 'Oracle database driver not available'}), 503
        
        if not db_service.is_configured():
            return jsonify({'error': 'Oracle database not configured'}), 503
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        code = data.get('code')
        if not code:
            return jsonify({'error': 'Template code is required'}), 400
        
        # Load template
        try:
            template_html = template_service.load_template_by_code(code)
        except FileNotFoundError:
            return jsonify({'error': f'Template "{code}" not found'}), 404
        
        # Get SQL query
        sql = data.get('sql')
        if not sql:
            query_data = template_service.load_query(code)
            if query_data and query_data.get('sql'):
                sql = query_data['sql']
            else:
                return jsonify({
                    'error': 'No SQL query provided and no linked query found for template'
                }), 400
        
        params = data.get('params', {})
        extra_data = data.get('extra_data', {})
        css = data.get('css', '')
        
        # Execute query
        query_result = db_service.execute_query_with_metadata(sql, params)
        
        # Prepare template data
        template_data = {
            'rows': query_result['rows'],
            'columns': query_result['columns'],
            'row_count': query_result['row_count'],
            **extra_data
        }
        
        # Render template
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


@pdf_bp.route('/db/query-params/<code>', methods=['GET'])
def get_query_params(code):
    """
    Get the parameters required by a template's linked query
    
    Args:
        code: Template code
    
    Returns:
        List of parameter names found in the SQL query
    """
    try:
        query_data = template_service.load_query(code)
        
        if not query_data or not query_data.get('sql'):
            return jsonify({
                'error': f'No query linked to template "{code}"'
            }), 404
        
        sql = query_data['sql']
        params = db_service.parse_query_params(sql)
        
        return jsonify({
            'success': True,
            'code': code,
            'parameters': params,
            'sql': sql
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
