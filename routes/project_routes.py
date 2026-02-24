"""
Project management routes - API endpoints for report projects
"""
import os
import base64
from flask import Blueprint, request, jsonify, Response
from werkzeug.utils import secure_filename

from services.project_service import ProjectService
from services.subreport_service import SubReportService
from services.pdf_service import PdfService
from services.database_service import get_database_service
from config import get_config


project_bp = Blueprint('projects', __name__)
config = get_config()

# Initialize services
projects_dir = os.path.join(config.TEMPLATES_DIR, '..', 'projects')
project_service = ProjectService(projects_dir)
pdf_service = PdfService()
db_service = get_database_service(config)


# ==========================================
# Project CRUD Routes
# ==========================================

@project_bp.route('/templates', methods=['GET'])
def list_templates():
    """
    List available project templates (starter projects)
    
    Returns: List of template summaries
    """
    try:
        templates = project_service.list_templates()
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('', methods=['POST'])
def create_project():
    """
    Create a new report project
    
    Request body:
    {
        "name": "Monthly Sales Report",
        "description": "Sales report with charts",
        "author": "John Doe",
        "pageSize": "A4",
        "orientation": "portrait"
    }
    
    Returns: Created project info
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Project name is required'}), 400
        
        project = project_service.create_project(
            name=name,
            description=data.get('description', ''),
            author=data.get('author', ''),
            page_size=data.get('pageSize', 'A4'),
            orientation=data.get('orientation', 'portrait'),
            template=data.get('template')
        )
        
        return jsonify({
            'success': True,
            'project': project
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('', methods=['GET'])
def list_projects():
    """
    List all available projects
    
    Returns: List of project summaries
    """
    try:
        projects = project_service.list_projects()
        return jsonify({
            'success': True,
            'projects': projects,
            'count': len(projects)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Get project details
    
    Args:
        project_id: Project identifier
        
    Returns: Full project configuration
    """
    try:
        project = project_service.load_project(project_id)
        return jsonify({
            'success': True,
            **project
        })
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Update project configuration
    
    Args:
        project_id: Project identifier
        
    Request body: Fields to update
    
    Returns: Updated project
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        project = project_service.update_project(project_id, data)
        
        return jsonify({
            'success': True,
            **project
        })
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Delete a project
    
    Args:
        project_id: Project identifier
        
    Returns: Success message
    """
    try:
        project_service.delete_project(project_id)
        return jsonify({
            'success': True,
            'message': f"Project '{project_id}' deleted"
        })
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# Project Validation Routes
# ==========================================

@project_bp.route('/<project_id>/validate', methods=['GET'])
def validate_project(project_id):
    """
    Validate project structure and references
    
    Args:
        project_id: Project identifier
        
    Returns: Validation results with errors and warnings
    """
    try:
        result = project_service.validate_project(project_id)
        return jsonify({
            'success': True,
            'project_id': project_id,
            **result
        })
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# Query Retrieval Routes
# ==========================================

@project_bp.route('/<project_id>/query/<query_name>', methods=['GET'])
def get_project_query(project_id, query_name):
    """
    Get the SQL content of a project query file
    
    Args:
        project_id: Project identifier
        query_name: Query name (without .sql extension)
        
    Returns: SQL content
    """
    try:
        project = project_service.load_project(project_id)
        query_path = os.path.join(project['path'], 'queries', f'{query_name}.sql')
        
        if not os.path.exists(query_path):
            return jsonify({'error': f"Query '{query_name}' not found"}), 404
        
        with open(query_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        return jsonify({
            'success': True,
            'sql': sql,
            'queryName': query_name,
            'projectId': project_id
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# Sub-Report Management Routes
# ==========================================

@project_bp.route('/<project_id>/subreports', methods=['POST'])
def add_subreport(project_id):
    """
    Add a sub-report to a project
    
    Args:
        project_id: Project identifier
        
    Request body:
    {
        "id": "header",
        "templateName": "header",
        "queryName": "header_stats",  // optional
        "position": "header"  // header, footer, inline
    }
    
    Returns: Updated project
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        subreport_id = data.get('id')
        if not subreport_id:
            return jsonify({'error': 'Sub-report id is required'}), 400
        
        template_name = data.get('templateName', subreport_id)
        query_name = data.get('queryName')
        position = data.get('position', 'inline')
        
        project = project_service.add_subreport(
            project_id=project_id,
            subreport_id=subreport_id,
            template_name=template_name,
            query_name=query_name,
            position=position
        )
        
        return jsonify({
            'success': True,
            **project
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/subreports/<subreport_id>', methods=['DELETE'])
def remove_subreport(project_id, subreport_id):
    """
    Remove a sub-report from a project
    
    Args:
        project_id: Project identifier
        subreport_id: Sub-report identifier
        
    Returns: Updated project
    """
    try:
        project = project_service.load_project(project_id)
        config = project['config']
        
        # Filter out the sub-report
        original_count = len(config.get('subReports', []))
        config['subReports'] = [
            sr for sr in config.get('subReports', [])
            if sr.get('id') != subreport_id
        ]
        
        if len(config['subReports']) == original_count:
            return jsonify({'error': f"Sub-report '{subreport_id}' not found"}), 404
        
        updated = project_service.update_project(project_id, {'subReports': config['subReports']})
        
        return jsonify({
            'success': True,
            **updated
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# Asset Management Routes
# ==========================================

@project_bp.route('/<project_id>/assets', methods=['POST'])
def upload_asset(project_id):
    """
    Upload an asset file to a project
    
    Args:
        project_id: Project identifier
        
    Request: multipart/form-data
        - file: Asset file
        - type: Asset type (fonts, images, styles)
        - name: Optional custom filename
        
    Returns: Updated project
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        asset_type = request.form.get('type', 'images')
        if asset_type not in ['fonts', 'images', 'styles']:
            return jsonify({'error': 'Invalid asset type. Use: fonts, images, styles'}), 400
        
        # Validate file extension
        allowed_extensions = {
            'fonts': ['.ttf', '.otf', '.woff', '.woff2'],
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
            'styles': ['.css']
        }
        
        filename = secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in allowed_extensions[asset_type]:
            return jsonify({
                'error': f"Invalid file type for {asset_type}. Allowed: {allowed_extensions[asset_type]}"
            }), 400
        
        # Save file temporarily
        project = project_service.load_project(project_id)
        target_dir = os.path.join(project['path'], 'assets', asset_type)
        os.makedirs(target_dir, exist_ok=True)
        
        custom_name = request.form.get('name')
        if custom_name:
            filename = secure_filename(custom_name)
            if not filename.endswith(ext):
                filename += ext
        
        file_path = os.path.join(target_dir, filename)
        file.save(file_path)
        
        # Update project config
        config = project['config']
        if 'assets' not in config:
            config['assets'] = {'fonts': [], 'images': [], 'styles': []}
        if asset_type not in config['assets']:
            config['assets'][asset_type] = []
        
        relative_path = f"assets/{asset_type}/{filename}"
        if relative_path not in config['assets'][asset_type]:
            config['assets'][asset_type].append(relative_path)
        
        updated = project_service.update_project(project_id, {'assets': config['assets']})
        
        return jsonify({
            'success': True,
            'asset': {
                'type': asset_type,
                'path': relative_path,
                'name': filename
            },
            'project': updated
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/assets/<asset_type>/<filename>', methods=['DELETE'])
def delete_asset(project_id, asset_type, filename):
    """
    Delete an asset from a project
    
    Args:
        project_id: Project identifier
        asset_type: Asset type (fonts, images, styles)
        filename: Asset filename
        
    Returns: Updated project
    """
    try:
        if asset_type not in ['fonts', 'images', 'styles']:
            return jsonify({'error': 'Invalid asset type'}), 400
        
        project = project_service.load_project(project_id)
        config = project['config']
        
        relative_path = f"assets/{asset_type}/{filename}"
        
        # Remove from filesystem
        full_path = os.path.join(project['path'], relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        
        # Remove from config
        if 'assets' in config and asset_type in config['assets']:
            config['assets'][asset_type] = [
                p for p in config['assets'][asset_type] 
                if p != relative_path
            ]
        
        updated = project_service.update_project(project_id, {'assets': config['assets']})
        
        return jsonify({
            'success': True,
            'message': f"Asset '{filename}' deleted",
            'project': updated
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/assets/styles/create', methods=['POST'])
def create_style(project_id):
    """
    Create a new CSS style file in a project
    
    Args:
        project_id: Project identifier
        
    Request body:
    {
        "name": "custom"  // Creates custom.css
    }
    
    Returns: Created style info with file path
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Style name is required'}), 400
        
        # Sanitize filename
        safe_name = secure_filename(name)
        if not safe_name:
            return jsonify({'error': 'Invalid style name'}), 400
        
        # Ensure .css extension
        if not safe_name.endswith('.css'):
            safe_name += '.css'
        
        project = project_service.load_project(project_id)
        config = project['config']
        
        # Create the CSS file
        target_dir = os.path.join(project['path'], 'assets', 'styles')
        os.makedirs(target_dir, exist_ok=True)
        
        file_path = os.path.join(target_dir, safe_name)
        if os.path.exists(file_path):
            return jsonify({'error': f"Style '{safe_name}' already exists"}), 400
        
        # Write default CSS content
        css_content = f"""/* {name} - Project Style */
/* Add your custom CSS here */

"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        # Register in project.json
        if 'assets' not in config:
            config['assets'] = {'fonts': [], 'images': [], 'styles': []}
        if 'styles' not in config['assets']:
            config['assets']['styles'] = []
        
        relative_path = f"assets/styles/{safe_name}"
        if relative_path not in config['assets']['styles']:
            config['assets']['styles'].append(relative_path)
        
        updated = project_service.update_project(project_id, {'assets': config['assets']})
        
        return jsonify({
            'success': True,
            'style': {
                'name': safe_name,
                'path': relative_path,
                'fullPath': file_path
            },
            'project': updated
        }), 201
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==========================================
# Rendering Routes
# ==========================================

@project_bp.route('/<project_id>/render', methods=['POST'])
def render_project(project_id):
    """
    Render a project report as PDF
    
    Args:
        project_id: Project identifier
        
    Request body:
    {
        "params": {"start_date": "2026-01-01"},  // Query parameters
        "subreportData": {  // Optional, execute queries if not provided
            "header": {"title": "Header Data"}
        },
        "mainData": {},  // Optional, execute main query if not provided
        "options": {
            "pageSize": "A4",
            "orientation": "portrait"
        }
    }
    
    Returns: PDF as base64
    """
    try:
        project = project_service.load_project(project_id)
        config = project['config']
        
        data = request.get_json() or {}
        params = data.get('params', {})
        options = data.get('options', {})
        
        # Initialize sub-report service
        subreport_service = SubReportService(project['path'], config)
        
        # Get main data - either from request or execute query
        main_data = data.get('mainData')
        if main_data is None and db_service.is_available() and db_service.is_configured():
            main_query_path = config.get('mainQuery')
            if main_query_path:
                sql = subreport_service.get_query_content(main_query_path)
                result = db_service.execute_query_with_metadata(sql, params)
                main_data = {
                    'rows': result['rows'],
                    'columns': result['columns'],
                    'row_count': result['row_count']
                }
        
        if main_data is None:
            main_data = {}
        
        # Get sub-report data - either from request or execute queries
        subreport_data = data.get('subreportData', {})
        if not subreport_data and db_service.is_available() and db_service.is_configured():
            for sr in config.get('subReports', []):
                sr_id = sr.get('id')
                sr_query = sr.get('query')
                if sr_id and sr_query:
                    try:
                        sql = subreport_service.get_query_content(sr_query)
                        result = db_service.execute_query_with_metadata(sql, params)
                        subreport_data[sr_id] = {
                            'rows': result['rows'],
                            'columns': result['columns'],
                            'row_count': result['row_count']
                        }
                    except (FileNotFoundError, Exception):
                        subreport_data[sr_id] = {}
        
        # Add extra data from params
        main_data.update(data.get('extraData', {}))
        
        # Compose the full report
        rendered_html = subreport_service.compose_report(main_data, subreport_data)
        
        # Generate PDF
        page_size = options.get('pageSize', config.get('settings', {}).get('pageSize', 'A4'))
        orientation = options.get('orientation', config.get('settings', {}).get('orientation', 'portrait'))
        
        pdf_bytes = pdf_service.generate_pdf(
            html=rendered_html,
            page_size=page_size,
            orientation=orientation,
            base_url=project_service.get_project_base_url(project_id)
        )
        
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return jsonify({
            'success': True,
            'pdf': pdf_base64,
            'size': len(pdf_bytes)
        })
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/render-file', methods=['POST'])
def render_project_file(project_id):
    """
    Render a project report as PDF file download
    
    Similar to /render but returns binary PDF file
    """
    try:
        project = project_service.load_project(project_id)
        config = project['config']
        
        data = request.get_json() or {}
        params = data.get('params', {})
        options = data.get('options', {})
        filename = data.get('filename', f"{project_id}_report.pdf")
        
        # Initialize sub-report service
        subreport_service = SubReportService(project['path'], config)
        
        # Get main data
        main_data = data.get('mainData')
        if main_data is None and db_service.is_available() and db_service.is_configured():
            main_query_path = config.get('mainQuery')
            if main_query_path:
                sql = subreport_service.get_query_content(main_query_path)
                result = db_service.execute_query_with_metadata(sql, params)
                main_data = {
                    'rows': result['rows'],
                    'columns': result['columns'],
                    'row_count': result['row_count']
                }
        
        if main_data is None:
            main_data = {}
        
        # Get sub-report data
        subreport_data = data.get('subreportData', {})
        if not subreport_data and db_service.is_available() and db_service.is_configured():
            for sr in config.get('subReports', []):
                sr_id = sr.get('id')
                sr_query = sr.get('query')
                if sr_id and sr_query:
                    try:
                        sql = subreport_service.get_query_content(sr_query)
                        result = db_service.execute_query_with_metadata(sql, params)
                        subreport_data[sr_id] = {
                            'rows': result['rows'],
                            'columns': result['columns']
                        }
                    except Exception:
                        subreport_data[sr_id] = {}
        
        main_data.update(data.get('extraData', {}))
        
        # Compose and generate PDF
        rendered_html = subreport_service.compose_report(main_data, subreport_data)
        
        page_size = options.get('pageSize', config.get('settings', {}).get('pageSize', 'A4'))
        orientation = options.get('orientation', config.get('settings', {}).get('orientation', 'portrait'))
        
        pdf_bytes = pdf_service.generate_pdf(
            html=rendered_html,
            page_size=page_size,
            orientation=orientation,
            base_url=project_service.get_project_base_url(project_id)
        )
        
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/preview', methods=['POST'])
def preview_project(project_id):
    """
    Preview project report as HTML
    
    Args:
        project_id: Project identifier
        
    Request body: Same as /render
        
    Returns: Rendered HTML
    """
    try:
        project = project_service.load_project(project_id)
        config = project['config']
        
        data = request.get_json() or {}
        params = data.get('params', {})
        
        # Initialize sub-report service
        subreport_service = SubReportService(project['path'], config)
        
        # Get main data
        main_data = data.get('mainData')
        if main_data is None and db_service.is_available() and db_service.is_configured():
            main_query_path = config.get('mainQuery')
            if main_query_path:
                try:
                    sql = subreport_service.get_query_content(main_query_path)
                    result = db_service.execute_query_with_metadata(sql, params)
                    main_data = {
                        'rows': result['rows'],
                        'columns': result['columns'],
                        'row_count': result['row_count']
                    }
                except Exception:
                    main_data = {}
        
        if main_data is None:
            main_data = {}
        
        # Get sub-report data
        subreport_data = data.get('subreportData', {})
        if not subreport_data and db_service.is_available() and db_service.is_configured():
            for sr in config.get('subReports', []):
                sr_id = sr.get('id')
                sr_query = sr.get('query')
                if sr_id and sr_query:
                    try:
                        sql = subreport_service.get_query_content(sr_query)
                        result = db_service.execute_query_with_metadata(sql, params)
                        subreport_data[sr_id] = {
                            'rows': result['rows'],
                            'columns': result['columns']
                        }
                    except Exception:
                        subreport_data[sr_id] = {}
        
        main_data.update(data.get('extraData', {}))
        
        # Compose the report
        rendered_html = subreport_service.compose_report(main_data, subreport_data)
        
        return Response(rendered_html, mimetype='text/html')
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/circular-check', methods=['GET'])
def check_circular_references(project_id):
    """
    Check for circular references in project sub-reports
    
    Args:
        project_id: Project identifier
        
    Returns: List of circular reference chains (empty if none)
    """
    try:
        project = project_service.load_project(project_id)
        subreport_service = SubReportService(project['path'], project['config'])
        
        circular = subreport_service.detect_circular_references()
        
        return jsonify({
            'success': True,
            'hasCircular': len(circular) > 0,
            'circularChains': circular
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
