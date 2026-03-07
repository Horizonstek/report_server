"""
Jinja2 Template Rendering Service
"""
from datetime import datetime
from jinja2 import Environment, BaseLoader, TemplateError


class StringLoader(BaseLoader):
    """Custom Jinja2 loader for string templates"""
    
    def get_source(self, environment, template):
        return template, None, lambda: True


class TemplateService:
    """Service for rendering Jinja2 templates"""
    
    def __init__(self):
        self.env = Environment(
            loader=StringLoader(),
            autoescape=True
        )
        self._register_custom_filters()
        self._register_custom_globals()
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters"""
        
        # Number formatting
        self.env.filters['number_format'] = lambda value, decimals=2: (
            f"{float(value):,.{decimals}f}" if value is not None else ''
        )
        
        # Currency formatting
        self.env.filters['currency'] = lambda value, symbol='$', decimals=2: (
            f"{symbol}{float(value):,.{decimals}f}" if value is not None else ''
        )
        
        # Date formatting
        self.env.filters['date_format'] = self._format_date
        
        # Percentage formatting
        self.env.filters['percentage'] = lambda value, decimals=1: (
            f"{float(value):.{decimals}f}%" if value is not None else ''
        )
        
        # Safe default for None values
        self.env.filters['default_if_none'] = lambda value, default='': (
            default if value is None else value
        )
        
        # QR Code filter (generates QR code image from base64 data)
        self.env.filters['qrcode'] = self._generate_qrcode
    
    def _register_custom_globals(self):
        """Register global variables and functions"""
        self.env.globals['now'] = datetime.now
        self.env.globals['today'] = datetime.today
    
    def _format_date(self, value, format_str='%Y-%m-%d'):
        """Format a date value"""
        if value is None:
            return ''
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.strftime(format_str)
        return str(value)
    
    def _generate_qrcode(self, data, size=150) -> str:
        """
        Generate a QR code image from data and return as a base64 data URI.
        
        Args:
            data: The data to encode in the QR code (base64 string or plain text)
            size: Size of the QR code image in pixels (default: 150)
            
        Returns:
            Data URI string (data:image/png;base64,...) for use in <img src>
        """
        import base64
        import io
        
        if data is None or str(data).strip() == '':
            return ''
        
        try:
            import qrcode
            from qrcode.constants import ERROR_CORRECT_L
            
            qr = qrcode.QRCode(
                version=None,
                error_correction=ERROR_CORRECT_L,
                box_size=10,
                border=1,
            )
            qr.add_data(str(data))
            qr.make(fit=True)
            
            img = qr.make_image(fill_color='black', back_color='white')
            
            # Convert to base64 data URI
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            b64 = base64.b64encode(buffer.getvalue()).decode('ascii')
            return f"data:image/png;base64,{b64}"
            
        except ImportError:
            return ''
        except Exception:
            return ''
    
    def render_template(
        self,
        template_html: str,
        data: dict,
        css: str = ''
    ) -> str:
        """
        Render a Jinja2 template with the provided data
        
        Args:
            template_html: The HTML template string with Jinja2 syntax
            data: Dictionary containing template variables
            css: Optional CSS to inject
            
        Returns:
            Rendered HTML string
        """
        try:
            # Add built-in variables
            template_data = {
                **data,
                'REPORT_DATE': datetime.now().strftime('%Y-%m-%d'),
                'REPORT_TIME': datetime.now().strftime('%H:%M:%S'),
                'REPORT_DATETIME': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Add row count if rows are provided
            if 'rows' in data and isinstance(data['rows'], list):
                template_data['TOTAL_RECORDS'] = len(data['rows'])
                template_data['row_count'] = len(data['rows'])
                # Add column names for dynamic table support (SELECT *)
                if len(data['rows']) > 0:
                    template_data['_columns'] = list(data['rows'][0].keys())
            
            # Compile and render the template
            template = self.env.from_string(template_html)
            rendered_html = template.render(**template_data)
            
            # Inject CSS if provided
            if css:
                rendered_html = self._inject_css(rendered_html, css)
            
            return rendered_html
            
        except TemplateError as e:
            raise ValueError(f"Template rendering error: {str(e)}")
    
    def _inject_css(self, html: str, css: str) -> str:
        """Inject CSS into HTML document"""
        style_tag = f"<style>{css}</style>"
        
        if '</head>' in html:
            return html.replace('</head>', f'{style_tag}</head>')
        elif '<head>' in html:
            return html.replace('<head>', f'<head>{style_tag}')
        elif '<html>' in html:
            return html.replace('<html>', f'<html><head>{style_tag}</head>')
        else:
            return f'{style_tag}{html}'
    
    def validate_template(self, template_html: str) -> dict:
        """
        Validate a Jinja2 template syntax
        
        Returns:
            Dict with 'valid' boolean and 'error' message if invalid
        """
        try:
            self.env.from_string(template_html)
            return {'valid': True, 'error': None}
        except TemplateError as e:
            return {'valid': False, 'error': str(e)}
