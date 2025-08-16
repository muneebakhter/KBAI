#!/usr/bin/env python3
"""
Simplified prebuild script for knowledge graphs and vector stores.
Creates indexes per project folder based on FAQ and KB data with versioning support.
Auto-discovers projects in the data/ folder without requiring proj_mapping.txt.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List

# Import the new versioned IndexBuilder
from kb_api.index_versioning import IndexBuilder


def check_required_dependencies() -> bool:
    """Check if required indexing dependencies are available"""
    missing_deps = []
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy>=1.24.0")
    
    try:
        import sentence_transformers
    except ImportError:
        missing_deps.append("sentence-transformers>=2.2.0")
    
    try:
        import faiss
    except ImportError:
        missing_deps.append("faiss-cpu>=1.7.4")
    
    try:
        import whoosh
    except ImportError:
        missing_deps.append("whoosh>=2.7.4")
    
    if missing_deps:
        print("❌ PREBUILD FAILED: Required dependencies are missing")
        print("=" * 50)
        print("The following libraries are required for proper indexing:")
        for dep in missing_deps:
            print(f"   ❌ {dep}")
        print()
        print("📦 Install missing dependencies with:")
        print("   pip install " + " ".join(dep.split(">=")[0] for dep in missing_deps))
        print()
        print("💡 Or install all recommended dependencies:")
        print("   pip install -r requirements.txt")
        print()
        print("🚫 Prebuild cannot continue without these libraries.")
        return False
    
    return True


def auto_discover_projects(data_dir: Path) -> Dict[str, str]:
    """Auto-discover projects by scanning the data directory"""
    projects = {}
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return projects
    
    # Look for project directories (directories with numeric names or containing project files)
    for item in data_dir.iterdir():
        if item.is_dir():
            project_id = item.name
            
            # Check if this looks like a project directory
            # Look for .faq.json or .kb.json files
            faq_file = item / f"{project_id}.faq.json"
            kb_file = item / f"{project_id}.kb.json"
            
            if faq_file.exists() or kb_file.exists():
                # Try to determine project name from the data
                project_name = project_id  # Default to ID
                
                # Try to get name from FAQ/KB data if available
                if faq_file.exists():
                    try:
                        with open(faq_file, 'r', encoding='utf-8') as f:
                            faq_data = json.load(f)
                            if faq_data and len(faq_data) > 0:
                                # Look through FAQs to guess project name
                                for faq in faq_data[:3]:  # Check first few FAQs
                                    answer = faq.get('answer', '').upper()
                                    question = faq.get('question', '').upper()
                                    content = answer + ' ' + question
                                    
                                    if 'ACLU' in content or 'AMERICAN CIVIL LIBERTIES' in content:
                                        project_name = 'ACLU'
                                        break
                                    elif 'ASPCA' in content or 'PREVENTION OF CRUELTY TO ANIMALS' in content:
                                        project_name = 'ASPCA' 
                                        break
                    except Exception:
                        pass  # Keep default name
                
                projects[project_id] = project_name
                
    return projects


def main():
    """Main prebuild function"""
    print("🚀 DARKBO Knowledge Base Prebuild")
    print("=" * 50)
    
    # Check required dependencies first
    if not check_required_dependencies():
        sys.exit(1)
    
    print("✅ All required dependencies are available")
    print()
    
    # Determine the working directory and data location
    current_dir = Path(".").resolve()
    
    if current_dir.name == "data":
        # We're running from inside data/ directory
        data_dir = current_dir
        base_dir = "."
        print(f"📁 Running from data directory: {data_dir}")
    else:
        # We're running from project root, look for data/ subdirectory
        data_dir = current_dir / "data"
        if not data_dir.exists():
            print("❌ No data directory found. Please run from data/ directory or ensure data/ exists")
            print("💡 Run 'python3 create_sample_data.py' to create the data directory")
            return
        base_dir = str(data_dir)
        print(f"📁 Using data directory: {data_dir}")
    
    # Auto-discover projects
    projects = auto_discover_projects(data_dir)
    
    if not projects:
        print("❌ No projects found in data directory")
        print("💡 Run 'python3 create_sample_data.py' to create sample projects")
        return
    
    print(f"📋 Auto-discovered {len(projects)} projects:")
    for project_id, project_name in projects.items():
        print(f"   {project_id} → {project_name}")
    
    # Build indexes for each project using versioning system
    results = {}
    
    for project_id, project_name in projects.items():
        try:
            # Use new IndexBuilder with versioning
            builder = IndexBuilder(project_id, base_dir)
            new_version = builder.build_new_version()
            
            if new_version:
                results[project_id] = {"version": new_version, "success": True}
                print(f"✅ {project_id} ({project_name}): version {new_version}")
            else:
                print(f"ℹ️  {project_id} ({project_name}): indexes up to date")
                results[project_id] = {"success": True, "up_to_date": True}
                
        except Exception as e:
            print(f"❌ {project_id} ({project_name}): {e}")
            results[project_id] = {"error": str(e)}
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Build Summary")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for project_id, result in results.items():
        project_name = projects.get(project_id, "Unknown")
        if "error" in result:
            print(f"❌ {project_id} ({project_name}): {result['error']}")
            failed += 1
        else:
            if result.get("up_to_date"):
                print(f"✅ {project_id} ({project_name}): up to date")
            else:
                version = result.get("version", "unknown")
                print(f"✅ {project_id} ({project_name}): version {version}")
            successful += 1
    
    print(f"\n🎉 Completed: {successful} successful, {failed} failed")
    
    # Exit with appropriate code
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()