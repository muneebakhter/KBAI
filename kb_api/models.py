import uuid
import hashlib
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json

# Namespace for UUID5 generation
NAMESPACE_URL = uuid.NAMESPACE_URL

class FAQEntry:
    """FAQ entry with stable UUID5 ID"""
    
    def __init__(self, id: str, question: str, answer: str, 
                 created_at: datetime = None, updated_at: datetime = None,
                 source: str = "manual", source_file: Optional[str] = None):
        self.id = id
        self.question = question
        self.answer = answer
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.source = source
        self.source_file = source_file
    
    @classmethod
    def create_id(cls, project_id: str, question: str, answer: str) -> str:
        """Generate stable UUID5 ID for FAQ entry"""
        content = f"faq:{project_id}:{question.strip()}:{answer.strip()}"
        return str(uuid.uuid5(NAMESPACE_URL, content))
    
    @classmethod
    def from_qa(cls, project_id: str, question: str, answer: str, **kwargs) -> "FAQEntry":
        """Create FAQ entry from question and answer"""
        faq_id = cls.create_id(project_id, question, answer)
        return cls(
            id=faq_id,
            question=question,
            answer=answer,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "source": self.source,
            "source_file": self.source_file
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FAQEntry":
        """Create from dictionary"""
        # Handle datetime strings
        for date_field in ['created_at', 'updated_at']:
            if isinstance(data.get(date_field), str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
                except:
                    data[date_field] = datetime.utcnow()
        
        return cls(**data)

class KBEntry:
    """Knowledge base entry with stable UUID5 ID"""
    
    def __init__(self, id: str, article: str, content: str,
                 created_at: datetime = None, updated_at: datetime = None,
                 source: str = "upload", source_file: Optional[str] = None,
                 chunk_index: Optional[int] = None):
        self.id = id
        self.article = article
        self.content = content
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.source = source
        self.source_file = source_file
        self.chunk_index = chunk_index
    
    @classmethod
    def create_id(cls, project_id: str, article: str, content: str) -> str:
        """Generate stable UUID5 ID for KB entry"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        content_str = f"kb:{project_id}:{article}:{content_hash}"
        return str(uuid.uuid5(NAMESPACE_URL, content_str))
    
    @classmethod
    def from_content(cls, project_id: str, article: str, content: str, **kwargs) -> "KBEntry":
        """Create KB entry from article and content"""
        kb_id = cls.create_id(project_id, article, content)
        return cls(
            id=kb_id,
            article=article,
            content=content,
            **kwargs
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "article": self.article,
            "content": self.content,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
            "source": self.source,
            "source_file": self.source_file,
            "chunk_index": self.chunk_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KBEntry":
        """Create from dictionary"""
        # Handle datetime strings
        for date_field in ['created_at', 'updated_at']:
            if isinstance(data.get(date_field), str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))
                except:
                    data[date_field] = datetime.utcnow()
        
        return cls(**data)

class QueryRequest:
    """Query request model"""
    
    def __init__(self, project_id: str, question: str, mode: str = "auto", strict_citations: bool = True):
        self.project_id = project_id
        self.question = question
        self.mode = mode
        self.strict_citations = strict_citations

class Citation:
    """Citation model for query responses"""
    
    def __init__(self, type: str, id: str, article: Optional[str] = None, 
                 lines: Optional[List[int]] = None, score: float = 0.0):
        self.type = type
        self.id = id
        self.article = article
        self.lines = lines
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "article": self.article,
            "lines": self.lines,
            "score": self.score
        }

class QueryResponse:
    """Structured query response with citations"""
    
    def __init__(self, answer: str, mode: str, confidence: float,
                 citations: List[Citation] = None, used_chunks: List[str] = None):
        self.answer = answer
        self.mode = mode
        self.confidence = confidence
        self.citations = citations or []
        self.used_chunks = used_chunks or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "mode": self.mode,
            "confidence": self.confidence,
            "citations": [c.to_dict() for c in self.citations],
            "used_chunks": self.used_chunks
        }