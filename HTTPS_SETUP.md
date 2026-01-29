# HTTPS Configuration Guide

## Overview
The WeasyPrint Report Server now supports HTTPS and all APIs are routed under `/weasyprint/`.

## New Route Structure
All endpoints are now accessible under the `/weasyprint/` base path:

- **Health Check**: `https://{IP}/weasyprint/health` or `https://{IP}/weasyprint/`
- **PDF Generation**: `https://{IP}/weasyprint/api/pdf/*`
- **Query API**: `https://{IP}/weasyprint/api/queries/*`

## Enabling HTTPS

### 1. Prepare SSL Certificates
You need SSL certificate and key files. You can:
- Use certificates from a Certificate Authority (CA)
- Generate self-signed certificates:
  ```bash
  openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
  ```

### 2. Update Environment Variables
Set the following in your `.env` file:
```
USE_SSL=true
SSL_CERT_FILE=/path/to/cert.pem
SSL_KEY_FILE=/path/to/key.pem
PORT=443
HOST=0.0.0.0
```

### 3. Configuration Options
- `USE_SSL`: Set to `true` to enable HTTPS (default: `true`)
- `SSL_CERT_FILE`: Path to SSL certificate file
- `SSL_KEY_FILE`: Path to SSL private key file
- `PORT`: Server port (default: 443 for HTTPS)
- `HOST`: Server host (default: `127.0.0.1`)

### 4. Running the Server

**Development (with HTTPS):**
```bash
python app.py
```

**Production (with Gunicorn + HTTPS):**
```bash
gunicorn --certfile=cert.pem --keyfile=key.pem --bind 0.0.0.0:443 wsgi:app
```

**Docker:**
Update your Docker configuration to mount certificates and set environment variables.

## Testing HTTPS Connection

```bash
# Using curl (ignoring self-signed cert warnings)
curl -k https://localhost/weasyprint/health

# Using Python
import requests
requests.get('https://localhost/weasyprint/health', verify=False)
```

## Reverting to HTTP (Development Only)
If you need HTTP for development:
```
USE_SSL=false
PORT=5000
```

## Troubleshooting

### Certificate Not Found
- Ensure `SSL_CERT_FILE` and `SSL_KEY_FILE` point to valid certificate files
- Check file permissions (should be readable by the application user)

### Port 443 Permission Denied
- On Linux, you may need elevated privileges to bind to port 443
- Use a higher port (e.g., 8443) with `PORT=8443`

### Certificate Verification Errors
- If using self-signed certificates, use `-k` flag with curl or `verify=False` with Python requests
