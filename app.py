"""
PDF Server - Flask application for PDF generation with WeasyPrint and Jinja2
"""
from flask import Flask
from flask_cors import CORS

from config import get_config
from routes.pdf_routes import pdf_bp
from routes.query_routes import query_bp
from routes.health_routes import health_bp


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    config = get_config()
    
    # Configure CORS
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Register blueprints under /weasyprint/ prefix
    app.register_blueprint(health_bp, url_prefix='/weasyprint')
    app.register_blueprint(pdf_bp, url_prefix='/weasyprint/api/pdf')
    app.register_blueprint(query_bp, url_prefix='/weasyprint/api/queries')
    
    return app


if __name__ == '__main__':
    import ssl
    config = get_config()
    app = create_app()
    
    # Configure SSL/HTTPS if certificates are provided
    ssl_context = None
    if config.USE_SSL and config.SSL_CERT_FILE and config.SSL_KEY_FILE:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(config.SSL_CERT_FILE, config.SSL_KEY_FILE)
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        ssl_context=ssl_context
    )
