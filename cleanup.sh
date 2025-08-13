#!/bin/bash
# KBAI Cleanup Script
# Removes generated data, indexes, database, and temporary files

set -e

echo "🧹 KBAI Cleanup Script"
echo "======================="
echo ""

# Function to confirm action
confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Show what would be cleaned
echo "📋 This script will clean up the following:"
echo "  🗃️  SQLite database (./app/kbai_api.db and related files)"
echo "  📁 data/ directory (all project data and indexes)"
echo "  📁 sample_data/ directory (if exists)"
echo "  🗃️  Any .pyc and __pycache__ files"
echo "  📊 Any temporary build artifacts"
echo "  📊 Home directory KBAI data (~/.kbai/)"
echo ""

if ! confirm "Do you want to proceed with cleanup?"; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🧹 Starting cleanup..."

# Remove SQLite database and related files
echo "🗑️  Removing SQLite database..."
if [ -f "./app/kbai_api.db" ]; then
    rm -f "./app/kbai_api.db"
    echo "   ✅ kbai_api.db removed"
else
    echo "   ℹ️  kbai_api.db not found"
fi

# Remove SQLite WAL and SHM files
if [ -f "./app/kbai_api.db-wal" ]; then
    rm -f "./app/kbai_api.db-wal"
    echo "   ✅ kbai_api.db-wal removed"
fi

if [ -f "./app/kbai_api.db-shm" ]; then
    rm -f "./app/kbai_api.db-shm"
    echo "   ✅ kbai_api.db-shm removed"
fi

# Remove data directory
if [ -d "data" ]; then
    echo "🗑️  Removing data/ directory..."
    rm -rf data/
    echo "   ✅ data/ removed"
else
    echo "   ℹ️  data/ directory not found"
fi

# Remove orphaned project directories from root (numeric folders like 95, 175)
echo "🗑️  Removing orphaned project directories from root..."
orphaned_count=0
for dir in */; do
    # Remove trailing slash
    dirname=${dir%/}
    # Check if it's a numeric directory (project folder)
    if [[ "$dirname" =~ ^[0-9]+$ ]]; then
        if [ -d "$dirname" ]; then
            echo "   🗑️  Removing orphaned project directory: $dirname/"
            rm -rf "$dirname"
            orphaned_count=$((orphaned_count + 1))
        fi
    fi
done

if [ $orphaned_count -gt 0 ]; then
    echo "   ✅ Removed $orphaned_count orphaned project directories"
else
    echo "   ℹ️  No orphaned project directories found"
fi

# Remove sample_data directory
if [ -d "sample_data" ]; then
    echo "🗑️  Removing sample_data/ directory..."
    rm -rf sample_data/
    echo "   ✅ sample_data/ removed"
else
    echo "   ℹ️  sample_data/ directory not found"
fi

# Remove home directory KBAI data
if [ -d "$HOME/.kbai" ]; then
    echo "🗑️  Removing ~/.kbai/ directory..."
    rm -rf "$HOME/.kbai"
    echo "   ✅ ~/.kbai/ removed"
else
    echo "   ℹ️  ~/.kbai/ directory not found"
fi

# Remove project mapping file
if [ -f "$HOME/proj_mapping.txt" ]; then
    echo "🗑️  Removing project mapping file..."
    rm -f "$HOME/proj_mapping.txt"
    echo "   ✅ ~/proj_mapping.txt removed"
else
    echo "   ℹ️  ~/proj_mapping.txt not found"
fi

# Remove Python cache files
echo "🗑️  Removing Python cache files..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "   ✅ Python cache files removed"

# Remove any temporary files
echo "🗑️  Removing temporary files..."
rm -f *.tmp *.temp 2>/dev/null || true
rm -rf /tmp/darkbo_* 2>/dev/null || true
rm -rf /tmp/*kbai* 2>/dev/null || true
echo "   ✅ Temporary files removed"

# Remove any log files
if ls *.log 1> /dev/null 2>&1; then
    echo "🗑️  Removing log files..."
    rm -f *.log
    echo "   ✅ Log files removed"
else
    echo "   ℹ️  No log files found"
fi

echo ""
echo "✅ Cleanup completed successfully!"
echo ""
echo "🚀 To start fresh with the combined API:"
echo "   1. ./init_db.sh                     # Initialize database"
echo "   2. python3 create_sample_data.py    # Create sample data"
echo "   3. python3 prebuild_kb.py           # Build indexes"
echo "   4. ./run_api.sh                     # Start combined API"
echo ""
echo "📚 Test the combined API:"
echo "   • Visit http://localhost:8000/docs for API documentation"
echo "   • Use admin/admin to get authentication token"
echo "   • Test AI queries and document upload"