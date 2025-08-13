#!/bin/bash
# safety-check.sh - Run this before any git operations
echo "🔍 DARKBO Safety Check"
echo "====================="

# Check if data folder exists
if [ -d "data" ]; then
    echo "⚠️  WARNING: data/ folder exists"
    echo "🧹 This should be cleaned up before committing"
    
    # Check if it's tracked by git
    if [ -n "$(git ls-files data/)" ]; then
        echo "🚨 CRITICAL: data/ folder is tracked by git!"
        echo "📋 Run: git rm -r --cached data/ && ./cleanup.sh"
        exit 1
    else
        echo "✅ data/ folder exists but is properly ignored by git"
        echo "💡 Consider running ./cleanup.sh for a clean state"
    fi
else
    echo "✅ No data/ folder found - safe to commit"
fi

# Check for any staged data files
if git diff --cached --name-only | grep -q "^data/"; then
    echo "🚨 CRITICAL: data/ files are staged for commit!"
    echo "📋 Run: git reset HEAD data/ && ./cleanup.sh"
    exit 1
fi

echo "✅ Safety check passed"