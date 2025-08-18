# PostgreSQL Document Storage with pgvector Walkthrough

This walkthrough explains how to set up and use PostgreSQL for document storage with base64 encoding and pgvector for enhanced vector operations in the KBAI system.

## Overview

Instead of storing documents in the file system, S3, or Google Drive, this implementation stores documents directly in PostgreSQL as base64-encoded content. This approach provides several benefits:

- **Centralized Storage**: All data (metadata, documents, embeddings) in one database
- **ACID Compliance**: Full transactional support for document operations
- **Backup Simplicity**: Single database backup covers all data
- **Enhanced Security**: Database-level access controls and encryption
- **Performance**: Reduced I/O operations and better caching

## Prerequisites

### 1. PostgreSQL Installation

Install PostgreSQL 12 or higher:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib

# macOS (using Homebrew)
brew install postgresql

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Install pgvector Extension

Install pgvector for vector operations:

```bash
# Ubuntu/Debian
sudo apt install postgresql-12-pgvector  # Replace 12 with your PostgreSQL version

# From source (if package not available)
git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

### 3. Install pgvectorscale (Optional)

For enhanced performance, install pgvectorscale (currently in development):

```bash
# This is currently not available in pip, but will be in the future
# The schema supports it when available
```

## Database Setup

### 1. Create Database and User

Connect to PostgreSQL as superuser and create the database:

```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Create database
CREATE DATABASE kbai;

-- Create user
CREATE USER kbai_user WITH PASSWORD 'kbai_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE kbai TO kbai_user;

-- Switch to the KBAI database
\c kbai

-- Grant additional privileges
GRANT ALL ON SCHEMA public TO kbai_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kbai_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kbai_user;
```

### 2. Enable Extensions

Enable required extensions:

```sql
-- Enable pgvector extension (required)
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable pgvectorscale extension (optional, when available)
-- CREATE EXTENSION IF NOT EXISTS vectorscale;

-- Verify extensions
\dx
```

### 3. Initialize Schema

Run the PostgreSQL schema initialization:

```bash
cd /path/to/KBAI
psql -h localhost -U kbai_user -d kbai -f app/schema_postgresql.sql
```

This creates the following tables:
- `sessions`: Authentication sessions
- `traces`: Request logging  
- `projects`: Project mappings (replaces proj_mapping.txt)
- `faqs`: FAQ entries (replaces JSON files)
- `kb_articles`: Knowledge Base articles (replaces JSON files)
- `vector_embeddings`: Vector storage with pgvector support
- `attachments`: Document storage with base64-encoded content

**Schema Features:**
- Full PostgreSQL optimization with JSONB, GIN indexes, and foreign keys
- Automatic timestamp triggers for updated_at columns
- Cascade deletion for project-related content
- Full-text search indexes on content fields
- Vector similarity search with pgvector

### 4. Verify Schema Installation

Check that all tables were created successfully:

```sql
-- Connect to your database
psql -h localhost -U kbai_user -d kbai

-- List all tables
\dt

-- Verify specific tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Check extensions
\dx
```

You should see these tables:
- attachments
- faqs  
- kb_articles
- projects
- sessions
- traces
- vector_embeddings

## Configuration

### 1. Environment Variables

Create or update your `.env` file to use PostgreSQL for **ALL** data storage:

```bash
# =============================================================================
# Database Configuration  
# =============================================================================

# Database backend type: 'sqlite' or 'postgresql' (REQUIRED: postgresql)
DB_BACKEND=postgresql

# PostgreSQL database configuration for main data  
DB_HOST=192.168.56.1
DB_PORT=5432
DB_NAME=kbai
DB_USER=kbai_user
DB_PASSWORD=test_kbai
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Vector database configuration (use same PostgreSQL instance)
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=192.168.56.1
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=kbai_vectors  # Can be same as DB_NAME or separate
VECTOR_DB_USER=kbai_vector_user
VECTOR_DB_PASSWORD=test_kbai_vector

# Attachment storage configuration (REQUIRED: postgresql for complete storage)
ATTACHMENT_STORAGE=postgresql

# Other settings
DATA_DIR=./data  # Still used for temporary files and local fallback
OPENAI_API_KEY=your_openai_api_key_here
```

**Important Configuration Notes:**
- `DB_BACKEND=postgresql` is **required** for complete PostgreSQL storage
- `ATTACHMENT_STORAGE=postgresql` ensures all files are stored in the database  
- `VECTOR_STORAGE=postgresql` enables pgvector for embeddings
- You can use the same database for all components or separate databases

**What Gets Stored in PostgreSQL:**
- ✅ Project mappings (replaces `proj_mapping.txt`)
- ✅ FAQ entries (replaces local JSON files)
- ✅ Knowledge Base articles (replaces local JSON files)
- ✅ File attachments (base64-encoded, replaces file system storage)
- ✅ Vector embeddings (with pgvector)
- ✅ Request traces and session data

### 2. Python Dependencies

Ensure required packages are installed:

```bash
pip install psycopg2-binary>=2.9.0 pgvector>=0.2.0
```

## Usage Examples

### 1. Document Storage

```python
from app.storage_interfaces import create_attachment_storage
from app.db_interfaces import create_database_interface

