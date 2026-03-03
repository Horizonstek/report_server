"""
Sub-Report Service - Handles sub-report rendering and composition
"""
import os
import re
from typing import Dict, Any, List, Optional, Set
from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateError, ChainableUndefined
from markupsafe import Markup


class SilentUndefined(ChainableUndefined):
    """Custom Undefined that silently handles all operations (comparisons, arithmetic, etc.)
    This mimics Jasper's tolerant null handling where missing fields don't cause errors."""
    def __str__(self): return ''
    def __html__(self): return ''
    def __bool__(self): return False
    def __int__(self): return 0
    def __float__(self): return 0.0
    def __gt__(self, other): return False
    def __lt__(self, other): return False
    def __ge__(self, other): return False
    def __le__(self, other): return False
    def __eq__(self, other): return other is None or isinstance(other, SilentUndefined)
    def __ne__(self, other): return not self.__eq__(other)
    def __add__(self, other): return other
    def __radd__(self, other): return other
    def __sub__(self, other): return 0
    def __rsub__(self, other): return other
    def __mul__(self, other): return 0
    def __rmul__(self, other): return 0
    def __iter__(self): return iter([])
    def __len__(self): return 0


class CaseInsensitiveSubreports:
    def __init__(self, data):
        self._data = {k.lower(): v for k, v in data.items()}
    def __getattr__(self, name):
        return self._data.get(name.lower(), '')
    def __getitem__(self, name):
        return self._data.get(name.lower(), '')
    def get(self, name, default=''):
        return self._data.get(name.lower(), default)
    def __contains__(self, name):
        return name.lower() in self._data

