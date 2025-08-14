from __future__ import annotations
import os
import json
import uuid
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

class VectorStorageInterface(ABC):
    """Abstract base class for vector storage operations."""
    
    @abstractmethod
    def store_embedding(self, project_id: str, content_type: str, content_id: str, 
                       title: str, content: str, embedding: List[float], 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store an embedding vector with associated content."""
        pass
    
    @abstractmethod
    def search_similar(self, project_id: str, query_embedding: List[float], 
                      limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar content based on embedding similarity."""
        pass
    
    @abstractmethod
    def delete_embedding(self, project_id: str, content_type: str, content_id: str) -> bool:
        """Delete embeddings for specific content."""
        pass
    
    @abstractmethod
    def get_embeddings(self, project_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all embeddings for a project, optionally filtered by content type."""
        pass


class AttachmentStorageInterface(ABC):
    """Abstract base class for attachment storage operations."""
    
    @abstractmethod
    def store_file(self, project_id: str, content_type: str, content_id: str,
                  filename: str, content: bytes, mime_type: Optional[str] = None) -> str:
        """Store a file attachment and return the storage path/ID."""
        pass
    
    @abstractmethod
    def retrieve_file(self, project_id: str, file_id: str) -> Tuple[bytes, str, str]:
        """Retrieve file content, mime type, and original filename."""
        pass
    
    @abstractmethod
    def delete_file(self, project_id: str, file_id: str) -> bool:
        """Delete a file attachment."""
        pass
    
    @abstractmethod
    def list_files(self, project_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all files for a project, optionally filtered by content type."""
        pass


class LocalVectorStorage(VectorStorageInterface):
    """Local file-based vector storage implementation."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_project_dir(self, project_id: str) -> Path:
        project_dir = self.base_dir / project_id / "vectors"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def _get_embeddings_file(self, project_id: str) -> Path:
        return self._get_project_dir(project_id) / "embeddings.json"
    
    def _load_embeddings(self, project_id: str) -> List[Dict[str, Any]]:
        embeddings_file = self._get_embeddings_file(project_id)
        if embeddings_file.exists():
            try:
                with open(embeddings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def _save_embeddings(self, project_id: str, embeddings: List[Dict[str, Any]]) -> None:
        embeddings_file = self._get_embeddings_file(project_id)
        with open(embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings, f, ensure_ascii=False, indent=2)
    
    def store_embedding(self, project_id: str, content_type: str, content_id: str,
                       title: str, content: str, embedding: List[float],
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        embeddings = self._load_embeddings(project_id)
        
        # Remove existing embedding for the same content
        embeddings = [e for e in embeddings if not (
            e.get('content_type') == content_type and e.get('content_id') == content_id
        )]
        
        # Add new embedding
        embedding_id = str(uuid.uuid4())
        new_embedding = {
            'id': embedding_id,
            'project_id': project_id,
            'content_type': content_type,
            'content_id': content_id,
            'title': title,
            'content': content,
            'embedding': embedding,
            'metadata': metadata or {},
            'created_at': json.dumps({"timestamp": "now"})  # Simplified for local storage
        }
        
        embeddings.append(new_embedding)
        self._save_embeddings(project_id, embeddings)
        return embedding_id
    
    def search_similar(self, project_id: str, query_embedding: List[float],
                      limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        embeddings = self._load_embeddings(project_id)
        
        # Calculate cosine similarity (simplified implementation)
        def cosine_similarity(a: List[float], b: List[float]) -> float:
            import math
            dot_product = sum(x * y for x, y in zip(a, b))
            magnitude_a = math.sqrt(sum(x * x for x in a))
            magnitude_b = math.sqrt(sum(x * x for x in b))
            if magnitude_a == 0 or magnitude_b == 0:
                return 0
            return dot_product / (magnitude_a * magnitude_b)
        
        # Calculate similarities and filter by threshold
        results = []
        for emb in embeddings:
            similarity = cosine_similarity(query_embedding, emb['embedding'])
            if similarity >= threshold:
                result = emb.copy()
                result['similarity'] = similarity
                results.append(result)
        
        # Sort by similarity and limit results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
    
    def delete_embedding(self, project_id: str, content_type: str, content_id: str) -> bool:
        embeddings = self._load_embeddings(project_id)
        original_count = len(embeddings)
        
        embeddings = [e for e in embeddings if not (
            e.get('content_type') == content_type and e.get('content_id') == content_id
        )]
        
        if len(embeddings) < original_count:
            self._save_embeddings(project_id, embeddings)
            return True
        return False
    
    def get_embeddings(self, project_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        embeddings = self._load_embeddings(project_id)
        if content_type:
            embeddings = [e for e in embeddings if e.get('content_type') == content_type]
        return embeddings


class PostgreSQLVectorStorage(VectorStorageInterface):
    """PostgreSQL with pgvector implementation."""
    
    def __init__(self, db_interface):
        self.db_interface = db_interface
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure vector storage tables exist."""
        # This would create the vector tables if they don't exist
        # Implementation depends on whether pgvector extension is available
        pass
    
    def store_embedding(self, project_id: str, content_type: str, content_id: str,
                       title: str, content: str, embedding: List[float],
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        # Implementation for PostgreSQL + pgvector
        # This would use the vector data type for efficient storage and search
        raise NotImplementedError("PostgreSQL vector storage not yet implemented")
    
    def search_similar(self, project_id: str, query_embedding: List[float],
                      limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        # Implementation using pgvector's similarity search
        raise NotImplementedError("PostgreSQL vector storage not yet implemented")
    
    def delete_embedding(self, project_id: str, content_type: str, content_id: str) -> bool:
        raise NotImplementedError("PostgreSQL vector storage not yet implemented")
    
    def get_embeddings(self, project_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("PostgreSQL vector storage not yet implemented")


class LocalAttachmentStorage(AttachmentStorageInterface):
    """Local file system attachment storage."""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_project_dir(self, project_id: str) -> Path:
        project_dir = self.base_dir / project_id / "attachments"
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def _get_metadata_file(self, project_id: str) -> Path:
        return self._get_project_dir(project_id) / "metadata.json"
    
    def _load_metadata(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        metadata_file = self._get_metadata_file(project_id)
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_metadata(self, project_id: str, metadata: Dict[str, Dict[str, Any]]) -> None:
        metadata_file = self._get_metadata_file(project_id)
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def store_file(self, project_id: str, content_type: str, content_id: str,
                  filename: str, content: bytes, mime_type: Optional[str] = None) -> str:
        project_dir = self._get_project_dir(project_id)
        file_id = str(uuid.uuid4())
        
        # Preserve file extension if present
        if '.' in filename:
            extension = filename.split('.')[-1]
            storage_filename = f"{file_id}.{extension}"
        else:
            storage_filename = file_id
        
        file_path = project_dir / storage_filename
        
        # Store file content
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Update metadata
        metadata = self._load_metadata(project_id)
        metadata[file_id] = {
            'file_id': file_id,
            'project_id': project_id,
            'content_type': content_type,
            'content_id': content_id,
            'filename': storage_filename,
            'original_filename': filename,
            'mime_type': mime_type,
            'file_size': len(content),
            'storage_backend': 'local'
        }
        self._save_metadata(project_id, metadata)
        
        return file_id
    
    def retrieve_file(self, project_id: str, file_id: str) -> Tuple[bytes, str, str]:
        metadata = self._load_metadata(project_id)
        file_meta = metadata.get(file_id)
        
        if not file_meta:
            raise FileNotFoundError(f"File {file_id} not found")
        
        project_dir = self._get_project_dir(project_id)
        file_path = project_dir / file_meta['filename']
        
        if not file_path.exists():
            raise FileNotFoundError(f"File content not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            content = f.read()
        
        return content, file_meta.get('mime_type', ''), file_meta['original_filename']
    
    def delete_file(self, project_id: str, file_id: str) -> bool:
        metadata = self._load_metadata(project_id)
        file_meta = metadata.get(file_id)
        
        if not file_meta:
            return False
        
        project_dir = self._get_project_dir(project_id)
        file_path = project_dir / file_meta['filename']
        
        # Delete file
        if file_path.exists():
            file_path.unlink()
        
        # Remove from metadata
        del metadata[file_id]
        self._save_metadata(project_id, metadata)
        
        return True
    
    def list_files(self, project_id: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        metadata = self._load_metadata(project_id)
        files = list(metadata.values())
        
        if content_type:
            files = [f for f in files if f.get('content_type') == content_type]
        
        return files


def create_vector_storage(storage_type: str = None, **kwargs) -> VectorStorageInterface:
    """Factory function to create vector storage interface."""
    
    if storage_type is None:
        storage_type = os.getenv('VECTOR_STORAGE', 'local').lower()
    
    if storage_type == 'local':
        base_dir = kwargs.get('base_dir') or os.getenv('DATA_DIR', './data')
        return LocalVectorStorage(base_dir)
    
    elif storage_type == 'postgresql':
        # Would need a database interface for PostgreSQL vector storage
        db_interface = kwargs.get('db_interface')
        if not db_interface:
            raise ValueError("db_interface required for PostgreSQL vector storage")
        return PostgreSQLVectorStorage(db_interface)
    
    else:
        raise ValueError(f"Unsupported vector storage type: {storage_type}")


def create_attachment_storage(storage_type: str = None, **kwargs) -> AttachmentStorageInterface:
    """Factory function to create attachment storage interface."""
    
    if storage_type is None:
        storage_type = os.getenv('ATTACHMENT_STORAGE', 'local').lower()
    
    if storage_type == 'local':
        base_dir = kwargs.get('base_dir') or os.getenv('DATA_DIR', './data')
        return LocalAttachmentStorage(base_dir)
    
    # Future: Add S3, GCS, Azure Blob storage implementations
    else:
        raise ValueError(f"Unsupported attachment storage type: {storage_type}")