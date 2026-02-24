# WeasyPrint PDF Report Server

A Flask-based PDF generation server built on top of WeasyPrint and Jinja2. This server powers the **Oracle Report Studio** extension and acts as a direct replacement for **JasperReportsIntegration** in Oracle APEX applications.

## Features

- **Dynamic Data Binding:** Connects directly to Oracle Databases to fetch data before rendering.
- **Jinja2 Templating:** Write reports using standard HTML, CSS, and Jinja2 loops (`{% for row in rows %}`).
- **Sub-reports:** Modularize reports (headers, footers, charts) using the `{{ subreports.name }}` syntax.
- **Jasper-Compatible API:** Drop-in replacement for JasperReportsIntegration (`GET /weasyprint/report`).
- **Multi-Datasource Support:** Define multiple named Oracle connection pools (e.g., `afaaq_100`).

---

## Configuration

There are two primary configuration files:

1. **`.env`** (Environment Variables)
   - Handles server fundamentals (Port, Host, SSL certificates, CORS).
   - Also configures the _default_ fallback database connection if a named data source isn't requested.
   - Copy `.env.example` to `.env` to start.

2. **`data_sources.json`** (Oracle Connections)
   - Stores your named data sources used by the Jasper-compatible endpoint.
   - Example format:
   ```json
   {
     "default": {
       "user": "hr",
       "password": "hr",
       "dsn": "localhost:1521/XEPDB1"
     },
     "afaaq_100": {
       "user": "afaaq",
       "password": "pwd",
       "host": "10.0.0.5",
       "port": 1521,
       "service_name": "PROD"
     }
   }
   ```

---

## Integration with Oracle APEX

The server exposes a special endpoint designed to mimic JasperReportsIntegration.

### API Endpoint

`GET /weasyprint/report`

### Parameters

| Parameter     | Description                                                                                                                              | Example                                     |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `_repName`    | **Required.** The deployed project name or sample template.                                                                              | `invoice` or `afaaq/SALES_REPORT/Main`      |
| `_repFormat`  | Output format.                                                                                                                           | `pdf` (currently the only supported format) |
| `_dataSource` | Which connection pool to use. Defined in `data_sources.json`.                                                                            | `afaaq_100`                                 |
| `P_*`         | **Dynamic Bind Variables.** Any parameter starting with `P_` (or anything else) is passed directly to the SQL queries as bind variables. | `&P_COMPANY_NO=1`                           |

### APEX JavaScript Helper

Add this to your APEX Global JavaScript to seamlessly transition from Jasper:

```javascript
var afaaq = afaaq || {};
afaaq.util = afaaq.util || {};

afaaq.util.generateWPrptUrl = function (options) {
  var wsUrl = "https://horizonstek.net/weasyprint/report?"; // Update to your production server URL
  var rptName = "_repName=" + options.reportName;
  var rptFormat = "&_repFormat=" + (options.reportFormat || "pdf");
  var dataSource = options.dataSource
    ? "&_dataSource=" + options.dataSource
    : "";
  var params = options.prms || "";

  return wsUrl + rptName + rptFormat + dataSource + params;
};

// Example APEX Call:
// var url = afaaq.util.generateWPrptUrl({
//     reportName: "invoice",
//     dataSource: "afaaq_100",
//     prms: "&P_COMPANY_NO=" + $v("P430_COMPANY_NO")
// });
// window.open(url, "_blank");
```

---

## Moving to Production

Do NOT use the built-in Flask development server (`flask run`) or bare `waitress-serve` in a production environment without proper process management.

### Option 1: Docker (Recommended)

The project includes a production-ready `Dockerfile` and `docker-compose.yml`. The Docker container uses `gunicorn` with multiple worker processes.

1. Ensure your `.env` file is properly configured.
2. Put your SSL certificates in the `certs/` folder (`cert.pem`, `key.pem`) if using HTTPS directly.
3. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```

### Option 2: Windows Service (NSSM)

If you must run this natively on Windows Server instead of Docker:

1. Create a Python Virtual Environment:
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Download [NSSM (Non-Sucking Service Manager)](https://nssm.cc/).
3. Install the server as a background Windows Service using Waitress:
   ```cmd
   nssm install WeasyPrintServer
   ```
4. In the NSSM GUI that opens:
   - **Path:** `C:\path\to\your\venv\Scripts\python.exe`
   - **Arguments:** `-m waitress --host=0.0.0.0 --port=5000 wsgi:app`
   - **Directory:** `c:\Users\Abdulrahman\Desktop\programming\production_v0\report_studio\report_server`
5. Start the service:
   ```cmd
   nssm start WeasyPrintServer
   ```
   _(Note: You will likely want to place this behind an IIS Reverse Proxy or Nginx for SSL termination on Windows)._

### Option 3: PM2 (Node.js Process Manager)

If you already use PM2 on your server for Node apps, you can use it to manage the Python Waitress process:

```bash
npm install -g pm2
pm2 start "waitress-serve --host=0.0.0.0 --port=5000 wsgi:app" --name weasyprint-server
pm2 save
pm2 startup
```

---

## Testing the Server

You can verify the Jasper endpoint and check which reports and data sources are loaded by accessing:

```
GET /weasyprint/report/test
```
