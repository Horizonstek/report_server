"""
Oracle Database Service - Handles database connections and query execution
"""
import re
from typing import Any, Dict, List, Optional, Tuple
from contextlib import contextmanager

try:
    import oracledb
    ORACLEDB_AVAILABLE = True
except ImportError:
    ORACLEDB_AVAILABLE = False


class DatabaseService:
    """Service for Oracle database operations"""
    
    def __init__(self, config):
        """
        Initialize the database service
        
        Args:
            config: Configuration object with Oracle settings
        """
        self.config = config
        self._pool = None
        self._initialized = False
        
    def is_available(self) -> bool:
        """Check if Oracle database driver is available"""
        return ORACLEDB_AVAILABLE
    
    def is_enabled(self) -> bool:
        """Check if Oracle connectivity is enabled in config"""
        return getattr(self.config, 'ORACLE_ENABLED', False)
    
    def is_configured(self) -> bool:
        """Check if Oracle connection is properly configured"""
        if not self.is_enabled():
            return False
        
        user = getattr(self.config, 'ORACLE_USER', '')
        password = getattr(self.config, 'ORACLE_PASSWORD', '')
        
        # Need either DSN or (host + service_name/sid)
        dsn = getattr(self.config, 'ORACLE_DSN', '')
        host = getattr(self.config, 'ORACLE_HOST', '')
        service_name = getattr(self.config, 'ORACLE_SERVICE_NAME', '')
        sid = getattr(self.config, 'ORACLE_SID', '')
        
        has_dsn = bool(dsn)
        has_host_config = bool(host and (service_name or sid))
        
        return bool(user and password and (has_dsn or has_host_config))
    
    def _get_dsn(self) -> str:
        """Build the DSN string for Oracle connection"""
        dsn = getattr(self.config, 'ORACLE_DSN', '')
        if dsn:
            return dsn
        
        host = getattr(self.config, 'ORACLE_HOST', 'localhost')
        port = getattr(self.config, 'ORACLE_PORT', 1521)
        service_name = getattr(self.config, 'ORACLE_SERVICE_NAME', '')
        sid = getattr(self.config, 'ORACLE_SID', '')
        
        if service_name:
            return oracledb.makedsn(host, port, service_name=service_name)
        elif sid:
            return oracledb.makedsn(host, port, sid=sid)
        else:
            raise ValueError("Either ORACLE_SERVICE_NAME or ORACLE_SID must be configured")
    
    def initialize(self) -> bool:
        """
        Initialize the connection pool
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not ORACLEDB_AVAILABLE:
            return False
        
        if not self.is_configured():
            return False
        
        if self._initialized:
            return True
        
        try:
            # Use thin mode (no Oracle Client required)
            oracledb.init_oracle_client()
        except Exception:
            # Thin mode is default, thick mode initialization failed
            pass
        
        try:
            self._pool = oracledb.create_pool(
                user=self.config.ORACLE_USER,
                password=self.config.ORACLE_PASSWORD,
                dsn=self._get_dsn(),
                min=getattr(self.config, 'ORACLE_POOL_MIN', 1),
                max=getattr(self.config, 'ORACLE_POOL_MAX', 5),
                increment=getattr(self.config, 'ORACLE_POOL_INCREMENT', 1)
            )
            self._initialized = True
            return True
        except Exception as e:
            print(f"Failed to initialize Oracle connection pool: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool
        
        Yields:
            Oracle database connection
        """
        if not self._initialized:
            if not self.initialize():
                raise ConnectionError("Database not initialized. Check Oracle configuration.")
        
        connection = self._pool.acquire()
        try:
            yield connection
        finally:
            self._pool.release(connection)
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the database connection
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not ORACLEDB_AVAILABLE:
            return False, "oracledb package not installed"
        
        if not self.is_configured():
            return False, "Oracle database not configured"
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
                cursor.close()
                return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def execute_query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as list of dictionaries
        
        Args:
            sql: SQL query string (can contain :param_name placeholders)
            params: Dictionary of query parameters
            fetch_all: Whether to fetch all results
            
        Returns:
            List of dictionaries with column names as keys
        """
        if params is None:
            params = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Set query timeout if configured
            timeout = getattr(self.config, 'ORACLE_QUERY_TIMEOUT', 30)
            cursor.callTimeout = timeout * 1000  # Convert to milliseconds
            
            try:
                cursor.execute(sql, params)
                
                # Get column names
                columns = [col[0] for col in cursor.description] if cursor.description else []
                
                if fetch_all:
                    rows = cursor.fetchall()
                else:
                    rows = []
                
                # Convert to list of dictionaries
                result = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        # Handle special Oracle types
                        if hasattr(value, 'read'):  # LOB types
                            value = value.read()
                        row_dict[col] = value
                    result.append(row_dict)
                
                return result
                
            finally:
                cursor.close()
    
    def execute_query_with_metadata(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query and return results with metadata
        
        Returns:
            Dictionary with 'rows', 'columns', 'row_count' keys
        """
        if params is None:
            params = {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            timeout = getattr(self.config, 'ORACLE_QUERY_TIMEOUT', 30)
            cursor.callTimeout = timeout * 1000
            
            try:
                cursor.execute(sql, params)
                
                columns = []
                column_types = []
                
                if cursor.description:
                    for col in cursor.description:
                        columns.append(col[0])
                        column_types.append({
                            'name': col[0],
                            'type': str(col[1]),
                            'display_size': col[2],
                            'precision': col[4] if len(col) > 4 else None,
                            'scale': col[5] if len(col) > 5 else None
                        })
                
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                result_rows = []
                for row in rows:
                    row_dict = {}
                    for i, col in enumerate(columns):
                        value = row[i]
                        if hasattr(value, 'read'):
                            value = value.read()
                        row_dict[col] = value
                    result_rows.append(row_dict)
                
                return {
                    'rows': result_rows,
                    'columns': columns,
                    'column_metadata': column_types,
                    'row_count': len(result_rows)
                }
                
            finally:
                cursor.close()
    
    def parse_query_params(self, sql: str) -> List[str]:
        """
        Parse a SQL query to find named parameters
        
        Args:
            sql: SQL query string with :param_name placeholders
            
        Returns:
            List of parameter names found in the query
        """
        # Match :param_name but not ::type_cast or strings
        pattern = r':([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(pattern, sql)
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique.append(match)
        return unique
    
    def close(self):
        """Close the connection pool"""
        if self._pool:
            self._pool.close()
            self._pool = None
            self._initialized = False


# Singleton instance for the application
_db_service: Optional[DatabaseService] = None


def get_database_service(config) -> DatabaseService:
    """
    Get or create the database service singleton
    
    Args:
        config: Configuration object
        
    Returns:
        DatabaseService instance
    """
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService(config)
    return _db_service
