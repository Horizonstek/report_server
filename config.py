"""
Configuration settings for the PDF Server
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 443))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    
    # HTTPS/SSL Settings
    SSL_CERT_FILE = os.getenv('SSL_CERT_FILE', None)
    SSL_KEY_FILE = os.getenv('SSL_KEY_FILE', None)
    USE_SSL = os.getenv('USE_SSL', 'true').lower() == 'true'
    
    # PDF Settings
    DEFAULT_PAGE_SIZE = os.getenv('DEFAULT_PAGE_SIZE', 'A4')
    DEFAULT_ORIENTATION = os.getenv('DEFAULT_ORIENTATION', 'portrait')
    
    # Allowed origins for CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Templates directory
    TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')
    MAX_TEMPLATE_SIZE = int(os.getenv('MAX_TEMPLATE_SIZE', 5 * 1024 * 1024))  # 5MB
    
    # Oracle Database Settings
    ORACLE_USER = os.getenv('ORACLE_USER', '')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', '')
    ORACLE_DSN = os.getenv('ORACLE_DSN', '')  # Format: host:port/service_name or TNS name
    ORACLE_HOST = os.getenv('ORACLE_HOST', 'localhost')
    ORACLE_PORT = int(os.getenv('ORACLE_PORT', 1521))
    ORACLE_SERVICE_NAME = os.getenv('ORACLE_SERVICE_NAME', '')
    ORACLE_SID = os.getenv('ORACLE_SID', '')  # Alternative to service name
    
    # Connection pool settings
    ORACLE_POOL_MIN = int(os.getenv('ORACLE_POOL_MIN', 1))
    ORACLE_POOL_MAX = int(os.getenv('ORACLE_POOL_MAX', 5))
    ORACLE_POOL_INCREMENT = int(os.getenv('ORACLE_POOL_INCREMENT', 1))
    
    # Query timeout in seconds
    ORACLE_QUERY_TIMEOUT = int(os.getenv('ORACLE_QUERY_TIMEOUT', 30))
    
    # Enable/disable Oracle connectivity
    ORACLE_ENABLED = os.getenv('ORACLE_ENABLED', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
