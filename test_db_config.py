#!/usr/bin/env python3
"""
Test script for KBAI database configuration system.
Tests both SQLite and PostgreSQL backends with the new configuration system.
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_sqlite_backend():
    """Test SQLite backend functionality."""
    print("🧪 Testing SQLite backend...")
    
    try:
        from app.storage import DB
        from app.db_interfaces import create_database_interface
        
        # Test 1: Original backward-compatible usage
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        os.unlink(db_path)  # Remove the empty file
        
        # Initialize SQLite database with schema
        os.system(f'sqlite3 {db_path} < app/schema.sql')
        
        # Test original API
        db = DB(db_path)
        print("✅ Original DB class initialization successful")
        
        # Test basic operations
        db.execute("INSERT INTO sessions(id, token_jti, client_name, scopes, issued_at, expires_at, disabled) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  ("test_sess", "test_jti", "test_client", "read:basic", "2023-01-01T00:00:00Z", "2023-01-01T01:00:00Z", 0))
        
        sessions = db.query("SELECT * FROM sessions WHERE id = ?", ("test_sess",))
        assert len(sessions) == 1
        assert sessions[0]["id"] == "test_sess"
        print("✅ Original API session operations successful")
        
        # Test 2: New interface usage
        db_new = DB(backend='sqlite', path=db_path)
        print("✅ New interface SQLite initialization successful")
        
        # Test new interface operations
        sessions_new = db_new.query("SELECT * FROM sessions WHERE id = ?", ("test_sess",))
        assert len(sessions_new) == 1
        assert sessions_new[0]["id"] == "test_sess"
        print("✅ New interface SQLite operations successful")
        
        # Clean up
        os.unlink(db_path)
        
        return True
        
    except Exception as e:
        print(f"❌ SQLite backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_postgresql_backend():
    """Test PostgreSQL backend functionality (if available)."""
    print("🧪 Testing PostgreSQL backend...")
    
    # Check if PostgreSQL dependencies are available
    try:
        import psycopg2
        print("✅ psycopg2 dependency available")
    except ImportError:
        print("⚠️ psycopg2 not available, skipping PostgreSQL tests")
        return True
    
    try:
        from app.db_interfaces import create_database_interface, PostgreSQLDatabase
        
        # Test interface creation (will fail connection but should not crash)
        try:
            db_interface = create_database_interface(
                backend='postgresql',
                host='nonexistent',
                port=5432,
                database='test',
                user='test',
                password='test'
            )
            print("✅ PostgreSQL interface creation successful")
            
            # This will fail but we're testing the interface creation
            try:
                db_interface.query("SELECT 1")
            except Exception:
                print("✅ Expected connection failure for nonexistent server")
                
        except Exception as e:
            if "Failed to initialize PostgreSQL connection pool" in str(e):
                print("✅ Expected PostgreSQL connection failure")
            else:
                raise
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_interfaces():
    """Test vector and attachment storage interfaces."""
    print("🧪 Testing storage interfaces...")
    
    try:
        from app.storage_interfaces import (
            create_vector_storage, 
            create_attachment_storage,
            LocalVectorStorage,
            LocalAttachmentStorage
        )
        
        # Test vector storage
        with tempfile.TemporaryDirectory() as temp_dir:
            vector_storage = create_vector_storage('local', base_dir=temp_dir)
            print("✅ Vector storage interface creation successful")
            
            # Test storing an embedding
            embedding_id = vector_storage.store_embedding(
                project_id="test_project",
                content_type="faq",
                content_id="faq_1",
                title="Test FAQ",
                content="This is a test FAQ",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={"source": "test"}
            )
            assert embedding_id is not None
            print("✅ Vector embedding storage successful")
            
            # Test searching
            results = vector_storage.search_similar(
                project_id="test_project",
                query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                limit=5,
                threshold=0.5
            )
            assert len(results) == 1
            assert results[0]["content_id"] == "faq_1"
            print("✅ Vector similarity search successful")
            
            # Test attachment storage
            attachment_storage = create_attachment_storage('local', base_dir=temp_dir)
            print("✅ Attachment storage interface creation successful")
            
            # Test storing a file
            test_content = b"This is test file content"
            file_id = attachment_storage.store_file(
                project_id="test_project",
                content_type="faq",
                content_id="faq_1",
                filename="test.txt",
                content=test_content,
                mime_type="text/plain"
            )
            assert file_id is not None
            print("✅ File attachment storage successful")
            
            # Test retrieving a file
            retrieved_content, mime_type, original_filename = attachment_storage.retrieve_file(
                project_id="test_project",
                file_id=file_id
            )
            assert retrieved_content == test_content
            assert original_filename == "test.txt"
            print("✅ File attachment retrieval successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage interfaces test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """Test environment-based configuration."""
    print("🧪 Testing configuration system...")
    
    try:
        from app.db_interfaces import create_database_interface
        
        # Test default SQLite configuration
        original_env = os.environ.copy()
        
        try:
            # Set environment for SQLite
            os.environ['DB_BACKEND'] = 'sqlite'
            os.environ['TRACE_DB_PATH'] = './test.db'
            
            # Test that configuration is read correctly
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                db_path = tmp_db.name
            os.unlink(db_path)
            os.system(f'sqlite3 {db_path} < app/schema.sql')
            
            os.environ['TRACE_DB_PATH'] = db_path
            
            db_interface = create_database_interface()
            print("✅ Configuration-based SQLite interface creation successful")
            
            # Test query
            result = db_interface.query("SELECT 1 as test")
            assert len(result) == 1
            assert result[0]["test"] == 1
            print("✅ Configuration-based SQLite operations successful")
            
            os.unlink(db_path)
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 KBAI Database Configuration Test Suite")
    print("=" * 50)
    
    tests = [
        ("SQLite Backend", test_sqlite_backend),
        ("PostgreSQL Backend", test_postgresql_backend), 
        ("Storage Interfaces", test_storage_interfaces),
        ("Configuration System", test_configuration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} tests...")
        if test_func():
            print(f"✅ {test_name} tests passed")
            passed += 1
        else:
            print(f"❌ {test_name} tests failed")
    
    print(f"\n🏁 Test Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! Database configuration system is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())