class SubReportService:
    """Service for rendering and composing sub-reports within a project"""
    
    # Maximum nesting depth to prevent infinite recursion
    MAX_NESTING_DEPTH = 3
    
    def __init__(self, project_path: str, project_config: Dict[str, Any]):
        """
        Initialize the sub-report service for a specific project
        
        Args:
            project_path: Absolute path to the project directory
            project_config: Project configuration dict
        """
        self.project_path = project_path
        self.config = project_config
        self.templates_dir = os.path.join(project_path, 'templates')
        
        # Create Jinja2 environment with project template loader
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True,
            undefined=SilentUndefined
        )
        
        # Register custom filters and globals
        self._register_custom_filters()
        self._register_custom_globals()
        
        # Cache for rendered sub-reports
        self._render_cache: Dict[str, str] = {}
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters"""
        from datetime import datetime
        
        # Number formatting
        self.env.filters['number_format'] = lambda value, decimals=2: (
            f"{float(value):,.{decimals}f}" if value is not None and str(value).strip() != '' else ''
        )
        
        # Currency formatting
        self.env.filters['currency'] = lambda value, symbol='$', decimals=2: (
            f"{symbol}{float(value):,.{decimals}f}" if value is not None and str(value).strip() != '' else ''
        )
        
        # Date formatting - register as both 'date_format' and 'date' (templates use | date(...))
        self.env.filters['date_format'] = self._format_date
        self.env.filters['date'] = self._format_date
        
        # Percentage formatting
        self.env.filters['percentage'] = lambda value, decimals=1: (
            f"{float(value):.{decimals}f}%" if value is not None and str(value).strip() != '' else ''
        )
        
        # Safe default for None values
        self.env.filters['default_if_none'] = lambda value, default='': (
            default if value is None else value
        )
        
        # Asset URL filter (so templates can use {{ value | asset_url }})
        self.env.filters['asset_url'] = self._asset_url
    
    def _register_custom_globals(self):
        """Register global variables and functions"""
        from datetime import datetime
        
        self.env.globals['now'] = datetime.now
        self.env.globals['today'] = datetime.today
        
        # Asset URL helper
        self.env.globals['asset_url'] = self._asset_url
    
    def _format_date(self, value, format_str='%Y-%m-%d'):
        """Format a date value. Supports both Python strftime and Jasper/moment-style formats."""
        from datetime import datetime
        
        if value is None or str(value).strip() == '':
            return ''
        
        # Convert Jasper/moment-style format to Python strftime
        # e.g. 'YYYY-MM-DD' -> '%Y-%m-%d', 'YYYY-MM' -> '%Y-%m'
        if 'YYYY' in format_str or 'MM' in format_str or 'DD' in format_str:
            format_str = (format_str
                .replace('YYYY', '%Y')
                .replace('YY', '%y')
                .replace('MM', '%m')
                .replace('DD', '%d')
                .replace('HH', '%H')
                .replace('mm', '%M')
                .replace('ss', '%S')
            )
        
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        if isinstance(value, datetime):
            return value.strftime(format_str)
        return str(value)
    
    def _asset_url(self, relative_path) -> str:
        """
        Convert a relative asset path to an absolute file URL,
        or convert raw binary image data (BLOB) to a base64 data URI.
        
        Args:
            relative_path: Path relative to project assets folder, or raw image bytes from DB
            
        Returns:
            Absolute file URL for the asset, or a base64 data URI
        """
        import base64
        
        # If the value is raw binary image data (BLOB from DB), return a data URI
        if isinstance(relative_path, (bytes, bytearray)):
            mime_type = 'application/octet-stream'
            if relative_path[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = 'image/png'
            elif relative_path[:2] == b'\xff\xd8':
                mime_type = 'image/jpeg'
            elif relative_path[:6] in (b'GIF87a', b'GIF89a'):
                mime_type = 'image/gif'
            elif relative_path[:4] == b'RIFF' and relative_path[8:12] == b'WEBP':
                mime_type = 'image/webp'
            
            b64 = base64.b64encode(relative_path).decode('ascii')
            return f"data:{mime_type};base64,{b64}"
        
        relative_path = str(relative_path)
        
        # Handle paths with or without assets/ prefix
        if relative_path.startswith('assets/'):
            full_path = os.path.join(self.project_path, relative_path)
        else:
            full_path = os.path.join(self.project_path, 'assets', relative_path)
        
        # Convert to file:// URL
        return f"file:///{full_path.replace(os.sep, '/')}"
    
    def get_subreport_config(self, subreport_id: str) -> Optional[Dict[str, Any]]:
        """
        Get sub-report configuration by ID
        
        Args:
            subreport_id: Sub-report identifier
            
        Returns:
            Sub-report config dict or None
        """
        for sr in self.config.get('subReports', []):
            if sr.get('id') == subreport_id:
                return sr
        return None
    
    def render_subreport(
        self,
        subreport_id: str,
        data: Dict[str, Any],
        depth: int = 0
    ) -> str:
        """
        Render a single sub-report
        
        Args:
            subreport_id: Sub-report identifier
            data: Data context for rendering
            depth: Current nesting depth (for recursion protection)
            
        Returns:
            Rendered HTML string
            
        Raises:
            ValueError: If sub-report not found or max depth exceeded
        """
        if depth >= self.MAX_NESTING_DEPTH:
            raise ValueError(f"Maximum sub-report nesting depth ({self.MAX_NESTING_DEPTH}) exceeded")
        
        sr_config = self.get_subreport_config(subreport_id)
        if not sr_config:
            raise ValueError(f"Sub-report '{subreport_id}' not found")
        
        template_path = sr_config.get('template')
        if not template_path:
            raise ValueError(f"Sub-report '{subreport_id}' has no template defined")
        
        # Get relative path from templates dir
        if template_path.startswith('templates/'):
            template_rel = template_path[len('templates/'):]
        else:
            template_rel = template_path
        
        try:
            template = self.env.get_template(template_rel)
            
            # Add built-in variables
            from datetime import datetime
            render_data = {
                **data,
                'REPORT_DATE': datetime.now().strftime('%Y-%m-%d'),
                'REPORT_TIME': datetime.now().strftime('%H:%M:%S'),
                'REPORT_DATETIME': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'SUBREPORT_ID': subreport_id,
            }
            
            # Add row count if rows present
            if 'rows' in data and isinstance(data['rows'], list):
                render_data['TOTAL_RECORDS'] = len(data['rows'])
                render_data['row_count'] = len(data['rows'])
                if len(data['rows']) > 0:
                    render_data['_columns'] = list(data['rows'][0].keys())
            
            return Markup(template.render(**render_data))
            
        except TemplateError as e:
            raise ValueError(f"Error rendering sub-report '{subreport_id}': {str(e)}")
    
    def render_all_subreports(
        self,
        subreport_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Render all sub-reports with their respective data
        
        Args:
            subreport_data: Dict mapping sub-report IDs to their data
            
        Returns:
            Dict mapping sub-report IDs to rendered HTML
        """
        rendered = {}
        
        for subreport_id, data in subreport_data.items():
            try:
                rendered[subreport_id] = self.render_subreport(subreport_id, data)
            except ValueError as e:
                # Include error message in output for debugging
                rendered[subreport_id] = Markup(f'<div class="subreport-error">Error: {str(e)}</div>')
        
        return rendered
    
    def compose_report(
        self,
        main_data: Dict[str, Any],
        subreport_data: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> str:
        """
        Compose the full report by rendering main template with sub-reports
        
        Args:
            main_data: Data for the main template
            subreport_data: Optional dict mapping sub-report IDs to their data
            
        Returns:
            Complete rendered HTML
        """
        from datetime import datetime
        
        # Render all sub-reports first
        rendered_subreports = {}
        if subreport_data:
            rendered_subreports = self.render_all_subreports(subreport_data)
        else:
            # Render sub-reports with empty data if not provided
            for sr in self.config.get('subReports', []):
                sr_id = sr.get('id')
                if sr_id:
                    try:
                        rendered_subreports[sr_id] = self.render_subreport(sr_id, {})
                    except ValueError:
                        rendered_subreports[sr_id] = ''
        
        # Load and render main template
        main_template_path = self.config.get('mainTemplate', 'templates/main.html')
        if main_template_path.startswith('templates/'):
            main_template_rel = main_template_path[len('templates/'):]
        else:
            main_template_rel = main_template_path
        
        try:
            template = self.env.get_template(main_template_rel)
        except TemplateError as e:
            raise ValueError(f"Error loading main template: {str(e)}")
        
        # Build complete data context
        render_data = {
            **main_data,
            'subreports': CaseInsensitiveSubreports(rendered_subreports),
            'REPORT_DATE': datetime.now().strftime('%Y-%m-%d'),
            'REPORT_TIME': datetime.now().strftime('%H:%M:%S'),
            'REPORT_DATETIME': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Add row count if rows present
        if 'rows' in main_data and isinstance(main_data['rows'], list):
            render_data['TOTAL_RECORDS'] = len(main_data['rows'])
            render_data['row_count'] = len(main_data['rows'])
            if len(main_data['rows']) > 0:
                render_data['_columns'] = list(main_data['rows'][0].keys())
                # Flatten first row fields into context so templates can use
                # {{ TITLE }} or {{ title }} directly instead of {{ rows[0].TITLE }}
                first_row = main_data['rows'][0]
                for col_name, col_value in first_row.items():
                    # Add as original case (e.g. TITLE)
                    if col_name not in render_data:
                        render_data[col_name] = col_value
                    # Add as lowercase (e.g. title)
                    lower_name = col_name.lower()
                    if lower_name not in render_data:
                        render_data[lower_name] = col_value
        
        # Inject project styles if configured
        rendered_html = template.render(**render_data)
        rendered_html = self._inject_project_styles(rendered_html)
        rendered_html = self._inject_project_fonts(rendered_html)
        
        return rendered_html
    
    def _inject_project_styles(self, html: str) -> str:
        """Inject project CSS styles into HTML"""
        styles = self.config.get('assets', {}).get('styles', [])
        if not styles:
            return html
        
        style_links = []
        for style_path in styles:
            abs_path = os.path.join(self.project_path, style_path)
            if os.path.exists(abs_path):
                try:
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    style_links.append(f'<style>\n{css_content}\n</style>')
                except IOError:
                    pass
        
        if style_links and '</head>' in html:
            styles_html = '\n'.join(style_links)
            html = html.replace('</head>', f'{styles_html}\n</head>')
        
        return html
    
    def _inject_project_fonts(self, html: str) -> str:
        """Inject project font definitions into HTML"""
        fonts = self.config.get('assets', {}).get('fonts', [])
        if not fonts:
            return html
        
        font_faces = []
        for font_path in fonts:
            abs_path = os.path.join(self.project_path, font_path)
            if os.path.exists(abs_path):
                # Extract font name from filename
                font_name = os.path.splitext(os.path.basename(font_path))[0]
                font_url = f"file:///{abs_path.replace(os.sep, '/')}"
                
                font_faces.append(f"""
@font-face {{
    font-family: '{font_name}';
    src: url('{font_url}');
}}
""")
        
        if font_faces:
            font_css = '<style>\n' + '\n'.join(font_faces) + '</style>'
            if '</head>' in html:
                html = html.replace('</head>', f'{font_css}\n</head>')
            elif '<head>' in html:
                html = html.replace('<head>', f'<head>\n{font_css}')
            else:
                html = font_css + html
        
        return html
    
    def detect_circular_references(self) -> List[str]:
        """
        Detect circular references in sub-report includes
        
        Returns:
            List of circular reference chains found (empty if none)
        """
        circular = []
        
        # Build a dependency graph
        dependencies: Dict[str, Set[str]] = {}
        
        for sr in self.config.get('subReports', []):
            sr_id = sr.get('id')
            template_path = sr.get('template')
            
            if sr_id and template_path:
                full_path = os.path.join(self.project_path, template_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # Find include_subreport references
                        includes = re.findall(r"include_subreport\s*['\"](\w+)['\"]", content)
                        dependencies[sr_id] = set(includes)
                    except IOError:
                        dependencies[sr_id] = set()
        
        # Check for cycles using DFS
        def has_cycle(node: str, visited: Set[str], path: List[str]) -> Optional[List[str]]:
            if node in visited:
                if node in path:
                    cycle_start = path.index(node)
                    return path[cycle_start:] + [node]
                return None
            
            visited.add(node)
            path.append(node)
            
            for dep in dependencies.get(node, set()):
                cycle = has_cycle(dep, visited, path)
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        for sr_id in dependencies:
            cycle = has_cycle(sr_id, set(), [])
            if cycle:
                chain = ' -> '.join(cycle)
                if chain not in circular:
                    circular.append(chain)
        
        return circular
    
    def get_template_content(self, template_path: str) -> str:
        """
        Load template content from project
        
        Args:
            template_path: Path relative to project (e.g., 'templates/main.html')
            
        Returns:
            Template content string
        """
        full_path = os.path.join(self.project_path, template_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_query_content(self, query_path: str) -> str:
        """
        Load query content from project
        
        Args:
            query_path: Path relative to project (e.g., 'queries/main.sql')
            
        Returns:
            SQL query string
        """
        full_path = os.path.join(self.project_path, query_path)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Query not found: {query_path}")
        
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def clear_cache(self):
        """Clear the render cache"""
        self._render_cache.clear()
