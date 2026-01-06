# Oracle Report Studio - PDF Server

A Python Flask server for PDF generation using WeasyPrint and Jinja2 templating, with Oracle database integration for dynamic report generation.

## Features

- **Jinja2 Templates**: Full Jinja2 templating support with custom filters
- **WeasyPrint PDF**: High-quality PDF generation from HTML/CSS
- **Oracle Database Integration**: Execute SQL queries and populate templates with live data
- **REST API**: Simple REST API for integration with VS Code extension
- **Custom Filters**: Built-in filters for number, currency, date, and percentage formatting
- **Connection Pooling**: Efficient Oracle connection management

## Requirements

- Python 3.9+
- WeasyPrint dependencies (see [WeasyPrint installation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation))
- Oracle Database (optional, for database-driven reports)

## Installation

### 1. Install WeasyPrint System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-pip python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**macOS:**
```bash
brew install pango libffi
```

**Windows:**
See [WeasyPrint Windows installation](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows)

### 2. Create Virtual Environment

```bash
cd pdf_server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env as needed
```

#### Basic Configuration

```env
HOST=127.0.0.1
PORT=5000
DEBUG=true
```

#### Oracle Database Configuration (Optional)

To enable Oracle database connectivity, add these settings to your `.env` file:

```env
# Enable Oracle
ORACLE_ENABLED=true

# Credentials
ORACLE_USER=your_username
ORACLE_PASSWORD=your_password

# Connection (use ONE of these methods):

# Method 1: DSN string
ORACLE_DSN=hostname:1521/service_name

# Method 2: Individual settings
ORACLE_HOST=localhost
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=ORCLPDB1
# Or use SID instead:
# ORACLE_SID=ORCL

# Connection pool settings
ORACLE_POOL_MIN=1
ORACLE_POOL_MAX=5
ORACLE_POOL_INCREMENT=1
ORACLE_QUERY_TIMEOUT=30
```

### 5. Run the Server

```bash
python app.py

or

gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 'app:create_app()'
```

The server will start on http://127.0.0.1:5000

## API Endpoints

### Health Check

```
GET /health
```

Returns server status, WeasyPrint availability, and Oracle connection status.

**Response:**
```json
{
    "status": "ok",
    "weasyprint_available": true,
    "oracle": {
        "driver_available": true,
        "enabled": true,
        "configured": true,
        "connected": true,
        "message": "Connection successful"
    },
    "version": "1.1.0"
}
```

### Render Template (HTML)

```
POST /api/pdf/render
Content-Type: application/json

{
    "template": "<html><body>Hello {{ name }}</body></html>",
    "data": {
        "name": "World",
        "rows": [...]
    },
    "css": "body { font-family: sans-serif; }"
}
```

### Generate PDF (Base64)

```
POST /api/pdf/generate
Content-Type: application/json

{
    "template": "<html><body>{{ content }}</body></html>",
    "data": { "content": "PDF Content" },
    "options": {
        "page_size": "A4",
        "orientation": "portrait"
    }
}
```

### Generate PDF (File Download)

```
POST /api/pdf/generate-file
Content-Type: application/json

{
    "template": "...",
    "data": {...},
    "filename": "report.pdf"
}
```

### Preview HTML

```
POST /api/pdf/preview
Content-Type: application/json

{
    "template": "...",
    "data": {...}
}
```

## Oracle Database Endpoints

These endpoints fetch data from Oracle and generate reports dynamically.

### Check Database Status

```
GET /api/pdf/db/status
```

Returns Oracle connection status and configuration.

### Test Query

```
POST /api/pdf/db/test-query
Content-Type: application/json

{
    "sql": "SELECT * FROM employees WHERE department_id = :dept_id",
    "params": {"dept_id": 10}
}
```

### Generate PDF from Database

```
POST /api/pdf/db/generate
Content-Type: application/json

{
    "code": "employee_report",
    "sql": "SELECT * FROM employees WHERE department_id = :dept_id",
    "params": {"dept_id": 10},
    "extra_data": {"report_title": "Department Report"},
    "options": {
        "page_size": "A4",
        "orientation": "landscape"
    }
}
```

If `sql` is omitted, the server uses the linked query saved with the template.

**Response:**
```json
{
    "success": true,
    "pdf": "base64_encoded_pdf_content",
    "size": 12345,
    "rows_processed": 25
}
```

### Generate PDF File from Database

```
POST /api/pdf/db/generate-file
Content-Type: application/json

{
    "code": "employee_report",
    "params": {"dept_id": 10},
    "filename": "department_report.pdf"
}
```

Returns the PDF as a binary file download.

### Preview HTML from Database

```
POST /api/pdf/db/preview
Content-Type: application/json

{
    "code": "employee_report",
    "params": {"dept_id": 10}
}
```

Returns rendered HTML for browser preview.

### Get Query Parameters

```
GET /api/pdf/db/query-params/{template_code}
```

