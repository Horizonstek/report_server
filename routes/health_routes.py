"""
Health check routes
"""
from flask import Blueprint, jsonify
from services.pdf_service import PdfService
from services.database_service import get_database_service
from config import get_config

health_bp = Blueprint('health', __name__)
config = get_config()
db_service = get_database_service(config)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """Check if the server is running and all services are available"""
    pdf_service = PdfService()
    weasyprint_available = pdf_service.check_weasyprint()
    
    # Oracle database status
    oracle_status = {
        'driver_available': db_service.is_available(),
        'enabled': db_service.is_enabled(),
        'configured': db_service.is_configured(),
        'connected': False
    }
    
    if oracle_status['driver_available'] and oracle_status['configured']:
        success, message = db_service.test_connection()
        oracle_status['connected'] = success
        oracle_status['message'] = message
    
    return jsonify({
        'status': 'ok',
        'weasyprint_available': weasyprint_available,
        'oracle': oracle_status,
        'version': '1.1.0'
    })


@health_bp.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'name': 'Oracle Report Studio PDF Server',
        'version': '1.1.0',
        'endpoints': {
            'health': '/health',
            'render_html': '/api/pdf/render',
            'generate_pdf': '/api/pdf/generate',
            'preview': '/api/pdf/preview',
            'db_status': '/api/pdf/db/status',
            'db_generate': '/api/pdf/db/generate',
            'db_preview': '/api/pdf/db/preview'
        }
    })
