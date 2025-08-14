#!/usr/bin/env bash
set -euo pipefail

# KBAI Database Configuration Demo
# This script demonstrates the new multi-backend database support

echo "🚀 KBAI Database Configuration Demo"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Please run this script from the KBAI project root directory"
    exit 1
fi

echo -e "${BLUE}📋 Available Database Backends:${NC}"
echo "1. SQLite (default) - Single file database, perfect for development"
echo "2. PostgreSQL - Enterprise database with connection pooling"
echo ""

echo -e "${BLUE}📋 Available Storage Options:${NC}"
echo "1. Local Vector Storage - File-based embeddings storage"
echo "2. PostgreSQL Vector Storage - Database-based with pgvector (future)"
echo "3. Local Attachment Storage - File system attachment storage"
echo ""

# Demo 1: Test SQLite configuration
echo -e "${YELLOW}Demo 1: Testing SQLite Backend (Default)${NC}"
echo "----------------------------------------"

echo "✓ Running database configuration tests..."
python test_db_config.py

echo ""
echo -e "${GREEN}✅ SQLite backend working correctly!${NC}"
echo ""

# Demo 2: Show configuration options
echo -e "${YELLOW}Demo 2: Configuration Examples${NC}"
echo "-----------------------------------"

echo "🔧 SQLite Configuration (.env):"
cat << 'EOF'
DB_BACKEND=sqlite
TRACE_DB_PATH=./app/kbai_api.db
VECTOR_STORAGE=local
ATTACHMENT_STORAGE=local
EOF

echo ""
echo "🔧 PostgreSQL Configuration (.env):"
cat << 'EOF'
DB_BACKEND=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kbai
DB_USER=kbai_user
DB_PASSWORD=kbai_password
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
VECTOR_STORAGE=postgresql
VECTOR_DB_HOST=localhost
VECTOR_DB_NAME=kbai_vectors
EOF

echo ""

# Demo 3: Show multi-backend initialization
echo -e "${YELLOW}Demo 3: Multi-Backend Initialization${NC}"
echo "-------------------------------------"

echo "📄 Available initialization scripts:"
echo "  ./init_db.sh        - Original SQLite-only script"
echo "  ./init_db_multi.sh  - New multi-backend script"
echo ""

echo "✓ Testing multi-backend initialization script..."
if [ -x "./init_db_multi.sh" ]; then
    echo "✅ Multi-backend initialization script is executable"
else
    echo "❌ Multi-backend initialization script is not executable"
    exit 1
fi

# Demo 4: Show vector and attachment storage
echo -e "${YELLOW}Demo 4: Storage Interface Demo${NC}"
echo "-----------------------------------"

echo "✓ Testing vector and attachment storage interfaces..."
python3 << 'EOF'
import tempfile
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path.cwd()))

from app.storage_interfaces import create_vector_storage, create_attachment_storage

print("🔍 Testing Vector Storage...")
with tempfile.TemporaryDirectory() as temp_dir:
    # Test vector storage
    vector_storage = create_vector_storage('local', base_dir=temp_dir)
    
    # Store a test embedding
    embedding_id = vector_storage.store_embedding(
        project_id="demo_project",
        content_type="faq",
        content_id="faq_demo",
        title="Demo FAQ",
        content="This is a demonstration FAQ",
        embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        metadata={"demo": True}
    )
    
    print(f"✅ Stored embedding with ID: {embedding_id}")
    
    # Search for similar content
    results = vector_storage.search_similar(
        project_id="demo_project",
        query_embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        limit=5
    )
    
    print(f"✅ Found {len(results)} similar results")
    
    print("\n📎 Testing Attachment Storage...")
    
    # Test attachment storage
    attachment_storage = create_attachment_storage('local', base_dir=temp_dir)
    
    # Store a test file
    test_content = b"This is demo file content for KBAI"
    file_id = attachment_storage.store_file(
        project_id="demo_project",
        content_type="document",
        content_id="doc_demo",
        filename="demo.txt",
        content=test_content,
        mime_type="text/plain"
    )
    
    print(f"✅ Stored file with ID: {file_id}")
    
    # Retrieve the file
    content, mime_type, filename = attachment_storage.retrieve_file(
        project_id="demo_project",
        file_id=file_id
    )
    
    print(f"✅ Retrieved file: {filename} ({mime_type})")
    print(f"   Content size: {len(content)} bytes")

print("\n✅ All storage interfaces working correctly!")
EOF

echo ""

# Demo 5: Show benefits
echo -e "${YELLOW}Demo 5: Benefits of New Database Configuration${NC}"
echo "-----------------------------------------------"

echo "🎯 Key Benefits:"
echo "  ✅ Multi-instance deployment support"
echo "  ✅ Shared data across API instances"
echo "  ✅ Enterprise-grade PostgreSQL support"
echo "  ✅ Connection pooling for performance"
echo "  ✅ Backward compatibility with SQLite"
echo "  ✅ Configurable vector and attachment storage"
echo "  ✅ Scalable architecture for production"
echo ""

echo "🔄 Migration Path:"
echo "  1. Development: Start with SQLite"
echo "  2. Staging: Test with PostgreSQL"  
echo "  3. Production: Deploy with PostgreSQL cluster"
echo "  4. Scale: Add multiple API instances"
echo ""

echo "📚 Documentation:"
echo "  📖 Database setup: DATABASE_CONFIG.md"
echo "  📖 Environment config: .env.example" 
echo "  📖 Migration guide: DATABASE_CONFIG.md"
echo ""

echo -e "${GREEN}🎉 KBAI Database Configuration Demo Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Copy .env.example to .env"
echo "  2. Configure your preferred database backend"
echo "  3. Run ./init_db_multi.sh to initialize"
echo "  4. Start the API with ./run_api.sh"
echo ""
echo "For PostgreSQL setup, see DATABASE_CONFIG.md"