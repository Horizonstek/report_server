# Template Upload and Management Feature

## Overview
The PDF server now supports uploading and managing HTML templates that can be reused without needing to send the full template content with each request.

## New Endpoints

### 1. Upload Template
**Endpoint:** `POST /api/pdf/upload`

**Description:** Upload an HTML template file to the server

**Request:** multipart/form-data
```
- file: HTML template file (required)
- code: Template code/filename without .html (optional)
         If not provided, uses the original filename
```

**Response:**
```json
{
  "success": true,
  "code": "filename",
  "path": "/path/to/templates/filename.html",
  "message": "Template \"filename\" uploaded successfully"
}
```

**HTTP Status:** 201 Created
- 400: Bad Request (missing file, invalid code)
- 413: Payload Too Large (exceeds MAX_TEMPLATE_SIZE)
- 500: Server Error

**Example:**
```bash
curl -X POST http://localhost:5000/api/pdf/upload \
  -F "file=@template.html" \
  -F "code=invoice"
```

### 2. List Templates
**Endpoint:** `GET /api/pdf/templates`

**Description:** List all available templates

**Response:**
```json
{
  "success": true,
  "templates": ["invoice", "report", "receipt"],
  "count": 3
}
```

### 3. Delete Template
**Endpoint:** `DELETE /api/pdf/templates/<code>`

**Description:** Delete a template by code

**Parameters:**
- code: Template code (filename without .html)

**Response:**
```json
{
  "success": true,
  "message": "Template \"code\" deleted successfully"
}
```

**HTTP Status:** 
- 200: OK
- 404: Template not found
- 400: Invalid code
- 500: Server Error

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/pdf/templates/invoice
```

## Updated Endpoints

### Render Template
**Endpoint:** `POST /api/pdf/render`

Now supports two modes:

#### Option 1: Inline Template (Original)
```json
{
  "template": "<html>{{ variable }}</html>",
  "data": {"variable": "value"},
  "css": "optional css"
}
```

#### Option 2: Code-based Template (New)
```json
{
  "code": "invoice",
  "data": {"variable": "value"},
  "css": "optional css"
}
```

### Generate PDF
**Endpoint:** `POST /api/pdf/generate`

Now supports two modes:

#### Option 1: Inline Template (Original)
```json
{
  "template": "<html>{{ variable }}</html>",
  "data": {"variable": "value"},
  "css": "optional css",
  "options": {
    "page_size": "A4",
    "orientation": "portrait"
  }
}
```

#### Option 2: Code-based Template (New)
```json
{
  "code": "invoice",
  "data": {"variable": "value"},
  "css": "optional css",
  "options": {
    "page_size": "A4",
    "orientation": "portrait"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice",
    "data": {"invoice_number": "INV-001", "total": 100}
  }'
```

### Generate PDF File
**Endpoint:** `POST /api/pdf/generate-file`

Now supports two modes (same as `/generate`)

**Example:**
```bash
curl -X POST http://localhost:5000/api/pdf/generate-file \
  -H "Content-Type: application/json" \
  -d '{
    "code": "invoice",
    "data": {"invoice_number": "INV-001", "total": 100},
    "filename": "invoice-001.pdf"
  }' \
  --output invoice-001.pdf
```

## Usage Workflow

### 1. Upload a Template
```bash
curl -X POST http://localhost:5000/api/pdf/upload \
  -F "file=@my-template.html" \
  -F "code=my_template"
```

### 2. Render with Data
```bash
curl -X POST http://localhost:5000/api/pdf/render \
  -H "Content-Type: application/json" \
  -d '{
    "code": "my_template",
    "data": {"name": "John", "amount": 1000}
  }'
```

### 3. Generate PDF
```bash
curl -X POST http://localhost:5000/api/pdf/generate \
  -H "Content-Type: application/json" \
  -d '{
    "code": "my_template",
    "data": {"name": "John", "amount": 1000},
    "options": {"page_size": "A4"}
  }'
```

## Configuration

### Environment Variables
- `MAX_TEMPLATE_SIZE`: Maximum allowed template file size in bytes (default: 5MB)
- `TEMPLATES_DIR`: Directory path for storing templates (auto-configured)

### Directory Structure
```
pdf_server/
├── templates/
│   ├── invoice.html
│   ├── report.html
│   └── receipt.html
├── app.py
├── config.py
├── routes/
│   ├── pdf_routes.py
│   └── health_routes.py
└── services/
    ├── template_service.py
    └── pdf_service.py
```

## Security Considerations

1. **Path Traversal Prevention:** Template codes are sanitized to prevent directory traversal attacks (`..`, `/`, `\` are rejected)
2. **File Size Limit:** Templates have a configurable maximum size to prevent resource exhaustion
3. **File Encoding:** Only UTF-8 encoded files are accepted

## Error Handling

All endpoints return appropriate HTTP status codes:

| Status | Meaning |
|--------|---------|
| 200    | Success |
| 201    | Created (upload successful) |
| 400    | Bad Request (invalid parameters) |
| 404    | Not Found (template doesn't exist) |
| 413    | Payload Too Large (file exceeds size limit) |
| 500    | Server Error |

## Template Service Methods

The `TemplateService` class provides the following methods:

- `load_template_by_code(code: str) -> str`: Load template content by code
- `save_template(code: str, content: str) -> str`: Save a new template
- `list_templates() -> list`: List all template codes
- `delete_template(code: str) -> bool`: Delete a template
- `render_template(template_html: str, data: dict, css: str = '') -> str`: Render template with data
