# Database Configuration Guide

This guide explains how to configure KBAI to use remote databases for scalability and redundancy.

## Overview

KBAI now supports multiple database backends:

- **SQLite** (default) - Single file database, perfect for development and small deployments
- **PostgreSQL** - Enterprise-grade database with connection pooling and advanced features
- **Vector Storage** - Configurable storage for embeddings (local files or PostgreSQL with pgvector)
- **Attachment Storage** - Configurable storage for file attachments

## Configuration

All database configuration is done through environment variables. Copy `.env.example` to `.env` and modify as needed.

### SQLite Configuration (Default)

```bash
# Use SQLite (default)
DB_BACKEND=sqlite
TRACE_DB_PATH=./app/kbai_api.db
```

### PostgreSQL Configuration

```bash
# Use PostgreSQL
DB_BACKEND=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kbai
DB_USER=kbai_user
DB_PASSWORD=kbai_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

### Vector Storage Configuration

```bash
# Local vector storage (default)
VECTOR_STORAGE=local

# PostgreSQL vector storage with pgvector
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=localhost
VECTOR_DB_PORT=5432
VECTOR_DB_NAME=kbai_vectors
VECTOR_DB_USER=kbai_vector_user
VECTOR_DB_PASSWORD=kbai_vector_password
```

### Attachment Storage Configuration

```bash
# Local file storage (default)
ATTACHMENT_STORAGE=local
ATTACHMENT_STORAGE_PATH=./data

# Future: S3, GCS, Azure Blob Storage support planned
```

## Database Setup

### PostgreSQL Setup

1. **Install PostgreSQL** (version 12+ recommended)

2. **Create Database and User**:
```sql
-- Connect as postgres superuser
CREATE DATABASE kbai;
CREATE USER kbai_user WITH PASSWORD 'kbai_password';
GRANT ALL PRIVILEGES ON DATABASE kbai TO kbai_user;

-- Optional: Create separate database for vectors
CREATE DATABASE kbai_vectors;
CREATE USER kbai_vector_user WITH PASSWORD 'kbai_vector_password';
GRANT ALL PRIVILEGES ON DATABASE kbai_vectors TO kbai_vector_user;
```

3. **Enable pgvector extension** (for vector storage):
```sql
-- Connect to your database
\c kbai_vectors
CREATE EXTENSION IF NOT EXISTS vector;
```

4. **Initialize Schema**:
```bash
# Set environment variables in .env
DB_BACKEND=postgresql
DB_HOST=localhost
# ... other PostgreSQL settings

# Run initialization script
./init_db_multi.sh
```

### SQLite Setup (Default)

```bash
# SQLite is the default, just run:
./init_db.sh
# or
./init_db_multi.sh
```

## Migration from SQLite to PostgreSQL

1. **Export existing SQLite data**:
```bash
# Export sessions
sqlite3 app/kbai_api.db "SELECT * FROM sessions;" > sessions_export.csv

# Export traces  
sqlite3 app/kbai_api.db "SELECT * FROM traces;" > traces_export.csv
```

2. **Set up PostgreSQL** (see above)

3. **Import data** (customize as needed):
```sql
-- Connect to PostgreSQL database
\copy sessions FROM 'sessions_export.csv' WITH CSV;
\copy traces FROM 'traces_export.csv' WITH CSV;
```

4. **Update configuration** to use PostgreSQL

5. **Restart application**

## High Availability Setup

For production deployments with multiple API instances:

### Option 1: Shared PostgreSQL Database

```bash
# Instance 1
DB_BACKEND=postgresql
DB_HOST=postgres.internal
DB_NAME=kbai_prod
# ... connection details

# Instance 2 (same configuration)
DB_BACKEND=postgresql  
DB_HOST=postgres.internal
DB_NAME=kbai_prod
# ... same connection details
```

### Option 2: PostgreSQL Cluster with Load Balancer

```bash
# All instances use load balancer endpoint
DB_BACKEND=postgresql
DB_HOST=postgres-cluster.internal  # Load balancer
DB_PORT=5432
DB_NAME=kbai_prod
```

### Vector Storage for Multiple Instances

```bash
# Shared PostgreSQL vector storage
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=postgres-vectors.internal
VECTOR_DB_NAME=kbai_vectors_prod

# Or shared file storage (NFS, EFS, etc.)
VECTOR_STORAGE=local
DATA_DIR=/shared/kbai/data  # Shared filesystem
```

## Connection Pooling

PostgreSQL backend includes built-in connection pooling:

```bash
# Pool configuration
DB_POOL_SIZE=10         # Minimum connections
DB_MAX_OVERFLOW=20      # Additional connections when needed
```

## Monitoring and Health Checks

The application provides health endpoints that check database connectivity:

- `/healthz` - Basic health check
- `/readyz` - Readiness check (includes database connectivity)
- `/admin` - Admin dashboard with database metrics

## Troubleshooting

### Connection Issues

1. **Check connectivity**:
```bash
# Test PostgreSQL connection
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1;"
```

2. **Check logs**:
```bash
# View application logs for database errors
./run_api.sh
```

3. **Test configuration**:
```bash
# Run configuration tests
python test_db_config.py
```

### Performance Issues

1. **Monitor connection pool**:
   - Check if `DB_POOL_SIZE` needs adjustment
   - Monitor connection usage in PostgreSQL

2. **Database optimization**:
   - Ensure proper indexes exist
   - Consider `VACUUM` and `ANALYZE` for PostgreSQL

3. **Vector search optimization**:
   - For PostgreSQL+pgvector: create proper vector indexes
   - For local storage: consider upgrading to PostgreSQL for large datasets

## Security Considerations

1. **Use strong passwords** for database users
2. **Enable SSL/TLS** for database connections
3. **Restrict network access** to database servers
4. **Use connection encryption** in production
5. **Regular security updates** for database software
6. **Backup and recovery** procedures

## Backup and Recovery

### PostgreSQL Backup

```bash
# Full database backup
pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > kbai_backup.sql

# Restore
psql -h $DB_HOST -U $DB_USER $DB_NAME < kbai_backup.sql
```

### SQLite Backup

```bash
# Simple file copy
cp app/kbai_api.db app/kbai_api.db.backup

# Or use SQLite backup command
sqlite3 app/kbai_api.db ".backup app/kbai_api.db.backup"
```

## Configuration Examples

### Development Environment
```bash
# .env.development
DB_BACKEND=sqlite
TRACE_DB_PATH=./app/kbai_api.db
VECTOR_STORAGE=local
ATTACHMENT_STORAGE=local
```

### Staging Environment
```bash
# .env.staging
DB_BACKEND=postgresql
DB_HOST=staging-postgres.internal
DB_NAME=kbai_staging
DB_USER=kbai_staging_user
DB_PASSWORD=staging_password_here
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=staging-postgres.internal
VECTOR_DB_NAME=kbai_vectors_staging
```

### Production Environment
```bash
# .env.production
DB_BACKEND=postgresql
DB_HOST=prod-postgres.internal
DB_NAME=kbai_production
DB_USER=kbai_prod_user
DB_PASSWORD=secure_production_password
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=50
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=prod-postgres-vectors.internal
VECTOR_DB_NAME=kbai_vectors_production
```

This configuration system allows KBAI to scale from single-instance development to multi-instance production deployments with shared data storage.