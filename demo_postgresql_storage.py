#!/usr/bin/env python3
"""
Demonstration script for PostgreSQL document storage with base64 encoding.
This script shows how to use the new PostgreSQL storage capabilities.
"""

import os
import sys
import base64
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demonstrate_postgresql_storage():
    """Demonstrate PostgreSQL document storage capabilities."""
    print("🎯 PostgreSQL Document Storage Demonstration")
    print("=" * 60)
    
    try:
        from app.storage_interfaces import create_attachment_storage, create_vector_storage
        
        # Create mock database interface for demonstration
        class DemoDatabase:
            def __init__(self):
                self.attachments = {}
                self.vectors = {}
                self.next_id = 1
            
            def execute(self, sql: str, params: tuple = ()):
                sql_normalized = ' '.join(sql.split())
                if "INSERT INTO attachments" in sql_normalized:
                    file_id = params[0]
                    self.attachments[file_id] = {
                        'id': self.next_id,
                        'file_id': file_id,
                        'project_id': params[1],
                        'content_type': params[2],
                        'content_id': params[3],
                        'filename': params[4],
                        'original_filename': params[5],
                        'mime_type': params[6],
                        'file_size': params[7],
                        'file_content_base64': params[8],
                        'storage_backend': 'postgresql'
                    }
                    self.next_id += 1
                elif "INSERT INTO vector_embeddings" in sql_normalized:
                    key = f"{params[0]}_{params[1]}_{params[2]}"
                    self.vectors[key] = {
                        'id': self.next_id,
                        'project_id': params[0],
                        'content_type': params[1],
                        'content_id': params[2],
                        'title': params[3],
                        'content': params[4],
                        'embedding': params[5],
                        'metadata': params[6]
                    }
                    self.next_id += 1
            
            def query(self, sql: str, params: tuple = ()):
                sql_normalized = ' '.join(sql.split())
                if "SELECT 1 FROM" in sql_normalized:
                    return [{'1': 1}]
                elif "SELECT file_content_base64" in sql_normalized:
                    project_id, file_id = params
                    for att in self.attachments.values():
                        if att['project_id'] == project_id and att['file_id'] == file_id:
                            return [{
                                'file_content_base64': att['file_content_base64'],
                                'mime_type': att['mime_type'],
                                'original_filename': att['original_filename']
                            }]
                    return []
                elif "SELECT id FROM vector_embeddings WHERE project_id" in sql_normalized and len(params) == 3:
                    key = f"{params[0]}_{params[1]}_{params[2]}"
                    if key in self.vectors:
                        return [{'id': self.vectors[key]['id']}]
                    return []
                elif "1 - (embedding <=> " in sql_normalized:
                    project_id = params[1]
                    return [v for v in self.vectors.values() if v['project_id'] == project_id]
                return []
        
        demo_db = DemoDatabase()
        
        # 1. Document Storage Demo
        print("\n📄 Document Storage with Base64 Encoding")
        print("-" * 50)
        
        attachment_storage = create_attachment_storage('postgresql', db_interface=demo_db)
        
        # Create sample document content
        sample_document = """# Sample Technical Document
        
This is a sample technical document that demonstrates how documents
are stored in PostgreSQL using base64 encoding.

## Key Features:
- Base64 encoding for binary safety
- Full transactional support
- Centralized storage
- Enhanced security

The document content is automatically encoded and can contain any
binary data including PDFs, images, and other file types.
"""
        
        document_bytes = sample_document.encode('utf-8')
        
        # Store the document
        file_id = attachment_storage.store_file(
            project_id="demo_project",
            content_type="document",
            content_id="doc_001",
            filename="technical_spec.md",
            content=document_bytes,
            mime_type="text/markdown"
        )
        
        print(f"✅ Document stored with ID: {file_id}")
        print(f"   Original size: {len(document_bytes)} bytes")
        
        # Verify base64 encoding
        stored_attachment = demo_db.attachments[file_id]
        base64_content = stored_attachment['file_content_base64']
        print(f"   Base64 encoded size: {len(base64_content)} bytes")
        print(f"   Compression ratio: {len(base64_content)/len(document_bytes):.2f}x")
        
        # Retrieve the document
        retrieved_content, mime_type, original_filename = attachment_storage.retrieve_file(
            project_id="demo_project",
            file_id=file_id
        )
        
        print(f"✅ Document retrieved successfully")
        print(f"   MIME type: {mime_type}")
        print(f"   Original filename: {original_filename}")
        print(f"   Content integrity: {'✅ VERIFIED' if retrieved_content == document_bytes else '❌ FAILED'}")
        
        # 2. Vector Storage Demo
        print("\n🔍 Vector Storage with pgvector")
        print("-" * 50)
        
        vector_storage = create_vector_storage('postgresql', db_interface=demo_db)
        
        # Create sample embeddings (simulating OpenAI embeddings)
        sample_embeddings = {
            "AI and Machine Learning": [0.8, 0.2, 0.1, 0.7, 0.3],
            "Database Systems": [0.3, 0.9, 0.4, 0.2, 0.8],
            "Web Development": [0.1, 0.4, 0.9, 0.6, 0.2]
        }
        
        # Store embeddings
        embedding_ids = []
        for i, (title, embedding) in enumerate(sample_embeddings.items()):
            embedding_id = vector_storage.store_embedding(
                project_id="demo_project",
                content_type="document",
                content_id=f"doc_{i+1:03d}",
                title=title,
                content=f"This document covers {title} concepts and implementations.",
                embedding=embedding,
                metadata={"category": title.split()[0].lower(), "index": i}
            )
            embedding_ids.append(embedding_id)
            print(f"✅ Stored embedding for '{title}' (ID: {embedding_id})")
        
        # Demonstrate similarity search
        query_embedding = [0.5, 0.6, 0.7, 0.4, 0.5]  # Mixed query
        results = vector_storage.search_similar(
            project_id="demo_project",
            query_embedding=query_embedding,
            limit=3,
            threshold=0.0
        )
        
        print(f"\n🎯 Similarity search results for mixed query:")
        for result in results:
            print(f"   📖 {result['title']}")
            print(f"      Content: {result['content']}")
            print(f"      Metadata: {result['metadata']}")
        
        # 3. Storage Statistics
        print("\n📊 Storage Statistics")
        print("-" * 50)
        
        total_documents = len(demo_db.attachments)
        total_vectors = len(demo_db.vectors)
        total_base64_size = sum(len(att['file_content_base64']) for att in demo_db.attachments.values())
        
        print(f"📄 Total documents stored: {total_documents}")
        print(f"🔍 Total vector embeddings: {total_vectors}")
        print(f"💾 Total base64 content size: {total_base64_size} bytes")
        print(f"🏗️ Storage backend: PostgreSQL with base64 encoding")
        print(f"🎯 Vector engine: pgvector with cosine similarity")
        
        # 4. Configuration Summary
        print("\n⚙️ Configuration for Production Use")
        print("-" * 50)
        
        config_example = """
# .env configuration for PostgreSQL storage
DB_BACKEND=postgresql
DB_HOST=localhost
DB_NAME=kbai
DB_USER=kbai_user
DB_PASSWORD=your_secure_password

# Use PostgreSQL for both vector and attachment storage
VECTOR_STORAGE=postgresql
ATTACHMENT_STORAGE=postgresql

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
"""
        
        print(config_example)
        
        print("✅ PostgreSQL document storage demonstration completed successfully!")
        print("\n📖 For detailed setup instructions, see: POSTGRESQL_STORAGE_WALKTHROUGH.md")
        
        return True
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_benefits():
    """Show the benefits of PostgreSQL storage over file system storage."""
    print("\n🎉 Benefits of PostgreSQL Document Storage")
    print("=" * 60)
    
    benefits = [
        ("🎯 Centralized Storage", "All data (metadata, documents, vectors) in single database"),
        ("🔒 ACID Compliance", "Full transactional support for document operations"),
        ("💾 Simplified Backup", "Single database backup covers all application data"),
        ("🛡️ Enhanced Security", "Database-level access controls and encryption"),
        ("⚡ Performance", "Reduced I/O operations and better caching"),
        ("🔍 Advanced Queries", "SQL joins between documents, metadata, and vectors"),
        ("📈 Scalability", "PostgreSQL's proven scalability for large datasets"),
        ("🔧 Maintenance", "Single system to monitor, tune, and maintain"),
        ("🌐 Consistency", "Consistent data access patterns across all components"),
        ("🚀 pgvector Integration", "Native vector operations with similarity search")
    ]
    
    for title, description in benefits:
        print(f"{title:<25} {description}")


def main():
    """Run the complete demonstration."""
    if demonstrate_postgresql_storage():
        show_benefits()
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())