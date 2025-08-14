from __future__ import annotations
import os
import json
import sqlite3
import threading
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from contextlib import contextmanager

# Database interface abstractions
class DatabaseInterface(ABC):
    """Abstract base class for database operations."""
    
    @abstractmethod
    def execute(self, sql: str, params: Tuple = ()) -> None:
        """Execute a SQL statement with parameters."""
        pass
    
    @abstractmethod
    def executemany(self, sql: str, rows: Iterable[Tuple]) -> None:
        """Execute a SQL statement multiple times with different parameters."""
        pass
    
    @abstractmethod
    def query(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass


class SQLiteDatabase(DatabaseInterface):
    """SQLite database implementation."""
    
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()
    
    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute(self, sql: str, params: Tuple = ()) -> None:
        with self._lock:
            with self.connect() as c:
                c.execute(sql, params)
                c.commit()
    
    def executemany(self, sql: str, rows: Iterable[Tuple]) -> None:
        with self._lock:
            with self.connect() as c:
                c.executemany(sql, rows)
                c.commit()
    
    def query(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        with self._lock:
            with self.connect() as c:
                cur = c.execute(sql, params)
                rows = cur.fetchall()
                # Convert sqlite3.Row objects to dictionaries
                return [dict(row) for row in rows]
    
    def close(self) -> None:
        # SQLite connections are closed automatically
        pass


class PostgreSQLDatabase(DatabaseInterface):
    """PostgreSQL database implementation."""
    
    def __init__(self, host: str, port: int, database: str, user: str, password: str, 
                 pool_size: int = 10, max_overflow: int = 20):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._pool = None
        self._lock = threading.RLock()
        
        # Import psycopg2 here to make it optional
        try:
            import psycopg2
            import psycopg2.pool
            import psycopg2.extras
            self.psycopg2 = psycopg2
            self.psycopg2_pool = psycopg2.pool
            self.psycopg2_extras = psycopg2.extras
        except ImportError:
            raise ImportError("psycopg2-binary is required for PostgreSQL support. Install with: pip install psycopg2-binary")
        
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            self._pool = self.psycopg2_pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.pool_size + self.max_overflow,
                **self.connection_params
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize PostgreSQL connection pool: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        if not self._pool:
            raise ConnectionError("Database pool not initialized")
        
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def execute(self, sql: str, params: Tuple = ()) -> None:
        with self._lock:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    conn.commit()
    
    def executemany(self, sql: str, rows: Iterable[Tuple]) -> None:
        with self._lock:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.executemany(sql, list(rows))
                    conn.commit()
    
    def query(self, sql: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        with self._lock:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=self.psycopg2_extras.RealDictCursor) as cur:
                    cur.execute(sql, params)
                    rows = cur.fetchall()
                    # Convert RealDictRow objects to regular dictionaries
                    return [dict(row) for row in rows]
    
    def close(self) -> None:
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()


def create_database_interface(backend: str = None, **kwargs) -> DatabaseInterface:
    """Factory function to create database interface based on configuration."""
    
    if backend is None:
        backend = os.getenv('DB_BACKEND', 'sqlite').lower()
    
    if backend == 'sqlite':
        db_path = kwargs.get('path') or os.getenv('TRACE_DB_PATH', './app/kbai_api.db')
        return SQLiteDatabase(db_path)
    
    elif backend == 'postgresql':
        host = kwargs.get('host') or os.getenv('DB_HOST', 'localhost')
        port = int(kwargs.get('port') or os.getenv('DB_PORT', 5432))
        database = kwargs.get('database') or os.getenv('DB_NAME', 'kbai')
        user = kwargs.get('user') or os.getenv('DB_USER', 'kbai_user')
        password = kwargs.get('password') or os.getenv('DB_PASSWORD', 'kbai_password')
        pool_size = int(kwargs.get('pool_size') or os.getenv('DB_POOL_SIZE', 10))
        max_overflow = int(kwargs.get('max_overflow') or os.getenv('DB_MAX_OVERFLOW', 20))
        
        return PostgreSQLDatabase(
            host=host,
            port=port, 
            database=database,
            user=user,
            password=password,
            pool_size=pool_size,
            max_overflow=max_overflow
        )
    
    else:
        raise ValueError(f"Unsupported database backend: {backend}")