# Create database interface
db_interface = create_database_interface(
    backend='postgresql',
    host='localhost',
    port=5432,
    database='kbai',
    user='kbai_user',
    password='kbai_password'
)

# Create attachment storage
storage = create_attachment_storage('postgresql', db_interface=db_interface)

# Store a document
with open('document.pdf', 'rb') as f:
    content = f.read()

file_id = storage.store_file(
    project_id="my_project",
    content_type="document",
    content_id="doc_123",
    filename="document.pdf",
    content=content,
    mime_type="application/pdf"
)

# Retrieve the document
retrieved_content, mime_type, original_filename = storage.retrieve_file(
    project_id="my_project",
    file_id=file_id
)

# List all documents
files = storage.list_files(project_id="my_project")
```

### 2. Vector Operations

```python
from app.storage_interfaces import create_vector_storage

# Create vector storage
vector_storage = create_vector_storage('postgresql', db_interface=db_interface)

# Store an embedding
embedding = [0.1, 0.2, 0.3, ...]  # Your 1536-dimensional embedding
embedding_id = vector_storage.store_embedding(
    project_id="my_project",
    content_type="document",
    content_id="doc_123",
    title="Important Document",
    content="Document content for search",
    embedding=embedding,
    metadata={"author": "John Doe", "category": "technical"}
)

# Search similar documents
query_embedding = [0.15, 0.25, 0.35, ...]  # Query embedding
results = vector_storage.search_similar(
    project_id="my_project",
    query_embedding=query_embedding,
    limit=10,
    threshold=0.7
)

for result in results:
    print(f"Document: {result['title']}")
    print(f"Similarity: {result['similarity']}")
    print(f"Content: {result['content'][:100]}...")
```

## Performance Optimization

### 1. Database Indexes

The schema automatically creates optimized indexes:

```sql
-- Vector similarity search indexes
CREATE INDEX idx_vector_embeddings_vector ON vector_embeddings 
    USING ivfflat (embedding vector_cosine_ops);

-- Attachment lookup indexes
CREATE INDEX idx_attachments_file_id ON attachments(file_id);
CREATE INDEX idx_attachments_project ON attachments(project_id);
```

### 2. pgvector Optimization

Configure pgvector for better performance:

```sql
-- Adjust ivfflat parameters for your dataset size
-- For datasets with > 1M vectors, increase lists parameter
ALTER INDEX idx_vector_embeddings_vector SET (lists = 1000);

-- Set effective_cache_size for better query planning
SET effective_cache_size = '4GB';  -- Adjust based on available RAM
```

### 3. Connection Pooling

The implementation uses connection pooling automatically:

```python
# Connection pool settings in .env
DB_POOL_SIZE=20        # Number of connections in pool
DB_MAX_OVERFLOW=30     # Additional connections if pool exhausted
```

## Monitoring and Maintenance

### 1. Monitor Storage Usage

Check database size and table usage:

```sql
-- Database size
SELECT pg_size_pretty(pg_database_size('kbai')) as database_size;

-- Table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Attachment storage statistics
SELECT 
    COUNT(*) as total_files,
    pg_size_pretty(SUM(file_size)) as total_size,
    AVG(file_size) as avg_file_size
FROM attachments;
```

### 2. Performance Monitoring

Monitor vector search performance:

```sql
-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('vector_embeddings', 'attachments');

-- Slow query monitoring
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
WHERE query LIKE '%vector_embeddings%' OR query LIKE '%attachments%'
ORDER BY mean_time DESC;
```

### 3. Backup Strategy

Regular backup procedures:

```bash
# Full database backup
pg_dump -h localhost -U kbai_user -d kbai > kbai_backup_$(date +%Y%m%d).sql

# Compressed backup
pg_dump -h localhost -U kbai_user -d kbai | gzip > kbai_backup_$(date +%Y%m%d).sql.gz

# Restore from backup
psql -h localhost -U kbai_user -d kbai_restored < kbai_backup_20231201.sql
```

## Migration from File System

To migrate existing documents from file system to PostgreSQL:

```python
import os
import base64
from pathlib import Path

def migrate_documents_to_postgresql():
    """Migrate documents from file system to PostgreSQL storage."""
    
    # Initialize PostgreSQL storage
    storage = create_attachment_storage('postgresql', db_interface=db_interface)
    
    # Migrate from local storage
    data_dir = Path('./data')
    for project_dir in data_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        project_id = project_dir.name
        attachments_dir = project_dir / 'attachments'
        
        if not attachments_dir.exists():
            continue
            
        # Load metadata
        metadata_file = attachments_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            for file_id, file_meta in metadata.items():
                file_path = attachments_dir / file_meta['filename']
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Store in PostgreSQL
                    new_file_id = storage.store_file(
                        project_id=project_id,
                        content_type=file_meta['content_type'],
                        content_id=file_meta['content_id'],
                        filename=file_meta['original_filename'],
                        content=content,
                        mime_type=file_meta.get('mime_type')
                    )
                    
                    print(f"Migrated {file_path} -> PostgreSQL (ID: {new_file_id})")

