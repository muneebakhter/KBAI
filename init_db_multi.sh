#!/usr/bin/env bash
set -euo pipefail

# KBAI API Database Initialization Script (Multi-backend support)
echo "Initializing KBAI API database..."

# Get script directory and set paths relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Configuration
DB_BACKEND=${DB_BACKEND:-sqlite}
SQLITE_DB_PATH="$PROJECT_ROOT/app/kbai_api.db"
SQLITE_SCHEMA_PATH="$PROJECT_ROOT/app/schema.sql"
POSTGRESQL_SCHEMA_PATH="$PROJECT_ROOT/app/schema_postgresql.sql"

# PostgreSQL configuration
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-kbai}
DB_USER=${DB_USER:-kbai_user}
DB_PASSWORD=${DB_PASSWORD:-kbai_password}

echo "Database backend: $DB_BACKEND"

if [ "$DB_BACKEND" = "postgresql" ]; then
    echo "Initializing PostgreSQL database..."
    
    # Check if PostgreSQL tools are available
    if ! command -v psql &> /dev/null; then
        echo "❌ Error: psql command not found. Please install PostgreSQL client tools."
        exit 1
    fi
    
    # Check if schema file exists
    if [ ! -f "$POSTGRESQL_SCHEMA_PATH" ]; then
        echo "❌ Error: PostgreSQL schema file not found at $POSTGRESQL_SCHEMA_PATH"
        exit 1
    fi
    
    # Test connection
    echo "Testing PostgreSQL connection..."
    export PGPASSWORD="$DB_PASSWORD"
    
    if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        echo "❌ Error: Cannot connect to PostgreSQL database"
        echo "   Host: $DB_HOST:$DB_PORT"
        echo "   Database: $DB_NAME"
        echo "   User: $DB_USER"
        echo ""
        echo "Please ensure:"
        echo "1. PostgreSQL server is running"
        echo "2. Database '$DB_NAME' exists"
        echo "3. User '$DB_USER' has access to the database"
        echo "4. Connection parameters are correct"
        exit 1
    fi
    
    echo "✅ PostgreSQL connection successful"
    
    # Initialize database with schema
    echo "Creating PostgreSQL tables and indexes..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$POSTGRESQL_SCHEMA_PATH"
    
    # Verify database creation
    TABLES=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('sessions', 'traces');")
    
    if echo "$TABLES" | grep -q "sessions" && echo "$TABLES" | grep -q "traces"; then
        echo "✅ PostgreSQL database initialized successfully"
        
        # Show table info
        echo ""
        echo "Database tables:"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt"
        
        echo ""
        echo "Sessions table schema:"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d sessions"
        
        echo ""
        echo "Traces table schema:"
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d traces"
    else
        echo "❌ Failed to create required tables in PostgreSQL database"
        exit 1
    fi
    
else
    # SQLite initialization (original logic)
    echo "Initializing SQLite database..."
    
    # Create app directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/app"
    
    # Remove existing database if it exists
    if [ -f "$SQLITE_DB_PATH" ]; then
        echo "Removing existing database: $SQLITE_DB_PATH"
        rm -f "$SQLITE_DB_PATH"
        rm -f "${SQLITE_DB_PATH}-shm"
        rm -f "${SQLITE_DB_PATH}-wal"
    fi
    
    # Check if schema file exists
    if [ ! -f "$SQLITE_SCHEMA_PATH" ]; then
        echo "❌ Error: SQLite schema file not found at $SQLITE_SCHEMA_PATH"
        exit 1
    fi
    
    # Initialize database with schema
    echo "Creating database: $SQLITE_DB_PATH"
    sqlite3 "$SQLITE_DB_PATH" < "$SQLITE_SCHEMA_PATH"
    
    # Verify database creation
    if [ -f "$SQLITE_DB_PATH" ]; then
        echo "✅ SQLite database initialized successfully: $SQLITE_DB_PATH"
        
        # Show table info
        echo ""
        echo "Database tables:"
        sqlite3 "$SQLITE_DB_PATH" ".tables"
        
        echo ""
        echo "Sessions table schema:"
        sqlite3 "$SQLITE_DB_PATH" ".schema sessions"
        
        echo ""
        echo "Traces table schema:"
        sqlite3 "$SQLITE_DB_PATH" ".schema traces"
    else
        echo "❌ Failed to create SQLite database"
        exit 1
    fi
fi

echo ""
echo "🚀 Database initialization complete!"
echo "Database backend: $DB_BACKEND"

if [ "$DB_BACKEND" = "postgresql" ]; then
    echo "PostgreSQL connection: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
else
    echo "SQLite database: $SQLITE_DB_PATH"
fi

echo "You can now run the API with: ./run_api.sh"