Returns the list of parameters required by a template's linked query.

**Response:**
```json
{
    "success": true,
    "code": "employee_report",
    "parameters": ["dept_id", "start_date", "end_date"],
    "sql": "SELECT * FROM employees WHERE department_id = :dept_id..."
}
```

## Jinja2 Template Syntax

### Variables

```html
<p>Hello {{ name }}</p>
<p>Total: {{ amount | currency }}</p>
```

### Loops

```html
{% for item in rows %}
<tr>
    <td>{{ item.name }}</td>
    <td>{{ item.price | currency }}</td>
</tr>
{% endfor %}
```

### Conditionals

```html
{% if total > 1000 %}
<p class="large-order">Large Order!</p>
{% endif %}
```

### Built-in Variables

- `{{ REPORT_DATE }}` - Current date (YYYY-MM-DD)
- `{{ REPORT_TIME }}` - Current time (HH:MM:SS)
- `{{ REPORT_DATETIME }}` - Current datetime
- `{{ TOTAL_RECORDS }}` - Number of rows
- `{{ row_count }}` - Alias for TOTAL_RECORDS

### Custom Filters

- `{{ value | number_format(2) }}` - Format number with decimals
- `{{ value | currency('$', 2) }}` - Format as currency
- `{{ value | date_format('%Y-%m-%d') }}` - Format date
- `{{ value | percentage(1) }}` - Format as percentage
- `{{ value | default_if_none('N/A') }}` - Default for None values

## Example Template

```html
<!DOCTYPE html>
<html>
<head>
    <title>Invoice</title>
    <style>
        body { font-family: Arial, sans-serif; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; }
    </style>
</head>
<body>
    <h1>Invoice #{{ invoice_number }}</h1>
    <p>Date: {{ REPORT_DATE }}</p>
    
    <table>
        <thead>
            <tr>
                <th>Item</th>
                <th>Quantity</th>
                <th>Price</th>
                <th>Total</th>
            </tr>
        </thead>
        <tbody>
            {% for item in rows %}
            <tr>
                <td>{{ item.name }}</td>
                <td>{{ item.quantity }}</td>
                <td>{{ item.price | currency }}</td>
                <td>{{ item.total | currency }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    
    <p><strong>Total: {{ grand_total | currency }}</strong></p>
</body>
</html>
```

## Production Deployment

### Option 1: Gunicorn (Recommended for Linux/macOS)

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with 4 worker processes
gunicorn -w 4 -b 0.0.0.0:5000 'app:create_app()'

# With timeout and logging
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 --access-logfile - --error-logfile - 'app:create_app()'
```

### Option 2: Gunicorn with Systemd Service

Create a systemd service file at `/etc/systemd/system/pdf-server.service`:

```ini
[Unit]
Description=Oracle Report Studio PDF Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/report_server
Environment="PATH=/path/to/report_server/venv/bin"
EnvironmentFile=/path/to/report_server/.env
ExecStart=/path/to/report_server/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 'app:create_app()'
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pdf-server
sudo systemctl start pdf-server
sudo systemctl status pdf-server
```

### Option 3: Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install WeasyPrint dependencies
RUN apt-get update && apt-get install -y \
    python3-pip python3-cffi python3-brotli \
    libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 libffi-dev shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV HOST=0.0.0.0
ENV PORT=5000

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "app:create_app()"]
```

Build and run:

```bash
docker build -t pdf-server .
docker run -d -p 5000:5000 --env-file .env --name pdf-server pdf-server
```

### Option 4: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  pdf-server:
    build: .
    ports:
      - "5000:5000"
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
      - ORACLE_ENABLED=true
    volumes:
      - ./templates:/app/templates
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:

```bash
docker-compose up -d
```

### Nginx Reverse Proxy (Recommended)

For production, put Nginx in front of Gunicorn:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for PDF generation
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
        
        # Increase max body size for template uploads
        client_max_body_size 10M;
    }
}
```

### Production Environment Variables

```env
# Production settings
FLASK_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=5000

# Security - restrict CORS in production
CORS_ORIGINS=https://your-domain.com

# Oracle Database
ORACLE_ENABLED=true
ORACLE_USER=prod_user
ORACLE_PASSWORD=secure_password
ORACLE_DSN=oracle-host:1521/PROD_SERVICE
ORACLE_POOL_MIN=2
ORACLE_POOL_MAX=10
ORACLE_QUERY_TIMEOUT=60
```

### Production Checklist

- [ ] Set `DEBUG=false` and `FLASK_ENV=production`
- [ ] Use strong Oracle credentials
- [ ] Configure CORS to allow only your domain
- [ ] Set up SSL/TLS (via Nginx or load balancer)
- [ ] Configure appropriate timeouts
- [ ] Set up log rotation
- [ ] Configure monitoring/health checks
- [ ] Use connection pooling for Oracle
- [ ] Set up firewall rules

## License

MIT
