#!/usr/bin/env python3
"""
Test script for PostgreSQL-based document and vector storage.
Tests the new PostgreSQL attachment storage with base64 encoding and pgvector support.
"""

import os
import sys
import tempfile
import json
import base64
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_postgresql_attachment_storage():
    """Test PostgreSQL attachment storage with base64 encoding."""
    print("🧪 Testing PostgreSQL attachment storage...")
    
    # Check if PostgreSQL dependencies are available
    try:
        import psycopg2
        print("✅ psycopg2 dependency available")
    except ImportError:
        print("⚠️ psycopg2 not available, skipping PostgreSQL storage tests")
        return True
    
    try:
        from app.storage_interfaces import PostgreSQLAttachmentStorage
        from app.db_interfaces import create_database_interface
        
        # Create a mock database interface for testing
        class MockPostgreSQLDatabase:
            def __init__(self):
                self.data = {}
                self.counter = 1
            
            def execute(self, sql: str, params: tuple = ()):
                if "INSERT INTO attachments" in sql:
                    # Mock insert operation
                    file_id = params[0]
                    self.data[file_id] = {
                        'id': self.counter,
                        'file_id': params[0],
                        'project_id': params[1],
                        'content_type': params[2],
                        'content_id': params[3],
                        'filename': params[4],
                        'original_filename': params[5],
                        'mime_type': params[6],
                        'file_size': params[7],
                        'file_content_base64': params[8],
                        'storage_backend': 'postgresql',
                        'metadata': json.loads(params[9] if params[9] else '{}'),
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                    self.counter += 1
                elif "DELETE FROM attachments" in sql:
                    # Mock delete operation
                    project_id, file_id = params
                    for key, value in list(self.data.items()):
                        if value['project_id'] == project_id and value['file_id'] == file_id:
                            del self.data[key]
                            break
            
            def query(self, sql: str, params: tuple = ()):
                if "SELECT 1 FROM attachments LIMIT 1" in sql:
                    return [{'1': 1}]  # Table exists
                elif "SELECT file_content_base64, mime_type, original_filename" in sql:
                    project_id, file_id = params
                    for value in self.data.values():
                        if value['project_id'] == project_id and value['file_id'] == file_id:
                            return [{
                                'file_content_base64': value['file_content_base64'],
                                'mime_type': value['mime_type'],
                                'original_filename': value['original_filename']
                            }]
                    return []
                elif "SELECT id FROM attachments WHERE project_id" in sql:
                    project_id, file_id = params
                    for value in self.data.values():
                        if value['project_id'] == project_id and value['file_id'] == file_id:
                            return [{'id': value['id']}]
                    return []
                elif "SELECT file_id, project_id" in sql:
                    if len(params) == 2:  # With content_type filter
                        project_id, content_type = params
                        return [v for v in self.data.values() 
                               if v['project_id'] == project_id and v['content_type'] == content_type]
                    else:  # Without content_type filter
                        project_id = params[0]
                        return [v for v in self.data.values() if v['project_id'] == project_id]
                return []
        
        # Test with mock database
        mock_db = MockPostgreSQLDatabase()
        storage = PostgreSQLAttachmentStorage(mock_db)
        print("✅ PostgreSQL attachment storage interface creation successful")
        
        # Test storing a file
        test_content = b"This is test file content for PostgreSQL storage"
        file_id = storage.store_file(
            project_id="test_project",
            content_type="document",
            content_id="doc_1",
            filename="test_document.txt",
            content=test_content,
            mime_type="text/plain"
        )
        assert file_id is not None
        print("✅ PostgreSQL file attachment storage successful")
        
        # Verify content was base64 encoded
        stored_data = mock_db.data[file_id]
        expected_base64 = base64.b64encode(test_content).decode('utf-8')
        assert stored_data['file_content_base64'] == expected_base64
        print("✅ File content properly base64 encoded")
        
        # Test retrieving a file
        retrieved_content, mime_type, original_filename = storage.retrieve_file(
            project_id="test_project",
            file_id=file_id
        )
        assert retrieved_content == test_content
        assert original_filename == "test_document.txt"
        assert mime_type == "text/plain"
        print("✅ PostgreSQL file attachment retrieval successful")
        
        # Test listing files
        files = storage.list_files(project_id="test_project")
        assert len(files) == 1
        assert files[0]['file_id'] == file_id
        print("✅ PostgreSQL file listing successful")
        
        # Test listing files with content type filter
        files_filtered = storage.list_files(project_id="test_project", content_type="document")
        assert len(files_filtered) == 1
        print("✅ PostgreSQL file listing with filter successful")
        
        # Test deleting a file
        delete_result = storage.delete_file(project_id="test_project", file_id=file_id)
        assert delete_result is True
        print("✅ PostgreSQL file deletion successful")
        
        # Verify file is deleted
        files_after_delete = storage.list_files(project_id="test_project")
        assert len(files_after_delete) == 0
        print("✅ PostgreSQL file deletion verification successful")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL attachment storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_postgresql_vector_storage():
    """Test PostgreSQL vector storage with pgvector."""
    print("🧪 Testing PostgreSQL vector storage...")
    
    try:
        from app.storage_interfaces import PostgreSQLVectorStorage
        
        # Create a mock database interface for testing
        class MockPostgreSQLVectorDatabase:
            def __init__(self):
                self.data = {}
                self.counter = 1
            
            def execute(self, sql: str, params: tuple = ()):
                if "DELETE FROM vector_embeddings" in sql:
                    # Mock delete operation
                    project_id, content_type, content_id = params
                    for key, value in list(self.data.items()):
                        if (value['project_id'] == project_id and 
                            value['content_type'] == content_type and 
                            value['content_id'] == content_id):
                            del self.data[key]
                            break
                elif "INSERT INTO vector_embeddings" in sql:
                    # Mock insert operation
                    project_id, content_type, content_id, title, content, embedding_str, metadata_str = params
                    key = f"{project_id}_{content_type}_{content_id}"
                    self.data[key] = {
                        'id': self.counter,
                        'project_id': project_id,
                        'content_type': content_type,
                        'content_id': content_id,
                        'title': title,
                        'content': content,
                        'embedding': embedding_str,
                        'metadata': json.loads(metadata_str),
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                    self.counter += 1
            
            def query(self, sql: str, params: tuple = ()):
                # Normalize SQL by removing extra whitespace and newlines
                normalized_sql = ' '.join(sql.split())
                if "SELECT 1 FROM vector_embeddings LIMIT 1" in normalized_sql:
                    return [{'1': 1}]  # Table exists
                elif "SELECT id FROM vector_embeddings WHERE project_id" in normalized_sql and len(params) == 3:
                    project_id, content_type, content_id = params
                    for key, value in self.data.items():
                        if (value['project_id'] == project_id and 
                            value['content_type'] == content_type and 
                            value['content_id'] == content_id):
                            return [{'id': value['id']}]
                    return []
                elif "1 - (embedding <=> " in normalized_sql:
                    # Mock similarity search
                    query_embedding_str, project_id, _, threshold, _, limit = params
                    results = []
                    for value in self.data.values():
                        if value['project_id'] == project_id:
                            # Mock similarity calculation (always return 0.9 for testing)
                            result = value.copy()
                            result['similarity'] = 0.9
                            results.append(result)
                    return results[:limit]
                elif "SELECT id, project_id, content_type" in normalized_sql:
                    if len(params) == 2:  # With content_type filter
                        project_id, content_type = params
                        return [v for v in self.data.values() 
                               if v['project_id'] == project_id and v['content_type'] == content_type]
                    else:  # Without content_type filter
                        project_id = params[0]
                        return [v for v in self.data.values() if v['project_id'] == project_id]
                return []
        
        # Test with mock database
        mock_db = MockPostgreSQLVectorDatabase()
        storage = PostgreSQLVectorStorage(mock_db)
        print("✅ PostgreSQL vector storage interface creation successful")
        
        # Test storing an embedding
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        embedding_id = storage.store_embedding(
            project_id="test_project",
            content_type="faq",
            content_id="faq_1",
            title="Test FAQ",
            content="This is a test FAQ for vector storage",
            embedding=test_embedding,
            metadata={"source": "test"}
        )
        assert embedding_id is not None
        print("✅ PostgreSQL vector embedding storage successful")
        
        # Test similarity search
        results = storage.search_similar(
            project_id="test_project",
            query_embedding=test_embedding,
            limit=5,
            threshold=0.5
        )
        assert len(results) == 1
        assert results[0]['content_id'] == "faq_1"
        assert results[0]['similarity'] == 0.9
        print("✅ PostgreSQL vector similarity search successful")
        
        # Test getting embeddings
        embeddings = storage.get_embeddings(project_id="test_project")
        assert len(embeddings) == 1
        assert embeddings[0]['content_id'] == "faq_1"
        print("✅ PostgreSQL vector embeddings retrieval successful")
        
        # Test getting embeddings with content type filter
        embeddings_filtered = storage.get_embeddings(project_id="test_project", content_type="faq")
        assert len(embeddings_filtered) == 1
        print("✅ PostgreSQL vector embeddings retrieval with filter successful")
        
        # Test deleting an embedding
        delete_result = storage.delete_embedding(project_id="test_project", content_type="faq", content_id="faq_1")
        assert delete_result is True
        print("✅ PostgreSQL vector embedding deletion successful")
        
        # Verify embedding is deleted
        embeddings_after_delete = storage.get_embeddings(project_id="test_project")
        assert len(embeddings_after_delete) == 0
        print("✅ PostgreSQL vector embedding deletion verification successful")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL vector storage test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_storage_factories():
    """Test storage factory functions for PostgreSQL."""
    print("🧪 Testing PostgreSQL storage factories...")
    
    try:
        from app.storage_interfaces import create_vector_storage, create_attachment_storage
        
        # Mock database interface
        class MockDB:
            def query(self, sql, params=()):
                return [{'1': 1}]
            def execute(self, sql, params=()):
                pass
        
        mock_db = MockDB()
        
        # Test vector storage factory
        vector_storage = create_vector_storage('postgresql', db_interface=mock_db)
        assert vector_storage is not None
        print("✅ PostgreSQL vector storage factory successful")
        
        # Test attachment storage factory
        attachment_storage = create_attachment_storage('postgresql', db_interface=mock_db)
        assert attachment_storage is not None
        print("✅ PostgreSQL attachment storage factory successful")
        
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL storage factories test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all PostgreSQL storage tests."""
    print("🚀 PostgreSQL Document Storage Test Suite")
    print("=" * 50)
    
    tests = [
        ("PostgreSQL Attachment Storage", test_postgresql_attachment_storage),
        ("PostgreSQL Vector Storage", test_postgresql_vector_storage),
        ("Storage Factories", test_storage_factories),
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
        print("🎉 All PostgreSQL storage tests passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())