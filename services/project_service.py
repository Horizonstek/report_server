"""
Project Service - Manages report projects with templates, queries, and assets
"""
import os
import json
import shutil
from datetime import datetime
from typing import Optional, List, Dict, Any


class ProjectService:
    """Service for managing report projects"""
    
    # Default project structure
    PROJECT_DIRS = ['queries', 'templates', 'templates/components', 'assets/fonts', 'assets/images', 'assets/styles', 'output']
    
    def __init__(self, projects_dir: str):
        """
        Initialize the project service
        
        Args:
            projects_dir: Root directory for storing projects
        """
        self.projects_dir = projects_dir
        os.makedirs(projects_dir, exist_ok=True)
        
        # Samples directory for project templates
        server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.samples_dir = os.path.join(server_root, 'samples')
    
    def create_project(
        self,
        name: str,
        description: str = '',
        author: str = '',
        page_size: str = 'A4',
        orientation: str = 'portrait',
        template: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new report project with folder structure
        
        Args:
            name: Project name (will be used as folder name)
            description: Project description
            author: Project author
            page_size: Default page size (A4, Letter, etc.)
            orientation: Default orientation (portrait, landscape)
            template: Optional template ID (e.g., 'report', 'invoice') to use as starter
            
        Returns:
            Project configuration dict
            
        Raises:
            ValueError: If project already exists or name is invalid
        """
        # Sanitize and validate name
        safe_name = self._sanitize_name(name)
        if not safe_name:
            raise ValueError("Invalid project name")
        
        project_path = os.path.join(self.projects_dir, safe_name)
        
        if os.path.exists(project_path):
            raise ValueError(f"Project '{safe_name}' already exists")
        
        # If a template is specified, create from template
        if template and template != 'blank':
            return self._create_project_from_template(
                safe_name, project_path, name, description, author,
                page_size, orientation, template
            )
        
        # Create blank project with default TLR_MODEL structure
        os.makedirs(project_path)
        for subdir in self.PROJECT_DIRS:
            os.makedirs(os.path.join(project_path, subdir), exist_ok=True)
        
        # Create project.json
        now = datetime.now().isoformat()
        project_config = {
            "name": name,
            "version": "1.0.0",
            "description": description,
            "author": author,
            "created": now,
            "updated": now,
            "settings": {
                "pageSize": page_size,
                "orientation": orientation,
                "margins": {
                    "top": "2cm",
                    "right": "1.5cm",
                    "bottom": "2cm",
                    "left": "1.5cm"
                },
                "defaultFont": None
            },
            "mainTemplate": "templates/main.html",
            "mainQuery": "queries/main.sql",
            "subReports": [],
            "assets": {
                "fonts": [
                    "assets/fonts/Cairo-Regular.ttf"
                ],
                "images": [],
                "styles": [
                    "assets/styles/styles.css"
                ]
            },
            "parameters": []
        }
        
        config_path = os.path.join(project_path, "project.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, ensure_ascii=False, indent=2)
        
        # Create default main template (TLR_MODEL style)
        self._create_default_main_template(project_path, name)
        
        # Create default main query
        self._create_default_main_query(project_path)
        
        # Copy default font
        self._copy_default_font(project_path)
        
        # Create default styles
        self._create_default_styles(project_path)
        
        return {
            "id": safe_name,
            "path": project_path,
            "config": project_config
        }
    
    def load_project(self, project_id: str) -> Dict[str, Any]:
        """
        Load a project configuration
        
        Args:
            project_id: Project identifier (folder name)
            
        Returns:
            Project configuration dict with path
            
        Raises:
            FileNotFoundError: If project doesn't exist
            ValueError: If project.json is invalid
        """
        project_path = os.path.join(self.projects_dir, project_id)
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project '{project_id}' not found")
        
        config_path = os.path.join(project_path, "project.json")
        
        if not os.path.exists(config_path):
            raise ValueError(f"Project '{project_id}' is missing project.json")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid project.json: {str(e)}")
        
        return {
            "id": project_id,
            "path": project_path,
            "config": config
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects
        
        Returns:
            List of project summaries
        """
        projects = []
        
        if not os.path.exists(self.projects_dir):
            return projects
        
        for item in os.listdir(self.projects_dir):
            item_path = os.path.join(self.projects_dir, item)
            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, "project.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        projects.append({
                            "id": item,
                            "name": config.get("name", item),
                            "description": config.get("description", ""),
                            "updated": config.get("updated", ""),
                            "path": item_path
                        })
                    except (json.JSONDecodeError, IOError):
                        # Skip invalid projects
                        pass
        
        return sorted(projects, key=lambda x: x['name'])
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update project configuration
        
        Args:
            project_id: Project identifier
            updates: Dict of fields to update
            
        Returns:
            Updated project configuration
        """
        project = self.load_project(project_id)
        config = project['config']
        
        # Update allowed fields
        allowed_fields = ['name', 'description', 'author', 'version', 'settings', 
                          'mainTemplate', 'mainQuery', 'subReports', 'assets', 'parameters']
        
        for field in allowed_fields:
            if field in updates:
                if field == 'settings' and isinstance(updates[field], dict):
                    # Merge settings
                    config['settings'] = {**config.get('settings', {}), **updates[field]}
                else:
                    config[field] = updates[field]
        
        # Update timestamp
        config['updated'] = datetime.now().isoformat()
        
        # Save
        config_path = os.path.join(project['path'], "project.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return {
            "id": project_id,
            "path": project['path'],
            "config": config
        }
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all its contents
        
        Args:
            project_id: Project identifier
            
        Returns:
            True if deleted
            
        Raises:
            FileNotFoundError: If project doesn't exist
        """
        project_path = os.path.join(self.projects_dir, project_id)
        
        if not os.path.exists(project_path):
            raise FileNotFoundError(f"Project '{project_id}' not found")
        
        shutil.rmtree(project_path)
        return True
    
    def validate_project(self, project_id: str) -> Dict[str, Any]:
        """
        Validate project structure and references
        
        Args:
            project_id: Project identifier
            
        Returns:
            Validation result with errors and warnings
        """
        project = self.load_project(project_id)
        config = project['config']
        path = project['path']
        
        errors = []
        warnings = []
        
        # Check main template exists
        main_template = config.get('mainTemplate')
        if main_template:
            template_path = os.path.join(path, main_template)
            if not os.path.exists(template_path):
                errors.append(f"Main template not found: {main_template}")
        else:
            errors.append("No main template specified")
        
        # Check main query exists
        main_query = config.get('mainQuery')
        if main_query:
            query_path = os.path.join(path, main_query)
            if not os.path.exists(query_path):
                warnings.append(f"Main query not found: {main_query}")
        
        # Check sub-reports
        for subreport in config.get('subReports', []):
            sr_template = subreport.get('template')
            if sr_template:
                sr_path = os.path.join(path, sr_template)
                if not os.path.exists(sr_path):
                    errors.append(f"Sub-report template not found: {sr_template}")
            
            sr_query = subreport.get('query')
            if sr_query:
                sq_path = os.path.join(path, sr_query)
                if not os.path.exists(sq_path):
                    warnings.append(f"Sub-report query not found: {sr_query}")
        
        # Check assets
        for asset_type in ['fonts', 'images', 'styles']:
            for asset in config.get('assets', {}).get(asset_type, []):
                asset_path = os.path.join(path, asset)
                if not os.path.exists(asset_path):
                    warnings.append(f"Asset not found: {asset}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def add_subreport(
        self,
        project_id: str,
        subreport_id: str,
        template_name: str,
        query_name: Optional[str] = None,
        position: str = 'inline'
    ) -> Dict[str, Any]:
        """
        Add a sub-report definition to a project
        
        Args:
            project_id: Project identifier
            subreport_id: Unique ID for the sub-report
            template_name: Template file name (without path)
            query_name: Optional query file name
            position: Position hint (header, footer, inline)
            
        Returns:
            Updated project configuration
        """
        project = self.load_project(project_id)
        config = project['config']
        path = project['path']
        
        # Check for duplicate ID
        existing_ids = [sr['id'] for sr in config.get('subReports', [])]
        if subreport_id in existing_ids:
            raise ValueError(f"Sub-report '{subreport_id}' already exists")
        
        # Create template file if it doesn't exist
        template_path = f"templates/{template_name}.html"
        full_template_path = os.path.join(path, template_path)
        if not os.path.exists(full_template_path):
            self._create_default_subreport_template(full_template_path, subreport_id)
        
        # Create query file if specified and doesn't exist
        query_path = None
        if query_name:
            query_path = f"queries/{query_name}.sql"
            full_query_path = os.path.join(path, query_path)
            if not os.path.exists(full_query_path):
                self._create_default_query(full_query_path, query_name)
        
        # Add to config
        new_subreport = {
            "id": subreport_id,
            "template": template_path,
            "query": query_path,
            "position": position
        }
        
        if 'subReports' not in config:
            config['subReports'] = []
        config['subReports'].append(new_subreport)
        
        return self.update_project(project_id, {'subReports': config['subReports']})
    
    def add_asset(
        self,
        project_id: str,
        asset_type: str,
        file_path: str,
        target_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add an asset file to a project
        
        Args:
            project_id: Project identifier
            asset_type: Type of asset (fonts, images, styles)
            file_path: Source file path
            target_name: Optional target filename (uses source name if not provided)
            
        Returns:
            Updated project configuration
        """
        if asset_type not in ['fonts', 'images', 'styles']:
            raise ValueError(f"Invalid asset type: {asset_type}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        project = self.load_project(project_id)
        path = project['path']
        config = project['config']
        
        # Determine target path
        filename = target_name or os.path.basename(file_path)
        target_path = f"assets/{asset_type}/{filename}"
        full_target = os.path.join(path, target_path)
        
        # Copy file
        shutil.copy2(file_path, full_target)
        
        # Update config
        if 'assets' not in config:
            config['assets'] = {'fonts': [], 'images': [], 'styles': []}
        if asset_type not in config['assets']:
            config['assets'][asset_type] = []
        
        if target_path not in config['assets'][asset_type]:
            config['assets'][asset_type].append(target_path)
        
        return self.update_project(project_id, {'assets': config['assets']})
    
    def resolve_asset_path(self, project_path: str, relative_path: str) -> str:
        """
        Resolve a relative asset path to absolute path
        
        Args:
            project_path: Absolute path to project
            relative_path: Relative path within project
            
        Returns:
            Absolute path to asset
        """
        return os.path.abspath(os.path.join(project_path, relative_path))
    
    def get_project_base_url(self, project_id: str) -> str:
        """
        Get the base URL for a project (for WeasyPrint asset resolution)
        
        Args:
            project_id: Project identifier
            
        Returns:
            File URL for project directory
        """
        project = self.load_project(project_id)
        # Convert to file:// URL format
        return f"file:///{project['path'].replace(os.sep, '/')}/"
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List available project templates from the samples directory
        
        Returns:
            List of template summaries with id, name, and description
        """
        templates = []
        
        if not os.path.exists(self.samples_dir):
            return templates
        
        for item in sorted(os.listdir(self.samples_dir)):
            item_path = os.path.join(self.samples_dir, item)
            if os.path.isdir(item_path):
                config_path = os.path.join(item_path, 'project.json')
                if os.path.exists(config_path):
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        templates.append({
                            'id': item,
                            'name': config.get('name', item.title()),
                            'description': config.get('description', ''),
                        })
                    except (json.JSONDecodeError, IOError):
                        pass
        
        return templates
    
    # ==========================================
    # Private Helper Methods
    # ==========================================
    
    def _create_project_from_template(
        self,
        safe_name: str,
        project_path: str,
        name: str,
        description: str,
        author: str,
        page_size: str,
        orientation: str,
        template: str
    ) -> Dict[str, Any]:
        """
        Create a project by copying a template from the samples directory
        
        Args:
            safe_name: Sanitized project folder name
            project_path: Target path for the new project
            name: Project display name
            description: Project description
            author: Project author
            page_size: Default page size
            orientation: Default orientation
            template: Template ID (folder name in samples/)
        """
        template_path = os.path.join(self.samples_dir, template)
        
        if not os.path.isdir(template_path):
            raise ValueError(f"Template '{template}' not found")
        
        template_config_path = os.path.join(template_path, 'project.json')
        if not os.path.exists(template_config_path):
            raise ValueError(f"Template '{template}' is not a valid project template")
        
        # Copy the entire template directory
        shutil.copytree(template_path, project_path)
        
        # Ensure all standard directories exist
        for subdir in self.PROJECT_DIRS:
            os.makedirs(os.path.join(project_path, subdir), exist_ok=True)
        
        # Load the template's config and update with user-provided values
        config_path = os.path.join(project_path, 'project.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            project_config = json.load(f)
        
        now = datetime.now().isoformat()
        project_config['name'] = name
        project_config['description'] = description or project_config.get('description', '')
        project_config['author'] = author or project_config.get('author', '')
        project_config['created'] = now
        project_config['updated'] = now
        project_config['settings']['pageSize'] = page_size
        project_config['settings']['orientation'] = orientation
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(project_config, f, ensure_ascii=False, indent=2)
        
        return {
            "id": safe_name,
            "path": project_path,
            "config": project_config
        }
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as folder name"""
        if not name:
            return ''
        # Replace unsafe characters
        safe = name.strip()
        for char in ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']:
            safe = safe.replace(char, '_')
        return safe
    
    def _create_default_main_template(self, project_path: str, project_name: str = 'Report'):
        """Create a default main.html template (TLR_MODEL style)"""
        template_content = f"""<!doctype html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="UTF-8" />
    <title>{{{{ title | default('{project_name}') }}}}</title>
    <style>
      * {{
        box-sizing: border-box;
      }}
      body {{
        font-family: "Cairo-Regular", "Cairo", Arial, sans-serif;
        margin: 0;
        padding: 30px;
        color: #2c3e50;
        direction: rtl;
        background-color: #fff;
      }}

      /* Header Section */
      .report-header {{
        text-align: center;
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 3px solid #1a5276;
      }}
      .report-header h1 {{
        color: #1a5276;
        font-size: 28px;
        margin: 0 0 8px 0;
      }}
      .report-header .subtitle {{
        color: #5d6d7e;
        font-size: 14px;
      }}

      /* Table Styles */
      table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        font-size: 14px;
      }}
      thead {{
        background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
      }}
      th {{
        color: white;
        padding: 12px 16px;
        text-align: right;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
      }}
      td {{
        padding: 10px 16px;
        text-align: right;
        border-bottom: 1px solid #e8ecef;
        color: #34495e;
      }}
      tr:nth-child(even) {{
        background-color: #f8f9fa;
      }}
      tr:hover {{
        background-color: #eaf2f8;
      }}

      .null-value {{
        color: #bdc3c7;
        font-style: italic;
      }}

      /* Footer */
      .report-footer {{
        margin-top: 30px;
        padding-top: 15px;
        border-top: 2px solid #e8ecef;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
        color: #95a5a6;
      }}
      .record-count {{
        background: #1a5276;
        color: white;
        padding: 4px 14px;
        border-radius: 12px;
        font-size: 12px;
      }}
    </style>
  </head>
  <body>
    {{%- if subreports and subreports.header %}}
      {{{{ subreports.header | safe }}}}
    {{%- endif %}}

    <div class="report-header">
      <h1>{{{{ title | default('{project_name}') }}}}</h1>
      <div class="subtitle">{{{{ REPORT_DATETIME }}}}</div>
    </div>

    <table>
      <thead>
        <tr>
          {{% for col in _columns %}}
          <th>{{{{ col }}}}</th>
          {{% endfor %}}
        </tr>
      </thead>
      <tbody>
        {{% for row in rows %}}
        <tr>
          {{% for col in _columns %}}
          <td>
            {{% if row[col] is not none %}}{{{{ row[col] }}}}{{% else %}}<span class="null-value">\u2014</span>{{% endif %}}
          </td>
          {{% endfor %}}
        </tr>
        {{% endfor %}}
      </tbody>
    </table>

    <div class="report-footer">
      <div>{{{{ REPORT_DATETIME }}}}</div>
      <div class="record-count">
        Total Records: {{{{ TOTAL_RECORDS | default(0) }}}}
      </div>
    </div>

    {{%- if subreports and subreports.footer %}}
      {{{{ subreports.footer | safe }}}}
    {{%- endif %}}
  </body>
