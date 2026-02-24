"""
Report Routes - Jasper-compatible report endpoint
Mimics JasperReportsIntegration URL pattern for APEX compatibility
"""
import os
import logging
from flask import Blueprint, request, Response, jsonify

from services.project_service import ProjectService
from services.subreport_service import SubReportService
from services.pdf_service import PdfService
from services.database_service import get_datasource_manager, get_database_service
from config import get_config

logger = logging.getLogger(__name__)

report_bp = Blueprint('report', __name__)
config = get_config()

# Initialize services
projects_dir = os.path.join(config.TEMPLATES_DIR, '..', 'projects')
samples_dir = os.path.join(config.TEMPLATES_DIR, '..', 'samples')
project_service = ProjectService(projects_dir)
samples_service = ProjectService(samples_dir)
pdf_service = PdfService()
ds_manager = get_datasource_manager(config)
db_service_default = get_database_service(config)


# Reserved parameter names (not passed as SQL bind variables)
RESERVED_PARAMS = {
    '_repName', '_repFormat', '_dataSource', '_repLocale',
    '_outFilename', '_repTimeZone'
}


def _find_project(rep_name: str) -> tuple:
    """
    Find a project by report name.
    
    Searches: deployed projects first, then sample templates.
    
    Supports multiple naming patterns:
      - Flat: "DETAILED_SALES_REPORT" → project_id = "DETAILED_SALES_REPORT"
      - Path: "afaaq/DETAILED_SALES_REPORT/Main" → tries full path, then last segment
    
    Args:
        rep_name: Report name from _repName parameter
        
    Returns:
        Tuple of (project_dict, project_service_instance)
        
    Raises:
        FileNotFoundError: If project not found
    """
    # URL decode: %2F → /
    rep_name = rep_name.replace('%2F', '/').replace('%2f', '/')
    
    # Build list of name variants to try
    names_to_try = [rep_name]
    
    if '/' in rep_name:
        flat_name = rep_name.replace('/', '_')
        names_to_try.append(flat_name)
        
        segments = [s for s in rep_name.split('/') if s]
        if len(segments) >= 2:
            names_to_try.append(segments[-2])
        if segments:
            names_to_try.append(segments[-1])
    
    # Try each name against projects dir, then samples dir
    for svc in [project_service, samples_service]:
        for name in names_to_try:
            try:
                return svc.load_project(name), svc
            except (FileNotFoundError, ValueError):
                continue
    
    raise FileNotFoundError(f"Report '{rep_name}' not found")


def _extract_bind_params(args: dict) -> dict:
    """
    Extract SQL bind parameters from URL query args.
    
    Filters out reserved parameters (starting with _) and returns
    the rest as bind variables for SQL execution.
    
    Args:
        args: Request query parameters
        
    Returns:
        Dict of parameter name → value for SQL binding
    """
    params = {}
    for key, value in args.items():
        if key not in RESERVED_PARAMS and not key.startswith('_'):
            params[key] = value
    return params


def _get_db_service(datasource_name: str = None):
    """
    Get the appropriate database service.
    
    Priority:
    1. Named data source from data_sources.json (if _dataSource specified)
    2. Default data source from data_sources.json
    3. Legacy single-DB service from .env config
    
    Args:
        datasource_name: Optional data source name from _dataSource param
        
    Returns:
        DatabaseService instance or None
    """
    # Try named data source first
    if datasource_name:
        svc = ds_manager.get_service(datasource_name)
        if svc:
            return svc
        logger.warning(f"Data source '{datasource_name}' not found in data_sources.json")
    
    # Try default data source
    svc = ds_manager.get_service('default')
    if svc and svc.is_configured():
        return svc
    
    # Fall back to legacy .env config
    if db_service_default.is_available() and db_service_default.is_configured():
        return db_service_default
    
    return None


