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
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(pdf_bp, url_prefix='/api/pdf')
    app.register_blueprint(query_bp, url_prefix='/api/queries')
    
    return app


if __name__ == '__main__':
    config = get_config()
    app = create_app()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
