#!/usr/bin/env python3
"""
Index versioning system for DARKBO
Manages versioned indexes to allow atomic updates while serving queries
"""

import os
import json
import shutil
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class IndexVersionManager:
    """Manages versioned indexes for atomic updates"""
    
    def __init__(self, project_id: str, base_dir: str = "."):
        self.project_id = project_id
        self.base_dir = Path(base_dir)
        self.project_dir = self.base_dir / project_id
        self.index_dir = self.project_dir / "index"
        self.versions_dir = self.index_dir / "versions"
        
        # Create directories
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Current version tracking
        self.version_file = self.index_dir / "current_version.json"
        self.lock_file = self.index_dir / "build.lock"
    
    def get_current_version(self) -> Optional[str]:
        """Get the currently active index version"""
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version')
            except:
                return None
        return None
    
    def get_data_checksum(self) -> str:
        """Calculate checksum of current FAQ and KB data"""
        checksums = []
        
        # FAQ checksum
        faq_file = self.project_dir / f"{self.project_id}.faq.json"
        if faq_file.exists():
            with open(faq_file, 'rb') as f:
                checksums.append(hashlib.sha256(f.read()).hexdigest())
        
        # KB checksum
        kb_file = self.project_dir / f"{self.project_id}.kb.json"
        if kb_file.exists():
            with open(kb_file, 'rb') as f:
                checksums.append(hashlib.sha256(f.read()).hexdigest())
        
        # Combined checksum
        combined = ''.join(sorted(checksums))
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def needs_rebuild(self) -> bool:
        """Check if indexes need to be rebuilt based on data changes"""
        current_version = self.get_current_version()
        if not current_version:
            return True
        
        # Get stored checksum
        version_dir = self.versions_dir / current_version
        meta_file = version_dir / "meta.json"
        
        if not meta_file.exists():
            return True
        
        try:
            with open(meta_file, 'r') as f:
                meta = json.load(f)
                stored_checksum = meta.get('data_checksum')
        except:
            return True
        
        current_checksum = self.get_data_checksum()
        return stored_checksum != current_checksum
    
    def is_building(self) -> bool:
        """Check if an index build is currently in progress"""
        return self.lock_file.exists()
    
    def start_build(self) -> str:
        """Start a new index build, returns the new version identifier"""
        if self.is_building():
            raise RuntimeError("Index build already in progress")
        
        # Create build lock
        with open(self.lock_file, 'w') as f:
            json.dump({
                'started_at': datetime.utcnow().isoformat(),
                'process_id': os.getpid()
            }, f)
        
        # Generate new version
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        data_checksum = self.get_data_checksum()[:8]
        new_version = f"v{timestamp}_{data_checksum}"
        
        # Create version directory
        version_dir = self.versions_dir / new_version
        version_dir.mkdir(exist_ok=True)
        
        return new_version
    
    def complete_build(self, version: str, index_metadata: Dict) -> bool:
        """Complete index build and make it the current version"""
        version_dir = self.versions_dir / version
        if not version_dir.exists():
            raise ValueError(f"Version directory {version} does not exist")
        
        # Write metadata
        meta_file = version_dir / "meta.json"
        metadata = {
            'version': version,
            'created_at': datetime.utcnow().isoformat(),
            'data_checksum': self.get_data_checksum(),
            'project_id': self.project_id,
            **index_metadata
        }
        
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Update current version atomically
        temp_version_file = self.version_file.with_suffix('.tmp')
        with open(temp_version_file, 'w') as f:
            json.dump({
                'version': version,
                'updated_at': datetime.utcnow().isoformat()
            }, f)
        
        # Atomic rename
        temp_version_file.rename(self.version_file)
        
        # Remove build lock
        if self.lock_file.exists():
            self.lock_file.unlink()
        
        # Clean up old versions (keep last 3)
        self._cleanup_old_versions()
        
        logger.info(f"Index version {version} is now active for project {self.project_id}")
        return True
    
    def abort_build(self, version: str = None):
        """Abort current build and clean up"""
        if version:
            version_dir = self.versions_dir / version
            if version_dir.exists():
                shutil.rmtree(version_dir)
        
        if self.lock_file.exists():
            self.lock_file.unlink()
    
    def get_version_path(self, version: str = None) -> Path:
        """Get path to version directory (current if version=None)"""
        if version is None:
            version = self.get_current_version()
            if not version:
                raise ValueError("No current version available")
        
        return self.versions_dir / version
    
    def get_current_index_paths(self) -> Dict[str, Path]:
        """Get paths to current index files"""
        current_version = self.get_current_version()
        if not current_version:
            # Fall back to old structure for backward compatibility
            return {
                'dense': self.index_dir / "dense",
                'sparse': self.index_dir / "sparse",
                'meta': self.index_dir / "meta.json"
            }
        
        version_dir = self.get_version_path(current_version)
        return {
            'dense': version_dir / "dense",
            'sparse': version_dir / "sparse", 
            'meta': version_dir / "meta.json"
        }
    
    def _cleanup_old_versions(self, keep_count: int = 3):
        """Remove old versions, keeping the most recent ones"""
        try:
            version_dirs = []
            for item in self.versions_dir.iterdir():
                if item.is_dir() and item.name.startswith('v'):
                    version_dirs.append(item)
            
            # Sort by creation time (newest first)
            version_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove old versions
            for old_version in version_dirs[keep_count:]:
                shutil.rmtree(old_version)
                logger.info(f"Cleaned up old index version: {old_version.name}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up old versions: {e}")
    
    def list_versions(self) -> List[Dict[str, any]]:
        """List all available versions with metadata"""
        versions = []
        
        try:
            for version_dir in self.versions_dir.iterdir():
                if not version_dir.is_dir() or not version_dir.name.startswith('v'):
                    continue
                
                meta_file = version_dir / "meta.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r') as f:
                            meta = json.load(f)
                            versions.append(meta)
                    except:
                        continue
        except:
            pass
        
        return sorted(versions, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def get_build_status(self) -> Dict[str, any]:
        """Get current build status"""
        status = {
            'is_building': self.is_building(),
            'current_version': self.get_current_version(),
            'needs_rebuild': self.needs_rebuild(),
            'data_checksum': self.get_data_checksum()
        }
        
        if status['is_building'] and self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    lock_data = json.load(f)
                    status['build_started_at'] = lock_data.get('started_at')
                    status['build_process_id'] = lock_data.get('process_id')
            except:
                pass
        
        return status


class IndexBuilder:
    """Enhanced index builder with versioning support"""
    
    def __init__(self, project_id: str, base_dir: str = "."):
        self.project_id = project_id
        self.base_dir = Path(base_dir)
        self.version_manager = IndexVersionManager(project_id, base_dir)
        
        # Import dependencies if available
        self.has_deps = False
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            import faiss
            from whoosh.index import create_in
            from whoosh.fields import Schema, TEXT, ID, STORED
            self.has_deps = True
        except ImportError:
            pass
    
    def build_new_version(self) -> str:
        """Build a new version of the indexes"""
        if not self.version_manager.needs_rebuild():
            current_version = self.version_manager.get_current_version()
            logger.info(f"Indexes are up to date for project {self.project_id}, version {current_version}")
            return current_version
        
        new_version = self.version_manager.start_build()
        logger.info(f"Starting index build for project {self.project_id}, version {new_version}")
        
        try:
            # Get version directory
            version_dir = self.version_manager.get_version_path(new_version)
            dense_dir = version_dir / "dense"
            sparse_dir = version_dir / "sparse"
            
            dense_dir.mkdir(exist_ok=True)
            sparse_dir.mkdir(exist_ok=True)
            
            # Load data
            faq_data, kb_data = self._load_project_data()
            all_items = faq_data + kb_data
            
            if not all_items:
                raise ValueError("No data to index")
            
            # Build indexes
            index_metadata = {
                'item_count': len(all_items),
                'faq_count': len(faq_data),
                'kb_count': len(kb_data),
                'indexes': {}
            }
            
            # Build dense index if dependencies available
            if self.has_deps:
                try:
                    dense_success = self._build_dense_index(all_items, dense_dir)
                    index_metadata['indexes']['dense'] = {
                        'available': dense_success,
                        'type': 'faiss'
                    }
                except Exception as e:
                    logger.warning(f"Dense index build failed: {e}")
                    index_metadata['indexes']['dense'] = {'available': False, 'error': str(e)}
            else:
                index_metadata['indexes']['dense'] = {'available': False, 'reason': 'dependencies_missing'}
            
            # Build sparse index if dependencies available
            if self.has_deps:
                try:
                    sparse_success = self._build_sparse_index(all_items, sparse_dir)
                    index_metadata['indexes']['sparse'] = {
                        'available': sparse_success,
                        'type': 'whoosh'
                    }
                except Exception as e:
                    logger.warning(f"Sparse index build failed: {e}")
                    index_metadata['indexes']['sparse'] = {'available': False, 'error': str(e)}
            else:
                index_metadata['indexes']['sparse'] = {'available': False, 'reason': 'dependencies_missing'}
            
            # Complete the build
            self.version_manager.complete_build(new_version, index_metadata)
            
            logger.info(f"Index build completed successfully for project {self.project_id}, version {new_version}")
            return new_version
            
        except Exception as e:
            logger.error(f"Index build failed for project {self.project_id}: {e}")
            self.version_manager.abort_build(new_version)
            raise
    
    def _load_project_data(self) -> Tuple[List[Dict], List[Dict]]:
        """Load FAQ and KB data from project files"""
        project_dir = self.base_dir / self.project_id
        
        # Load FAQs
        faq_data = []
        faq_file = project_dir / f"{self.project_id}.faq.json"
        if faq_file.exists():
            with open(faq_file, 'r', encoding='utf-8') as f:
                raw_faqs = json.load(f)
                for faq in raw_faqs:
                    faq_data.append({
                        'id': faq['id'],
                        'type': 'faq',
                        'question': faq['question'],
                        'answer': faq['answer'],
                        'content': f"{faq['question']} {faq['answer']}"
                    })
        
        # Load KB entries
        kb_data = []
        kb_file = project_dir / f"{self.project_id}.kb.json"
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                raw_kb = json.load(f)
                for kb in raw_kb:
                    kb_data.append({
                        'id': kb['id'],
                        'type': 'kb',
                        'title': kb['article'],
                        'content': kb['content']
                    })
        
        return faq_data, kb_data
    
    def _build_dense_index(self, items: List[Dict], dense_dir: Path) -> bool:
        """Build FAISS dense vector index"""
        if not self.has_deps:
            return False
        
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer
            import faiss
            
            # Load embedding model
            model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Prepare texts for embedding
            texts = [item['content'] for item in items]
            
            # Generate embeddings
            embeddings = model.encode(texts, convert_to_numpy=True)
            embeddings = embeddings.astype('float32')
            
            # Normalize embeddings
            faiss.normalize_L2(embeddings)
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)
            index.add(embeddings)
            
            # Save index
            index_file = dense_dir / "faiss.index"
            faiss.write_index(index, str(index_file))
            
            # Save metadata
            metadata = {
                'items': items,
                'dimension': dimension,
                'count': len(items),
                'model': 'all-MiniLM-L6-v2'
            }
            
            metadata_file = dense_dir / "metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Dense index build error: {e}")
            return False
    
    def _build_sparse_index(self, items: List[Dict], sparse_dir: Path) -> bool:
        """Build Whoosh sparse text index"""
        if not self.has_deps:
            return False
        
        try:
            from whoosh.index import create_in
            from whoosh.fields import Schema, TEXT, ID, STORED
            from whoosh.writing import AsyncWriter
            
            # Define schema
            schema = Schema(
                id=ID(stored=True),
                type=STORED,
                question=TEXT(stored=True),
                answer=TEXT(stored=True),
                title=TEXT(stored=True),
                content=TEXT(stored=True)
            )
            
            # Create index
            ix = create_in(str(sparse_dir), schema)
            
            # Add documents
            writer = AsyncWriter(ix)
            
            for item in items:
                doc_fields = {
                    'id': item['id'],
                    'type': item['type'],
                    'content': item['content']
                }
                
                if item['type'] == 'faq':
                    doc_fields.update({
                        'question': item['question'],
                        'answer': item['answer']
                    })
                else:
                    doc_fields.update({
                        'title': item['title']
                    })
                
                writer.add_document(**doc_fields)
            
            writer.commit()
            return True
            
        except Exception as e:
            logger.error(f"Sparse index build error: {e}")
            return False