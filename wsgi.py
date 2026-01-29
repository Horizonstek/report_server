"""
WSGI entry point for production deployment.
Supports both HTTP and HTTPS modes.

Usage with Waitress (Windows-compatible):
    python wsgi.py

Usage with Gunicorn (Linux/Docker):
    gunicorn --certfile=certs/cert.pem --keyfile=certs/key.pem --bind 0.0.0.0:443 wsgi:app
"""
from app import create_app
from config import get_config

app = create_app()


def run_with_waitress():
    """Run the app with Waitress WSGI server (supports Windows)."""
    from waitress import serve
    config = get_config()
    
    print(f"Starting WeasyPrint Report Server...")
    print(f"All routes under: https://{config.HOST}:{config.PORT}/weasyprint/")
    print(f"Health check: https://{config.HOST}:{config.PORT}/weasyprint/health")
    
    if config.USE_SSL and config.SSL_CERT_FILE and config.SSL_KEY_FILE:
        # Waitress doesn't support SSL directly, use a reverse proxy or Flask's dev server
        print("Note: Waitress doesn't support SSL directly.")
        print("For HTTPS, use a reverse proxy (nginx) or run with: python app.py")
        serve(app, host=config.HOST, port=config.PORT)
    else:
        serve(app, host=config.HOST, port=config.PORT)


if __name__ == '__main__':
    run_with_waitress()
