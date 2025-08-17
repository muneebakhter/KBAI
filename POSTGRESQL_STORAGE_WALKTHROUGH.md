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
- `vector_embeddings`: Vector storage with pgvector support
- `attachments`: Document storage with base64-encoded content

## Configuration

### 1. Environment Variables

Create or update your `.env` file:

```bash
# Database backend
DB_BACKEND=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kbai
DB_USER=kbai_user
DB_PASSWORD=kbai_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Vector storage (use PostgreSQL for pgvector support)
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=kbai
VECTOR_DB_USER=kbai_user
VECTOR_DB_PASSWORD=kbai_password

# Attachment storage (use PostgreSQL for base64 document storage)
ATTACHMENT_STORAGE=postgresql

# Other settings
DATA_DIR=./data
OPENAI_API_KEY=your_openai_api_key_here
```

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