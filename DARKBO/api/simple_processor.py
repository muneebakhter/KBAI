#!/usr/bin/env python3
"""
Simple document processor fallback when docling/PyPDF2/python-docx are not available
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

class SimpleDocumentProcessor:
    """Fallback document processor for basic text files"""
    
    def __init__(self):
        self.chunk_size = 1000
        self.chunk_overlap = 100
    
    def is_supported(self, filename: str) -> bool:
        """Check if file format is supported"""
        ext = Path(filename).suffix.lower()
        return ext in ['.txt', '.md']
    
    def extract_text(self, file_path: str) -> Tuple[str, List[str]]:
        """Extract text from text file"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        if ext in ['.txt', '.md']:
            return self._extract_text_file(file_path)
        else:
            # For PDF/DOCX without dependencies, return placeholder
            return self._extract_placeholder(file_path)
    
    def _extract_text_file(self, file_path: str) -> Tuple[str, List[str]]:
        """Extract text from plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        cleaned_text = self._clean_text(content)
        chunks = self._create_chunks(cleaned_text)
        
        return cleaned_text, chunks
    
    def _extract_placeholder(self, file_path: str) -> Tuple[str, List[str]]:
        """Create placeholder for unsupported files"""
        filename = Path(file_path).name
        placeholder_text = f"""This document ({filename}) was uploaded but could not be processed automatically.
        
To enable document processing for PDF and DOCX files, install the required dependencies:
pip install python-docx PyPDF2

The document has been saved as an attachment and can be accessed directly."""
        
        return placeholder_text, [placeholder_text]
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\/\n]', ' ', text)
        
        # Clean up spacing
        text = re.sub(r'\s+([,.;:!?])', r'\1', text)
        
        return text.strip()
    
    def _create_chunks(self, text: str) -> List[str]:
        """Split text into chunks"""
        if not text:
            return []
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end < len(text):
                # Try to end at sentence boundary
                chunk_text = text[start:end]
                last_period = chunk_text.rfind('.')
                last_newline = chunk_text.rfind('\n')
                
                if last_period > len(chunk_text) - 200:
                    end = start + last_period + 1
                elif last_newline > len(chunk_text) - 200:
                    end = start + last_newline + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + self.chunk_size - self.chunk_overlap, end)
            
            if start >= len(text):
                break
        
        return chunks
    
    def get_document_metadata(self, file_path: str) -> Dict[str, any]:
        """Get basic document metadata"""
        path = Path(file_path)
        
        metadata = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "file_extension": path.suffix.lower(),
            "supported": self.is_supported(path.name),
            "format": "Text" if self.is_supported(path.name) else "Binary"
        }
        
        return metadata


def process_document_for_kb(file_path: str, article_title: str = None) -> Tuple[str, List[str], Dict]:
    """
    Process document for KB ingestion with fallback processing
    """
    # Try to import full document processor first
    try:
        from api.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Use full processor if dependencies are available
        if processor.is_supported(file_path):
            full_text, chunks = processor.extract_text(file_path)
            metadata = processor.get_document_metadata(file_path)
            metadata['article_title'] = article_title or Path(file_path).stem.replace('_', ' ').title()
            metadata['chunk_count'] = len(chunks)
            metadata['text_length'] = len(full_text)
            return full_text, chunks, metadata
    except ImportError:
        pass
    
    # Fall back to simple processor
    processor = SimpleDocumentProcessor()
    
    if not article_title:
        article_title = Path(file_path).stem.replace('_', ' ').replace('-', ' ').title()
    
    full_text, chunks = processor.extract_text(file_path)
    metadata = processor.get_document_metadata(file_path)
    metadata['article_title'] = article_title
    metadata['chunk_count'] = len(chunks)
    metadata['text_length'] = len(full_text)
    
    return full_text, chunks, metadata