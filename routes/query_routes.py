"""
Query routes
"""
from flask import Blueprint, request, jsonify
from services.query_service import QueryService
from config import get_config

query_bp = Blueprint('query', __name__)
config = get_config()
query_service = QueryService(queries_dir=config.TEMPLATES_DIR)


@query_bp.route('/upload', methods=['POST'])
def upload_query():
    """
    Upload a query file
    
    Request: text/plain body with SQL content
    Headers:
    - X-Query-Code: Query identifier (filename without .sql)
    """
    try:
        # Get query code from header
        code = request.headers.get('X-Query-Code', '')
        if not code:
            return jsonify({'error': 'Query code is required in X-Query-Code header'}), 400
        
        # Get query content from body
        content = request.get_data(as_text=True)
        if not content or not content.strip():
            return jsonify({'error': 'Query content is required'}), 400
        
        # Validate file size
        content_size = len(content.encode('utf-8'))
        max_size = config.MAX_TEMPLATE_SIZE  # Reuse template size limit
        
        if content_size > max_size:
            return jsonify({
                'error': f'Query size exceeds maximum allowed size ({max_size} bytes)'
            }), 413
        
        # Save query
        try:
            query_path = query_service.save_query(code, content)
            return jsonify({
                'success': True,
                'code': code,
                'path': query_path,
                'message': f'Query "{code}" uploaded successfully'
            }), 201
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except IOError as e:
            return jsonify({'error': f'Failed to save query: {str(e)}'}), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@query_bp.route('/', methods=['GET'])
def list_queries():
    """
    List all available queries
    
    Returns: List of query codes
    """
    try:
        queries = query_service.list_queries()
        return jsonify({
            'success': True,
            'queries': queries,
            'count': len(queries)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@query_bp.route('/<code>', methods=['GET'])
def get_query(code):
    """
    Get a query's SQL content by code
    
    Args:
        code: Query code (filename without .sql)
    
    Returns:
        Query SQL content
    """
    try:
        content = query_service.load_query(code)
        return jsonify({
            'success': True,
            'code': code,
            'content': content
        })
    except FileNotFoundError:
        return jsonify({'error': 'Query not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@query_bp.route('/<code>', methods=['DELETE'])
def delete_query(code):
    """
    Delete a query by code
    
    Args:
        code: Query code (filename without .sql)
    """
    try:
        query_service.delete_query(code)
        return jsonify({
            'success': True,
            'message': f'Query "{code}" deleted successfully'
        })
    except FileNotFoundError:
        return jsonify({'error': 'Query not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
