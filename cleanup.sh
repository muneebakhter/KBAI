#!/bin/bash
# DARKBO Cleanup Script
# Removes generated data, indexes, and temporary files

set -e

echo "🧹 DARKBO Cleanup Script"
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
echo "  📁 data/ directory (all project data and indexes)"
echo "  📁 sample_data/ directory (if exists)"
echo "  🗃️  Any .pyc and __pycache__ files"
echo "  📊 Any temporary build artifacts"
echo ""

if ! confirm "Do you want to proceed with cleanup?"; then
    echo "❌ Cleanup cancelled"
    exit 0
fi

echo ""
echo "🧹 Starting cleanup..."

# Remove data directory
if [ -d "data" ]; then
    echo "🗑️  Removing data/ directory..."
    rm -rf data/
    echo "   ✅ data/ removed"
else
    echo "   ℹ️  data/ directory not found"
fi

# Remove sample_data directory
if [ -d "sample_data" ]; then
    echo "🗑️  Removing sample_data/ directory..."
    rm -rf sample_data/
    echo "   ✅ sample_data/ removed"
else
    echo "   ℹ️  sample_data/ directory not found"
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
echo "🚀 To regenerate data and start fresh:"
echo "   python3 create_sample_data.py"
echo "   cd data && python3 ../prebuild_kb.py"
echo "   python3 ai_worker.py"
echo ""
echo "📋 Or run the unified demo:"
echo "   ./demo_unified.sh"