</html>
"""
        template_path = os.path.join(project_path, 'templates', 'main.html')
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def _create_default_main_query(self, project_path: str):
        """Create a default main.sql query"""
        query_content = """-- Main report query
-- Replace this with your actual SQL query
-- Use :param_name syntax for parameters

SELECT * FROM CLIENT_AS_SAS_130_25.TLR_MODEL
"""
        query_path = os.path.join(project_path, 'queries', 'main.sql')
        with open(query_path, 'w', encoding='utf-8') as f:
            f.write(query_content)
    
    def _copy_default_font(self, project_path: str):
        """Copy the default Cairo font into the project"""
        # Look for the font in the bundled resources directory
        server_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        source_font = os.path.join(server_root, 'resources', 'fonts', 'Cairo-Regular.ttf')
        
        if os.path.exists(source_font):
            target_font = os.path.join(project_path, 'assets', 'fonts', 'Cairo-Regular.ttf')
            shutil.copy2(source_font, target_font)
    
    def _create_default_styles(self, project_path: str):
        """Create a default styles.css file"""
        css_content = """/* Project Styles */
/* Add your custom CSS here */

"""
        styles_path = os.path.join(project_path, 'assets', 'styles', 'styles.css')
        with open(styles_path, 'w', encoding='utf-8') as f:
            f.write(css_content)
    
    def _create_default_subreport_template(self, template_path: str, subreport_id: str):
        """Create a default sub-report template"""
        template_content = f"""<!-- Sub-report: {subreport_id} -->
<div class="subreport subreport-{subreport_id}">
    <p>Sub-report content for: {subreport_id}</p>
    <!-- Add your template content here -->
</div>
"""
        os.makedirs(os.path.dirname(template_path), exist_ok=True)
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def _create_default_query(self, query_path: str, query_name: str):
        """Create a default SQL query file"""
        query_content = f"""-- Query: {query_name}
-- Add your SQL query here

SELECT 1 AS PLACEHOLDER FROM DUAL
"""
        os.makedirs(os.path.dirname(query_path), exist_ok=True)
        with open(query_path, 'w', encoding='utf-8') as f:
            f.write(query_content)
