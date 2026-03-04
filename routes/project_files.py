
# ==========================================
# File Content Routes
# ==========================================

@project_bp.route('/<project_id>/files', methods=['GET'])
def get_file_content(project_id):
    """
    Get the string content of a project file (template, query, css, etc.)
    
    Query params:
        path: Relative path to the file in the project
    """
    try:
        file_path_req = request.args.get('path')
        if not file_path_req:
            return jsonify({'error': 'path query parameter is required'}), 400
            
        project = project_service.load_project(project_id)
        
        # Prevent directory traversal
        safe_path = os.path.normpath(f"/{file_path_req}").lstrip('/')
        full_path = os.path.join(project['path'], safe_path)
        
        # Verify it's within project directory
        if not os.path.abspath(full_path).startswith(os.path.abspath(project['path'])):
            return jsonify({'error': 'Invalid file path'}), 403
            
        if not os.path.exists(full_path):
            return jsonify({'error': f"File not found: {safe_path}"}), 404
            
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return jsonify({
            'success': True,
            'content': content,
            'path': safe_path,
            'projectId': project_id
        })
        
    except UnicodeDecodeError:
        return jsonify({'error': 'File is not a text file'}), 400
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/<project_id>/files', methods=['PUT'])
def update_file_content(project_id):
    """
    Update the string content of a project file
    
    Query params:
        path: Relative path to the file in the project
        
    Request body:
        { "content": "..." }
    """
    try:
        file_path_req = request.args.get('path')
        if not file_path_req:
            return jsonify({'error': 'path query parameter is required'}), 400
            
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Missing content in request body'}), 400
            
        content = data['content']
            
        project = project_service.load_project(project_id)
        
        # Prevent directory traversal
        safe_path = os.path.normpath(f"/{file_path_req}").lstrip('/')
        full_path = os.path.join(project['path'], safe_path)
        
        # Verify it's within project directory
        if not os.path.abspath(full_path).startswith(os.path.abspath(project['path'])):
            return jsonify({'error': 'Invalid file path'}), 403
            
        # Ensure directory exists but we shouldn't create new directories here if they shouldn't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return jsonify({
            'success': True,
            'path': safe_path,
            'message': 'File updated successfully'
        })
        
    except FileNotFoundError:
        return jsonify({'error': 'Project not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
