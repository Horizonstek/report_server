"""
Trash management routes - API endpoints for managing trashed (soft-deleted) projects
"""
from flask import Blueprint, jsonify

from services.project_service import ProjectService
from config import get_config
import os

trash_bp = Blueprint('trash', __name__)
config = get_config()

# Initialize service (same projects_dir as project_routes)
projects_dir = os.path.join(config.TEMPLATES_DIR, '..', 'projects')
project_service = ProjectService(projects_dir)


@trash_bp.route('', methods=['GET'])
def list_trash():
    """
    List all trashed projects
    
    Returns: List of trashed project summaries
    """
    try:
        trashed = project_service.list_trash()
        return jsonify({
            'success': True,
            'projects': trashed,
            'count': len(trashed)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@trash_bp.route('/<trash_id>/restore', methods=['POST'])
def restore_project(trash_id):
    """
    Restore a project from trash
    
    Args:
        trash_id: Trash entry identifier
        
    Returns: Restored project info
    """
    try:
        result = project_service.restore_project(trash_id)
        return jsonify({
            'success': True,
            'message': f"Project restored as '{result['id']}'",
            'project': result
        })
    except FileNotFoundError:
        return jsonify({'error': 'Trash entry not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

