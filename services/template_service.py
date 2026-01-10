"""
Jinja2 Template Rendering Service
"""
import os
import json
from datetime import datetime
from jinja2 import Environment, BaseLoader, TemplateError


class StringLoader(BaseLoader):
    """Custom Jinja2 loader for string templates"""
    
    def get_source(self, environment, template):
        return template, None, lambda: True


class TemplateService:
    """Service for rendering Jinja2 templates"""
    
    def __init__(self, templates_dir=None):
        self.env = Environment(
            loader=StringLoader(),
            autoescape=True
        )
        self.templates_dir = templates_dir
        self.queries_dir = os.path.join(templates_dir, 'queries') if templates_dir else None
        self._register_custom_filters()
        self._register_custom_globals()
        
        # Ensure queries directory exists
        if self.queries_dir:
            os.makedirs(self.queries_dir, exist_ok=True)
    
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
    
    def load_template_by_code(self, code: str) -> str:
        """
        Load a template from file by code (filename without .html extension)
        
        Args:
            code: Template code/filename without .html extension
            
        Returns:
            Template HTML content
            
        Raises:
            FileNotFoundError: If template file doesn't exist
            ValueError: If code is invalid
        """
        if not self.templates_dir:
            raise ValueError("Templates directory not configured")
        
        if not code or not isinstance(code, str):
            raise ValueError("Invalid template code")
        
        # Sanitize the code to prevent directory traversal
        code = code.strip()
        if '..' in code or '/' in code or '\\' in code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        template_path = os.path.join(self.templates_dir, f"{code}.html")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{code}' not found")
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise ValueError(f"Error reading template file: {str(e)}")
    
    def save_template(self, code: str, content: str) -> str:
        """
        Save a template file
        
        Args:
            code: Template code/filename without .html extension
            content: Template HTML content
            
        Returns:
            Path to saved template file
            
        Raises:
            ValueError: If code is invalid or content is empty
            IOError: If file cannot be written
        """
        if not self.templates_dir:
            raise ValueError("Templates directory not configured")
        
        if not code or not isinstance(code, str):
            raise ValueError("Invalid template code")
        
        # Sanitize the code
        code = code.strip()
        if '..' in code or '/' in code or '\\' in code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        if not content or not isinstance(content, str):
            raise ValueError("Template content is required")
        
        # Ensure templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)
        
        template_path = os.path.join(self.templates_dir, f"{code}.html")
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return template_path
        except IOError as e:
            raise ValueError(f"Error writing template file: {str(e)}")
    
    def list_templates(self) -> list:
        """
        List all available templates
        
        Returns:
            List of template codes (without .html extension)
        """
        if not self.templates_dir or not os.path.exists(self.templates_dir):
            return []
        
        templates = []
        try:
            for filename in os.listdir(self.templates_dir):
                if filename.endswith('.html'):
                    templates.append(filename[:-5])  # Remove .html extension
        except OSError:
            pass
        
        return sorted(templates)
    
    def delete_template(self, code: str) -> bool:
        """
        Delete a template file
        
        Args:
            code: Template code/filename without .html extension
            
        Returns:
            True if successful
            
        Raises:
            ValueError: If code is invalid
            FileNotFoundError: If template doesn't exist
        """
        if not self.templates_dir:
            raise ValueError("Templates directory not configured")
        
        if not code or not isinstance(code, str):
            raise ValueError("Invalid template code")
        
        # Sanitize the code
        code = code.strip()
        if '..' in code or '/' in code or '\\' in code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        template_path = os.path.join(self.templates_dir, f"{code}.html")
        
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{code}' not found")
        
        try:
            os.remove(template_path)
            return True
        except OSError as e:
            raise ValueError(f"Error deleting template file: {str(e)}")
    
    # ==========================================
    # Query Management Methods
    # ==========================================
    
    def save_query(self, code: str, sql: str, description: str = '') -> str:
        """
        Save a SQL query linked to a template
        
        Args:
            code: Template code (the query will be linked to this template)
            sql: SQL query string
            description: Optional description
            
        Returns:
            Path to saved query file
        """
        if not self.queries_dir:
            raise ValueError("Queries directory not configured")
        
        if not code or not isinstance(code, str):
            raise ValueError("Invalid template code")
        
        code = code.strip()
        if '..' in code or '/' in code or '\\' in code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        if not sql or not isinstance(sql, str):
            raise ValueError("SQL query is required")
        
        os.makedirs(self.queries_dir, exist_ok=True)
        
        query_data = {
            'code': code,
            'sql': sql.strip(),
            'description': description,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        query_path = os.path.join(self.queries_dir, f"{code}.json")
        
        try:
            with open(query_path, 'w', encoding='utf-8') as f:
                json.dump(query_data, f, ensure_ascii=False, indent=2)
            return query_path
        except IOError as e:
            raise ValueError(f"Error writing query file: {str(e)}")
    
    def save_template_query_link(self, template_code: str, query_code: str) -> str:
        """
        Save a link between a template and a query
        
        Args:
            template_code: Template code to link
            query_code: Query code to link to the template
            
        Returns:
            Path to saved link file
        """
        if not self.queries_dir:
            raise ValueError("Queries directory not configured")
        
        if not template_code or not isinstance(template_code, str):
            raise ValueError("Invalid template code")
        
        if not query_code or not isinstance(query_code, str):
            raise ValueError("Invalid query code")
        
        template_code = template_code.strip()
        query_code = query_code.strip()
        
        if '..' in template_code or '/' in template_code or '\\' in template_code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        if '..' in query_code or '/' in query_code or '\\' in query_code:
            raise ValueError("Invalid query code: path traversal not allowed")
        
        os.makedirs(self.queries_dir, exist_ok=True)
        
        link_data = {
            'template_code': template_code,
            'query_code': query_code,
            'created_at': datetime.now().isoformat()
        }
        
        # Save link file (template_code.link.json)
        link_path = os.path.join(self.queries_dir, f"{template_code}.link.json")
        
        try:
            with open(link_path, 'w', encoding='utf-8') as f:
                json.dump(link_data, f, ensure_ascii=False, indent=2)
            return link_path
        except IOError as e:
            raise ValueError(f"Error writing link file: {str(e)}")
    
    def get_template_query_link(self, template_code: str) -> str | None:
        """
        Get the linked query code for a template
        
        Args:
            template_code: Template code
            
        Returns:
            Query code or None if not linked
        """
        if not self.queries_dir:
            return None
        
        template_code = template_code.strip()
        link_path = os.path.join(self.queries_dir, f"{template_code}.link.json")
        
        if not os.path.exists(link_path):
            return None
        
        try:
            with open(link_path, 'r', encoding='utf-8') as f:
                link_data = json.load(f)
                return link_data.get('query_code')
        except (IOError, json.JSONDecodeError):
            return None

    def load_query(self, code: str) -> dict:
        """
        Load a SQL query by template code
        
        Args:
            code: Template code
            
        Returns:
            Dict with 'sql', 'description', etc.
        """
        if not self.queries_dir:
            raise ValueError("Queries directory not configured")
        
        if not code or not isinstance(code, str):
            raise ValueError("Invalid template code")
        
        code = code.strip()
        if '..' in code or '/' in code or '\\' in code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        # First, check for a link file to get the query code
        query_code = self.get_template_query_link(code)
        if query_code:
            # Load SQL from the linked query's .sql file
            sql_path = os.path.join(self.queries_dir, f"{query_code}.sql")
            if os.path.exists(sql_path):
                try:
                    with open(sql_path, 'r', encoding='utf-8') as f:
                        sql_content = f.read()
                    return {'sql': sql_content, 'code': query_code}
                except IOError as e:
                    raise ValueError(f"Error reading SQL file: {str(e)}")
        
        # Fallback: check for {code}.json (legacy format)
        query_path = os.path.join(self.queries_dir, f"{code}.json")
        if os.path.exists(query_path):
            try:
                with open(query_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                raise ValueError(f"Error reading query file: {str(e)}")
        
        # Also check for direct {code}.sql file
        sql_path = os.path.join(self.queries_dir, f"{code}.sql")
        if os.path.exists(sql_path):
            try:
                with open(sql_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                return {'sql': sql_content, 'code': code}
            except IOError as e:
                raise ValueError(f"Error reading SQL file: {str(e)}")
        
        return None  # No query linked
    
    def delete_query(self, code: str) -> bool:
        """
        Delete a SQL query
        
        Args:
            code: Template code
        """
        if not self.queries_dir:
            raise ValueError("Queries directory not configured")
        
        code = code.strip()
        if '..' in code or '/' in code or '\\' in code:
            raise ValueError("Invalid template code: path traversal not allowed")
        
        query_path = os.path.join(self.queries_dir, f"{code}.json")
        
        if not os.path.exists(query_path):
            raise FileNotFoundError(f"Query for '{code}' not found")
        
        try:
            os.remove(query_path)
            return True
        except OSError as e:
            raise ValueError(f"Error deleting query file: {str(e)}")
    
    def list_queries(self) -> list:
        """
        List all saved queries
        
        Returns:
            List of query codes with their SQL
        """
        if not self.queries_dir or not os.path.exists(self.queries_dir):
            return []
        
        queries = []
        try:
            for filename in os.listdir(self.queries_dir):
                if filename.endswith('.json'):
                    code = filename[:-5]
                    try:
                        query_data = self.load_query(code)
                        if query_data:
                            queries.append({
                                'code': code,
                                'sql': query_data.get('sql', ''),
                                'description': query_data.get('description', ''),
                                'has_template': os.path.exists(
                                    os.path.join(self.templates_dir, f"{code}.html")
                                )
                            })
                    except Exception:
                        pass
        except OSError:
            pass
        
        return sorted(queries, key=lambda x: x['code'])
    
    def get_template_with_query(self, code: str) -> dict:
        """
        Get both template and linked query
        
        Args:
            code: Template code
            
        Returns:
            Dict with 'template', 'query' (or None if no query linked)
        """
        template_html = self.load_template_by_code(code)
        query_data = self.load_query(code)
        
        return {
            'code': code,
            'template': template_html,
            'query': query_data
        }
