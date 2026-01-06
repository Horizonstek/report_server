"""
Query Service - Manages SQL query files storage and retrieval
"""
import os
import re
from typing import List, Optional


class QueryService:
    """Service for managing SQL query files"""
    
    def __init__(self, queries_dir: str):
        """
        Initialize the query service
        
        Args:
            queries_dir: Directory to store query files
        """
        self.queries_dir = queries_dir
        self._ensure_queries_directory()
    
    def _ensure_queries_directory(self):
        """Create queries directory if it doesn't exist"""
        os.makedirs(self.queries_dir, exist_ok=True)
        # Create subdirectory for linked queries if needed
        os.makedirs(os.path.join(self.queries_dir, 'queries'), exist_ok=True)
    
    def save_query(self, code: str, content: str) -> str:
        """
        Save a query file
        
        Args:
            code: Query identifier (will be used as filename without .sql)
            content: SQL query content
        
        Returns:
            Path to the saved query file
        
        Raises:
            ValueError: If code is invalid
            IOError: If file cannot be saved
        """
        # Validate code
        if not code or not self._is_valid_code(code):
            raise ValueError('Invalid query code. Use only letters, numbers, hyphens, and underscores.')
        
        # Construct file path
        filename = f"{code}.sql"
        file_path = os.path.join(self.queries_dir, 'queries', filename)
        
        # Save content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return file_path
        except Exception as e:
            raise IOError(f"Failed to save query: {str(e)}")
    
    def load_query(self, code: str) -> str:
        """
        Load a query by code
        
        Args:
            code: Query identifier
        
        Returns:
            Query SQL content
        
        Raises:
            FileNotFoundError: If query doesn't exist
            ValueError: If code is invalid
        """
        if not self._is_valid_code(code):
            raise ValueError('Invalid query code')
        
        filename = f"{code}.sql"
        file_path = os.path.join(self.queries_dir, 'queries', filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'Query "{code}" not found')
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Failed to load query: {str(e)}")
    
    def list_queries(self) -> List[str]:
        """
        List all available query codes
        
        Returns:
            List of query codes (filenames without .sql)
        """
        queries_path = os.path.join(self.queries_dir, 'queries')
        
        if not os.path.exists(queries_path):
            return []
        
        try:
            files = os.listdir(queries_path)
            # Filter for .sql files only
            query_files = [
                os.path.splitext(f)[0]
                for f in files
                if f.endswith('.sql') and os.path.isfile(os.path.join(queries_path, f))
            ]
            return sorted(query_files)
        except Exception as e:
            print(f"Error listing queries: {e}")
            return []
    
    def delete_query(self, code: str) -> bool:
        """
        Delete a query by code
        
        Args:
            code: Query identifier
        
        Returns:
            True if deleted successfully
        
        Raises:
            FileNotFoundError: If query doesn't exist
            ValueError: If code is invalid
        """
        if not self._is_valid_code(code):
            raise ValueError('Invalid query code')
        
        filename = f"{code}.sql"
        file_path = os.path.join(self.queries_dir, 'queries', filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'Query "{code}" not found')
        
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            raise IOError(f"Failed to delete query: {str(e)}")
    
    def query_exists(self, code: str) -> bool:
        """
        Check if a query exists
        
        Args:
            code: Query identifier
        
        Returns:
            True if query exists
        """
        if not self._is_valid_code(code):
            return False
        
        filename = f"{code}.sql"
        file_path = os.path.join(self.queries_dir, 'queries', filename)
        return os.path.exists(file_path)
    
    @staticmethod
    def _is_valid_code(code: str) -> bool:
        """
        Validate query code format
        
        Args:
            code: Query code to validate
        
        Returns:
            True if valid
        """
        # Allow letters, numbers, hyphens, and underscores
        # Must not be empty and not contain path separators
        if not code:
            return False
        
        # Check for path separators or dangerous characters
        if '/' in code or '\\' in code or '..' in code:
            return False
        
        # Must match safe pattern
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', code))