@report_bp.route('', methods=['GET'])
def render_report():
    """
    Jasper-compatible report endpoint.
    
    URL pattern (matches JasperReportsIntegration):
        GET /weasyprint/report?_repName=<name>&_repFormat=pdf&_dataSource=<ds>&P_PARAM1=val1&P_PARAM2=val2
    
    Parameters:
        _repName (required): Report/project name
        _repFormat (optional): Output format, only 'pdf' supported (default: pdf)
        _dataSource (optional): Named data source from data_sources.json
        _outFilename (optional): Download filename
        _repLocale (optional): Report locale (reserved for future use)
        P_* / any other: Passed as SQL bind variables
    
    Returns:
        PDF file (Content-Type: application/pdf)
    """
    args = request.args.to_dict()
    
    # --- Validate required params ---
    rep_name = args.get('_repName')
    if not rep_name:
        return jsonify({
            'error': 'Missing required parameter: _repName',
            'usage': '/weasyprint/report?_repName=<project_name>&P_PARAM1=value1'
        }), 400
    
    rep_format = args.get('_repFormat', 'pdf').lower()
    if rep_format != 'pdf':
        return jsonify({
            'error': f"Unsupported format: '{rep_format}'. Only 'pdf' is supported.",
        }), 400
    
    datasource_name = args.get('_dataSource')
    out_filename = args.get('_outFilename', f'{rep_name}.pdf')
    if not out_filename.endswith('.pdf'):
        out_filename += '.pdf'
    
    try:
        # --- Find the project ---
        project, proj_svc = _find_project(rep_name)
        project_config = project['config']
        
        # --- Extract SQL bind parameters ---
        bind_params = _extract_bind_params(args)
        
        # --- Get database service ---
        db_svc = _get_db_service(datasource_name)
        
        # --- Initialize sub-report service ---
        subreport_service = SubReportService(project['path'], project_config)
        
        # --- Execute main query ---
        main_data = {}
        main_query_path = project_config.get('mainQuery')
        if main_query_path and db_svc:
            try:
                sql = subreport_service.get_query_content(main_query_path)
                result = db_svc.execute_query_with_metadata(sql, bind_params)
                main_data = {
                    'rows': result['rows'],
                    'columns': result['columns'],
                    'row_count': result['row_count']
                }
            except Exception as e:
                logger.warning(f"Main query execution failed: {e}")
        
        # --- Execute sub-report queries ---
        subreport_data = {}
        for sr in project_config.get('subReports', []):
            sr_id = sr.get('id')
            sr_query = sr.get('query')
            if sr_id and sr_query and db_svc:
                try:
                    sql = subreport_service.get_query_content(sr_query)
                    result = db_svc.execute_query_with_metadata(sql, bind_params)
                    subreport_data[sr_id] = {
                        'rows': result['rows'],
                        'columns': result['columns'],
                        'row_count': result['row_count']
                    }
                except Exception as e:
                    logger.warning(f"Sub-report '{sr_id}' query failed: {e}")
                    subreport_data[sr_id] = {}
        
        # Add bind params as template variables too (for direct use in templates)
        main_data.update(bind_params)
        
        # --- Compose the full report ---
        rendered_html = subreport_service.compose_report(main_data, subreport_data)
        
        # --- Generate PDF ---
        page_size = project_config.get('settings', {}).get('pageSize', 'A4')
        orientation = project_config.get('settings', {}).get('orientation', 'portrait')
        
        pdf_bytes = pdf_service.generate_pdf(
            html=rendered_html,
            page_size=page_size,
            orientation=orientation,
            base_url=proj_svc.get_project_base_url(project['id'])
        )
        
        # --- Return PDF directly (like Jasper) ---
        return Response(
            pdf_bytes,
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{out_filename}"',
                'Content-Length': str(len(pdf_bytes)),
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            }
        )
        
    except FileNotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ConnectionError as e:
        return jsonify({
            'error': f'Database connection failed: {str(e)}',
            'hint': 'Check data_sources.json configuration'
        }), 503
    except Exception as e:
        logger.exception(f"Report generation failed for '{rep_name}'")
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500


@report_bp.route('/test', methods=['GET'])
def test_report_endpoint():
    """
    Test endpoint to verify report service is running.
    Also shows available projects and data sources.
    """
    try:
        projects = project_service.list_projects()
        project_names = [p.get('name', p.get('id', '')) for p in projects]
        
        samples = samples_service.list_projects()
        sample_names = [p.get('name', p.get('id', '')) for p in samples]
        
        ds_names = ds_manager.get_source_names()
        
        return jsonify({
            'status': 'ok',
            'message': 'WeasyPrint Report Service is running',
            'available_reports': project_names,
            'sample_reports': sample_names,
            'data_sources': ds_names,
            'usage': {
                'url': '/weasyprint/report?_repName=<name>&P_PARAM=value',
                'parameters': {
                    '_repName': 'Report/project name (required)',
                    '_repFormat': 'Output format: pdf (default)',
                    '_dataSource': 'Named data source from data_sources.json',
                    '_outFilename': 'Download filename',
                    'P_*': 'SQL bind parameters'
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
