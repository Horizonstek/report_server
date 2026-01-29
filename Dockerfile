FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies for WeasyPrint and Oracle client
RUN apt-get update && apt-get install -y --no-install-recommends \
    # WeasyPrint dependencies
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    libcairo2 \
    libgirepository-1.0-1 \
    gir1.2-pango-1.0 \
    fonts-liberation \
    fonts-dejavu-core \
    # Oracle Instant Client dependencies (optional)
    libaio1t64 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import ssl; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; urllib.request.urlopen('https://localhost:443/weasyprint/health', context=ctx)" || exit 1

# Run the application with gunicorn and HTTPS
CMD ["gunicorn", "app:create_app()", "--bind", "0.0.0.0:443", "--workers", "4", "--timeout", "120", "--certfile", "/app/certs/cert.pem", "--keyfile", "/app/certs/key.pem"]