# Run migration
migrate_documents_to_postgresql()
```

## Troubleshooting

### Common Issues

1. **Extension not found**: Ensure pgvector is properly installed
2. **Permission denied**: Check database user privileges
3. **Connection pool exhausted**: Increase pool size or check for connection leaks
4. **Large documents**: Consider file size limits and tune PostgreSQL settings

### Configuration Tuning

For large document storage, adjust PostgreSQL settings:

```sql
-- Increase max_wal_size for large transactions
ALTER SYSTEM SET max_wal_size = '2GB';

-- Increase shared_buffers for better caching
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work_mem for large sorts
ALTER SYSTEM SET work_mem = '256MB';

-- Reload configuration
SELECT pg_reload_conf();
```

## Benefits of This Approach

1. **Simplified Architecture**: Single database for all data
2. **ACID Transactions**: Consistent document and metadata operations
3. **Enhanced Security**: Database-level encryption and access control
4. **Better Performance**: Optimized queries across documents and vectors
5. **Simplified Backup**: Single backup operation for all data
6. **Scalability**: PostgreSQL's proven scalability for large datasets

This implementation provides a robust, performant solution for document storage with advanced vector search capabilities using PostgreSQL and pgvector.

## Testing Complete PostgreSQL Storage

### 1. Start the API Server

```bash
cd /path/to/KBAI
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

You should see output confirming PostgreSQL backend:
```
Starting KBAI API server...
Loading environment variables from .env
Using postgresql database backend
📚 API Documentation will be available at:
   Swagger UI: http://0.0.0.0:8000/docs
```

### 2. Test Project Management

Create a test project:
```bash
# Create project
curl -X POST "http://localhost:8000/v1/projects" \
  -H "Content-Type: application/json" \
  -d '{"id": "test_proj", "name": "Test Project", "active": true}'

# List projects (should show database storage)
curl "http://localhost:8000/v1/projects"

# Verify no proj_mapping.txt file is created
ls data/proj_mapping.txt  # Should not exist or be empty
```

### 3. Test FAQ Management

```bash
# Add FAQ
curl -X POST "http://localhost:8000/v1/projects/test_proj/faqs:batch_upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{
      "id": "faq_1",
      "question": "What is PostgreSQL storage?",
      "answer": "Complete database storage for all content.",
      "tags": ["database", "storage"]
    }]
  }'

# List FAQs (should show database storage)
curl "http://localhost:8000/v1/projects/test_proj/faqs"

# Verify no local JSON files are created
ls data/test_proj/faqs/  # Should not exist or be empty
```

### 4. Test Knowledge Base Management

```bash
# Add KB article
curl -X POST "http://localhost:8000/v1/projects/test_proj/kb:batch_upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [{
      "id": "kb_1", 
      "title": "PostgreSQL Benefits",
      "content": "PostgreSQL provides ACID compliance, full-text search, and vector operations.",
      "tags": ["database", "benefits"]
    }]
  }'

# List KB articles (should show database storage)
curl "http://localhost:8000/v1/projects/test_proj/kb"

# Verify no local JSON files are created
ls data/test_proj/kb/  # Should not exist or be empty
```

### 5. Verify Database Content

Connect to PostgreSQL and verify data is stored in tables:

```sql
-- Connect to database
psql -h localhost -U kbai_user -d kbai

-- Check projects
SELECT * FROM projects;

-- Check FAQs
SELECT id, question, LEFT(answer, 50) as answer_preview FROM faqs;

-- Check KB articles
SELECT id, title, LEFT(content, 50) as content_preview FROM kb_articles;

-- Check traces (if any requests made)
SELECT method, path, status, ts FROM traces ORDER BY ts DESC LIMIT 5;
```

### 6. Verify No Local File Storage

With complete PostgreSQL storage, these directories should be empty or non-existent:
```bash
# These should not contain project data
ls data/proj_mapping.txt  # Should not exist
ls data/test_proj/faqs/   # Should be empty
ls data/test_proj/kb/     # Should be empty
```

The `data/` directory may still exist for temporary files and AI worker indexes, but project content should be in the database.

## Troubleshooting

### Common Issues

1. **Connection Errors**: Verify PostgreSQL is running and accessible
2. **Permission Errors**: Check user privileges on database and tables  
3. **Extension Errors**: Ensure pgvector extension is installed
4. **Schema Errors**: Re-run schema initialization if tables are missing

### Debug SQL Queries

Enable SQL logging to debug issues:
```bash
# Add to .env for debugging
DB_DEBUG=true
```

This will log all SQL queries to help identify issues.