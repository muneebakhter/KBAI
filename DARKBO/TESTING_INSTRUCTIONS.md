# 🧪 DARKBO Testing Instructions

## ⚠️ CRITICAL REMINDER: Always Run Cleanup After Testing

**NEVER commit the `data/` folder or any generated files to the repository.**

After testing ANY bug fix or new feature, **ALWAYS** run the cleanup script:

```bash
./cleanup.sh
```

## 🚨 Why This Is Important

- The `data/` folder contains generated sample data, indexes, and temporary files
- These files can be large and should not be version controlled
- The `data/` folder is already in `.gitignore`, but running cleanup ensures no traces remain
- Cleanup prevents accidental commits of test data between different development sessions

## 📋 Standard Testing Workflow

### 1. Before Making Changes
```bash
# Ensure clean state
./cleanup.sh
git status  # Should show clean working directory
```

### 2. Testing Bug Fixes or New Features
```bash
# Generate test data
python3 create_sample_data.py

# Build indexes  
cd data
python3 ../prebuild_kb.py

# Test your changes
python3 ../ai_worker.py
# ... run your tests ...

# OR run the unified demo
cd ..
./demo_unified.sh
```

### 3. After Testing (MANDATORY)
```bash
# ALWAYS run cleanup after testing
./cleanup.sh

# Verify data folder is gone
ls -la | grep data  # Should return nothing

# Check git status
git status  # Should not show data/ folder
```

## 🔄 Complete Testing Cycle Example

```bash
# 1. Start clean
./cleanup.sh
git status

# 2. Make your code changes
# ... edit files ...

# 3. Test your changes  
python3 create_sample_data.py
cd data && python3 ../prebuild_kb.py && cd ..
python3 ai_worker.py &
# ... manual testing or automated tests ...
pkill -f ai_worker.py

# 4. MANDATORY CLEANUP
./cleanup.sh

# 5. Commit only your code changes
git add [your-changed-files]
git commit -m "Your changes description"
```

## 🛡️ Safety Checks

### Before Any Git Operations
```bash
# Always verify data/ is not in staging area
git status

# If you see data/ folder, run cleanup immediately
if git status | grep -q "data/"; then
    echo "⚠️  WARNING: data/ folder detected in git status"
    echo "🧹 Running cleanup..."
    ./cleanup.sh
fi
```

### Automated Safety Check Script
Create this safety check script in your project root:

```bash
#!/bin/bash
# safety-check.sh - Run this before any git operations
echo "🔍 DARKBO Safety Check"
echo "====================="

# Check if data folder exists
if [ -d "data" ]; then
    echo "⚠️  WARNING: data/ folder exists"
    echo "🧹 This should be cleaned up before committing"
    
    # Check if it's tracked by git
    if git ls-files data/ >/dev/null 2>&1; then
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
```

## 🔧 What the Cleanup Script Removes

The `cleanup.sh` script removes:
- `data/` directory (all project data and indexes)
- `sample_data/` directory (if exists)
- Python cache files (`*.pyc`, `__pycache__`)
- Temporary build artifacts
- Log files
- Any temporary files (`*.tmp`, `*.temp`)

## 📝 Pre-Commit Checklist

- [ ] Code changes are complete
- [ ] Testing is finished
- [ ] `./cleanup.sh` has been run
- [ ] `git status` shows no `data/` folder
- [ ] Only intended code files are staged for commit

## 🚀 Quick Commands Reference

```bash
# Clean everything
./cleanup.sh

# Full test cycle  
python3 create_sample_data.py && cd data && python3 ../prebuild_kb.py && cd .. && ./demo_unified.sh && ./cleanup.sh

# Safety check before commit
git status | grep -q "data/" && echo "🚨 CLEANUP NEEDED" || echo "✅ Safe to commit"
```

## 🎯 Remember

**The golden rule: If you generated data for testing, clean it up before committing.**

This ensures:
- Clean repository history
- No accidental large file commits  
- Consistent development environment
- Easy collaboration with other developers

---

*Always refer to this file before testing and committing changes to ensure proper cleanup procedures.*

## 📄 Keeping Instructions Updated

If you modify the cleanup process or add new types of generated files:

1. Update `cleanup.sh` to handle new file types
2. Update `.gitignore` if needed
3. Update this instruction file with any new procedures
4. Test the complete workflow to ensure everything works