#!/usr/bin/env python3
"""
Simplified AI Worker for DARKBO
Provides minimal endpoints for querying knowledge bases with sources and external tools.
"""

import os
import json
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from fastapi import FastAPI, HTTPException, Path as FastAPIPath
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss
    from whoosh.index import open_dir
    from whoosh.qparser import QueryParser
    import openai
    from dotenv import load_dotenv
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

# Load environment variables from .env file (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, skip loading .env file
    pass

# Import from parent directory - these modules exist in the root
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb_api.models import FAQEntry, KBEntry
from kb_api.storage import FileStorageManager
try:
    from kb_api.document_processor import process_document_for_kb
except ImportError:
    from kb_api.simple_processor import process_document_for_kb
from kb_api.index_versioning import IndexBuilder, IndexVersionManager
from tools import ToolManager

# Additional imports for file handling
from fastapi import File, UploadFile, Form, BackgroundTasks
import uuid
import asyncio


# Pydantic models for API
class QueryRequest(BaseModel):
    project_id: str
    question: str

class Source(BaseModel):
    id: str
    type: str  # 'faq' or 'kb'
    title: str
    url: str
    relevance_score: float

class ToolUsage(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    execution_time: Optional[float] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    project_id: str
    timestamp: str
    tools_used: Optional[List[ToolUsage]] = None

class FAQCreateRequest(BaseModel):
    question: str
    answer: str

class KBArticleCreateRequest(BaseModel):
    title: str
    content: str

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    kb_entries_created: Optional[List[str]] = None
    index_build_started: bool = False
    
class IndexBuildResponse(BaseModel):
    success: bool
    message: str
    version: Optional[str] = None
    build_status: Optional[Dict[str, Any]] = None


class KnowledgeBaseRetriever:
    """Retrieves information from prebuilt indexes with versioning support"""
    
    def __init__(self, project_id: str, base_dir: str = "."):
        self.project_id = project_id
        self.base_dir = Path(base_dir)
        self.project_dir = self.base_dir / project_id
        self.version_manager = IndexVersionManager(project_id, base_dir)
        
        # Load metadata
        self.metadata = self._load_metadata()
        
        # Initialize indexes
        self.dense_index = None
        self.dense_metadata = None
        self.sparse_index = None
        self.embedding_model = None
        
        self._load_indexes()
    
    def _load_metadata(self) -> Dict:
        """Load index metadata from current version"""
        try:
            index_paths = self.version_manager.get_current_index_paths()
            meta_file = index_paths['meta']
            
            if meta_file.exists():
                with open(meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load metadata for {self.project_id}: {e}")
        
        return {"error": "No index metadata found"}
    
    def _load_indexes(self):
        """Load prebuilt indexes from current version"""
        if not HAS_DEPS:
            return
        
        try:
            index_paths = self.version_manager.get_current_index_paths()
            
            # Load dense index
            if self.metadata.get('indexes', {}).get('dense', {}).get('available'):
                dense_dir = index_paths['dense']
                index_file = dense_dir / "faiss.index"
                metadata_file = dense_dir / "metadata.json"
                
                if index_file.exists() and metadata_file.exists():
                    self.dense_index = faiss.read_index(str(index_file))
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        self.dense_metadata = json.load(f)
                    
                    # Load embedding model
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Load sparse index
            if self.metadata.get('indexes', {}).get('sparse', {}).get('available'):
                sparse_dir = index_paths['sparse']
                if sparse_dir.exists():
                    self.sparse_index = open_dir(str(sparse_dir))
                    
        except Exception as e:
            print(f"Warning: Could not load indexes for {self.project_id}: {e}")
    
    def reload_indexes(self):
        """Reload indexes after a rebuild"""
        self.metadata = self._load_metadata()
        self.dense_index = None
        self.dense_metadata = None
        self.sparse_index = None
        self.embedding_model = None
        self._load_indexes()
    
    def search_dense(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using dense vector similarity"""
        if not self.dense_index or not self.embedding_model:
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.dense_index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                # Convert numpy types to Python types to avoid type issues
                idx = int(idx)
                score = float(score)
                
                # Validate index bounds
                if 0 <= idx < len(self.dense_metadata):
                    result = self.dense_metadata[idx].copy()
                    result['score'] = score
                    results.append(result)
            
            return results
        except Exception as e:
            print(f"Dense search error: {str(e)}")
            return []
    
    def search_sparse(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search using sparse text search"""
        if not self.sparse_index:
            return []
        
        try:
            with self.sparse_index.searcher() as searcher:
                parser = QueryParser("content", self.sparse_index.schema)
                parsed_query = parser.parse(query)
                
                results = []
                search_results = searcher.search(parsed_query, limit=top_k)
                
                for hit in search_results:
                    results.append({
                        'id': hit['id'],
                        'type': hit['type'],
                        'score': hit.score,
                        'question': hit.get('question', ''),
                        'answer': hit.get('answer', ''),
                        'article': hit.get('title', ''),
                        'content': hit.get('content', '')
                    })
                
                return results
        except Exception as e:
            print(f"Sparse search error: {str(e)}")
            return []
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Hybrid search combining dense and sparse results"""
        dense_results = self.search_dense(query, top_k)
        sparse_results = self.search_sparse(query, top_k)
        
        # If no ML-based search available, use basic text matching
        if not dense_results and not sparse_results:
            return self.search_basic(query, top_k)
        
        # Combine and deduplicate results
        seen_ids = set()
        combined_results = []
        
        # Add dense results first (usually better for semantic similarity)
        for result in dense_results:
            if result['id'] not in seen_ids:
                result['search_type'] = 'dense'
                combined_results.append(result)
                seen_ids.add(result['id'])
        
        # Add sparse results
        for result in sparse_results:
            if result['id'] not in seen_ids:
                result['search_type'] = 'sparse'
                combined_results.append(result)
                seen_ids.add(result['id'])
        
        # Sort by score (descending)
        combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return combined_results[:top_k]
    
    def search_basic(self, query: str, top_k: int = 5) -> List[Dict]:
        """Basic text search fallback when dependencies aren't available"""
        try:
            # Load FAQ and KB data directly
            faqs, kb_entries = self._load_raw_data()
            
            results = []
            query_lower = query.lower()
            
            # Search in FAQs
            for faq in faqs:
                question_lower = faq.question.lower()
                answer_lower = faq.answer.lower()
                
                # Calculate improved relevance score
                score = self._calculate_relevance_score(query_lower, question_lower, answer_lower)
                
                if score > 0:
                    results.append({
                        'id': faq.id,
                        'type': 'faq',
                        'score': score,
                        'question': faq.question,
                        'answer': faq.answer,
                        'search_type': 'basic'
                    })
            
            # Search in KB entries
            for kb in kb_entries:
                article_lower = kb.article.lower()
                content_lower = kb.content.lower()
                
                # Calculate improved relevance score
                score = self._calculate_relevance_score(query_lower, article_lower, content_lower)
                
                if score > 0:
                    results.append({
                        'id': kb.id,
                        'type': 'kb',
                        'score': score,
                        'article': kb.article,
                        'content': kb.content,
                        'search_type': 'basic'
                    })
            
            # Sort by score (descending) and return top results
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Basic search error: {e}")
            return []
    
    def _load_raw_data(self) -> tuple[List[FAQEntry], List[KBEntry]]:
        """Load raw FAQ and KB data for basic search"""
        faqs = []
        kb_entries = []
        
        # Load FAQ data
        faq_file = self.project_dir / f"{self.project_id}.faq.json"
        if faq_file.exists():
            with open(faq_file, 'r', encoding='utf-8') as f:
                faq_data = json.load(f)
                faqs = [FAQEntry.from_dict(item) for item in faq_data]
        
        # Load KB data  
        kb_file = self.project_dir / f"{self.project_id}.kb.json"
        if kb_file.exists():
            with open(kb_file, 'r', encoding='utf-8') as f:
                kb_data = json.load(f)
                kb_entries = [KBEntry.from_dict(item) for item in kb_data]
        
        return faqs, kb_entries

    def _calculate_relevance_score(self, query_lower: str, primary_text: str, secondary_text: str) -> float:
        """
        Calculate improved relevance score for better matching.
        
        Args:
            query_lower: The search query in lowercase
            primary_text: Primary text to search (question for FAQ, article for KB)
            secondary_text: Secondary text to search (answer for FAQ, content for KB)
        
        Returns:
            Float score indicating relevance (higher = more relevant)
        """
        import re
        
        # Clean up query - remove punctuation and split into words
        query_words = re.findall(r'\w+', query_lower)
        
        if not query_words:
            return 0.0
            
        score = 0.0
        primary_matches = 0
        secondary_matches = 0
        
        # Count individual word matches
        for word in query_words:
            if word in primary_text:
                score += 2.0  # Primary text matches get higher weight
                primary_matches += 1
            elif word in secondary_text:
                score += 1.0  # Secondary text matches get lower weight
                secondary_matches += 1
        
        # Bonus for multiple word matches (indicates higher relevance)
        total_matches = primary_matches + secondary_matches
        if total_matches > 1:
            score += total_matches * 0.5  # Bonus for multiple matches
        
        # Give extra points for content words (non-stopwords) matching
        # Common stop words that should get less weight
        stop_words = {'what', 'is', 'the', 'a', 'an', 'are', 'was', 'were', 'how', 'when', 'where', 'why'}
        content_words_in_primary = 0
        content_words_in_secondary = 0
        
        for word in query_words:
            if word not in stop_words:  # Content word
                if word in primary_text:
                    content_words_in_primary += 1
                    score += 1.0  # Extra bonus for content words
                elif word in secondary_text:
                    content_words_in_secondary += 1
                    score += 0.5  # Extra bonus for content words
        
        # Bonus for high content word ratio in primary text
        content_words = [w for w in query_words if w not in stop_words]
        if content_words:
            content_word_ratio = content_words_in_primary / len(content_words)
            if content_word_ratio == 1.0:  # All content words found
                score += 2.0
            elif content_word_ratio >= 0.5:
                score += content_word_ratio * 1.0
        
        # Special bonus for exact phrase matching or high word coverage
        query_phrase = ' '.join(query_words)
        if query_phrase in primary_text:
            score += 3.0  # Big bonus for exact phrase match in primary text
        elif query_phrase in secondary_text:
            score += 1.5  # Smaller bonus for exact phrase match in secondary text
        
        # Bonus for high word coverage (many query words found)
        word_coverage_ratio = total_matches / len(query_words)
        if word_coverage_ratio >= 0.5:  # At least half the words match
            score += word_coverage_ratio * 1.0
            
        return score


class AIWorker:
    """Main AI worker class with document ingestion support"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.projects = self._load_projects()
        self.retrievers = {}  # Cache retrievers
        self.tool_manager = ToolManager()  # Initialize tool manager
        self.storage = FileStorageManager(str(self.base_dir))  # Storage manager
        
        # Initialize OpenAI client
        self.openai_client = None
        self.openai_model = "gpt-4o-mini"  # Default model for cost efficiency
        self._setup_openai()
    
    def _load_projects(self) -> Dict[str, str]:
        """Load project mapping"""
        mapping_file = self.base_dir / "proj_mapping.txt"
        projects = {}
        
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        # Support both pipe-separated (new) and tab-separated (old) formats
                        if '|' in line:
                            parts = line.split('|', 2)
                            if len(parts) >= 2:
                                project_id, name = parts[0].strip(), parts[1].strip()
                                projects[project_id] = name
                        elif '\t' in line:
                            project_id, name = line.split('\t', 1)
                            projects[project_id.strip()] = name.strip()
        
        return projects
    
    def _setup_openai(self):
        """Setup OpenAI client with API key from environment"""
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # User requested gpt-5-nano, but it may not exist yet. Try fallback models.
        model_preference = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4"]
        if "nano" in model.lower() or "gpt-5" in model.lower():
            print("🔬 User requested GPT-5-nano (not yet available), using best alternative...")
            model = "gpt-4o-mini"  # Best available alternative
        
        if api_key and api_key != "your_openai_api_key_here":
            try:
                # Try with additional configuration for better connectivity
                self.openai_client = openai.OpenAI(
                    api_key=api_key,
                    timeout=30.0,  # Increase timeout
                    max_retries=2   # Add retries
                )
                self.openai_model = model
                print(f"✅ OpenAI client initialized with model: {model}")
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            print("⚠️ No valid OpenAI API key found. AI responses will be limited to knowledge base content.")
            self.openai_client = None
    
    def get_retriever(self, project_id: str) -> KnowledgeBaseRetriever:
        """Get or create retriever for project"""
        if project_id not in self.retrievers:
            if project_id not in self.projects:
                raise ValueError(f"Project {project_id} not found")
            
            self.retrievers[project_id] = KnowledgeBaseRetriever(project_id, str(self.base_dir))
        
        return self.retrievers[project_id]
    
    def get_faq_by_id(self, project_id: str, faq_id: str) -> Optional[FAQEntry]:
        """Get FAQ entry by ID"""
        faq_file = self.base_dir / project_id / f"{project_id}.faq.json"
        if not faq_file.exists():
            return None
        
        with open(faq_file, 'r', encoding='utf-8') as f:
            faqs_data = json.load(f)
            for faq_data in faqs_data:
                if faq_data['id'] == faq_id:
                    return FAQEntry.from_dict(faq_data)
        
        return None
    
    def get_kb_by_id(self, project_id: str, kb_id: str) -> Optional[KBEntry]:
        """Get KB entry by ID"""
        kb_file = self.base_dir / project_id / f"{project_id}.kb.json"
        if not kb_file.exists():
            return None
        
        with open(kb_file, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
            for kb_item in kb_data:
                if kb_item['id'] == kb_id:
                    return KBEntry.from_dict(kb_item)
        
        return None
    
    def _generate_fallback_response(self, question: str, search_results: List[Dict], tools_used: List[ToolUsage], project_name: str = None) -> str:
        """Generate intelligent fallback response when AI is unavailable"""
        print("AI Agent: Generating fallback response (AI unavailable)")
        
        # Check for datetime tool results first
        datetime_result = None
        for tool in tools_used:
            if tool.tool_name == "datetime" and tool.success:
                datetime_result = tool.result.get('data', {})
                break
        
        if datetime_result:
            current_time = datetime_result.get('current_datetime', 'N/A')
            weekday = datetime_result.get('weekday', 'N/A')
            print(f"AI Agent: Using datetime tool result in fallback: {current_time}")
            return f"I'm ACD Direct's Knowledge Base AI System. The current date and time is {current_time} ({weekday}). For additional information, please check the sources provided."
        
        # Check if we have a direct FAQ match for phone number queries
        question_lower = question.lower()
        
        # Look for phone number in the top results
        if any(word in question_lower for word in ['phone', 'number', 'call', 'contact']):
            print("AI Agent: Detected phone/contact query in fallback")
            # First, look for specific phone number FAQs
            for result in search_results[:7]:  # Check top 7 results
                if result.get('type') == 'faq':
                    question_text = result.get('question', '').lower()
                    answer = result.get('answer', '')
                    
                    # If this FAQ is specifically about phone numbers, return the answer directly
                    if any(word in question_text for word in ['phone', 'number']) and answer:
                        # Check if the answer looks like a phone number
                        if any(char.isdigit() for char in answer) and len(answer.replace('-', '').replace(' ', '')) >= 10:
                            print(f"AI Agent: Found phone number FAQ in fallback")
                            return f"I'm ACD Direct's Knowledge Base AI System. Based on our FAQ database, the answer to your question is: {answer}"
            
            # If no specific phone number FAQ found, look for contact info that might contain numbers
            for result in search_results[:7]:
                if result.get('type') == 'faq':
                    answer = result.get('answer', '')
                    # Check if this contact-related answer contains a phone number pattern
                    if any(word in answer.lower() for word in ['phone', 'call']) and any(char.isdigit() for char in answer):
                        # Extract potential phone number
                        import re
                        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
                        matches = re.findall(phone_pattern, answer)
                        if matches:
                            print(f"AI Agent: Extracted phone number from FAQ in fallback")
                            return f"I'm ACD Direct's Knowledge Base AI System. Based on our FAQ database, the phone number is: {matches[0]}"
        
        # Look for direct FAQ matches
        if search_results:
            best_result = search_results[0]
            if best_result.get('type') == 'faq' and best_result.get('score', 0) > 5:
                answer = best_result.get('answer', '')
                if answer:
                    print(f"AI Agent: Using best FAQ match in fallback (score: {best_result.get('score', 0)})")
                    return f"I'm ACD Direct's Knowledge Base AI System. Based on our knowledge base: {answer}"
        
        # Generic fallback when we have sources but no direct match
        if search_results:
            print(f"AI Agent: Generic fallback with {len(search_results)} sources")
            return f"I'm ACD Direct's Knowledge Base AI System. I found some relevant information in our knowledge base, but I'm currently unable to provide a detailed response due to a temporary service issue. Please check the sources provided for more information."
        
        # Final fallback
        print("AI Agent: Final fallback response (no sources found)")
        return f"I'm ACD Direct's Knowledge Base AI System. I'm currently unable to access detailed information due to a temporary service issue. Please try again later or contact us directly."

    async def _generate_ai_response_with_kb_check(self, question: str, search_results: List[Dict], tools_used: List[ToolUsage], project_name: str = None) -> Optional[str]:
        """Generate AI response using OpenAI API with KB context and insufficient context detection"""
        if not self.openai_client:
            print("AI Agent: OpenAI client not available, skipping AI response generation")
            return None
        
        try:
            print("AI Agent: Preparing context for OpenAI API call with KB context check")
            
            # Prepare system prompt with insufficient context detection
            system_prompt = f"""You are ACD Direct's Knowledge Base AI System, a helpful and knowledgeable assistant. 
You have access to a comprehensive knowledge base and various tools to provide accurate information.

Your primary role is to:
1. Answer questions ONLY using the provided knowledge base context when available
2. Use tool results when they provide current or specific information
3. Introduce yourself appropriately when asked about your identity
4. Be helpful, accurate, and conversational
5. NEVER make up information that is not in the provided context
6. If you don't have enough specific information in the context to properly answer the question, respond with "INSUFFICIENT_CONTEXT" followed by a brief explanation

IMPORTANT: Only provide information that is explicitly available in the knowledge base context or tool results. Do not hallucinate or guess answers.

If the provided context does not contain enough information to answer the question adequately, you MUST start your response with "INSUFFICIENT_CONTEXT" and then explain what information is missing.

Project context: {project_name or 'Knowledge Base System'}"""

            # Prepare context from search results - Expand context window
            context_parts = []
            if search_results:
                context_parts.append("=== KNOWLEDGE BASE CONTEXT ===")
                print(f"AI Agent: Including {len(search_results)} KB results in context")
                for i, result in enumerate(search_results[:7], 1):  # Increased from 3 to 7 for better context
                    if result.get('type') == 'faq':
                        context_parts.append(f"{i}. FAQ - {result.get('question', 'N/A')}")
                        context_parts.append(f"   Answer: {result.get('answer', 'N/A')}")
                    else:
                        context_parts.append(f"{i}. Article - {result.get('article', 'N/A')}")
                        content = result.get('content', '')
                        # Removed content truncation to preserve full context
                        context_parts.append(f"   Content: {content}")
                    context_parts.append("")
            
            # Add tool results context (if any from previous steps like datetime)
            if tools_used:
                context_parts.append("=== TOOL RESULTS ===")
                print(f"AI Agent: Including {len(tools_used)} tool results in context")
                for tool in tools_used:
                    if tool.success and tool.result.get('data'):
                        context_parts.append(f"Tool: {tool.tool_name}")
                        context_parts.append(f"Result: {tool.result['data']}")
                        context_parts.append("")
            
            # Prepare user message
            context_text = "\n".join(context_parts) if context_parts else "No specific context available."
            user_message = f"""Question: {question}

Context:
{context_text}

Please provide a helpful response based ONLY on the question and available context above. 
- If the context contains enough information to answer the question, provide it directly and clearly.
- If the question is about your identity, introduce yourself as "ACD Direct's Knowledge Base AI System".
- If the context does not contain enough information to answer the question properly, start your response with "INSUFFICIENT_CONTEXT" and explain what information would be needed to answer the question."""

            print("AI Agent: Making OpenAI API call...")
            
            # Make OpenAI API call
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_completion_tokens=1500  # Increased from 500 to allow for more comprehensive responses
            )
            
            ai_answer = response.choices[0].message.content.strip()
            print(f"AI Agent: OpenAI API call successful, generated {len(ai_answer)} character response")
            
            if "INSUFFICIENT_CONTEXT" in ai_answer:
                print("AI Agent: AI indicated insufficient context for proper answer")
            else:
                print("AI Agent: AI successfully answered using available context")
            
            return ai_answer
            
        except Exception as e:
            print(f"AI Agent Error: Failed to generate AI response: {str(e)}")
            return None

    async def _generate_ai_response(self, question: str, search_results: List[Dict], tools_used: List[ToolUsage], project_name: str = None) -> Optional[str]:
        """Generate AI response using OpenAI API with RAG context"""
        if not self.openai_client:
            print("AI Agent: OpenAI client not available, skipping AI response generation")
            return None
        
        try:
            print("AI Agent: Preparing context for OpenAI API call")
            
            # Prepare system prompt
            system_prompt = f"""You are ACD Direct's Knowledge Base AI System, a helpful and knowledgeable assistant. 
You have access to a comprehensive knowledge base and various tools to provide accurate information.

Your primary role is to:
1. Answer questions ONLY using the provided knowledge base context when available
2. Use tool results when they provide current or specific information
3. Introduce yourself appropriately when asked about your identity
4. Be helpful, accurate, and conversational
5. NEVER make up information that is not in the provided context
6. If you don't have the specific information in the context, clearly state that you don't have access to that information

IMPORTANT: Only provide information that is explicitly available in the knowledge base context or tool results. Do not hallucinate or guess answers.

Project context: {project_name or 'Knowledge Base System'}"""

            # Prepare context from search results - Expand context window
            context_parts = []
            if search_results:
                context_parts.append("=== KNOWLEDGE BASE CONTEXT ===")
                print(f"AI Agent: Including {len(search_results)} KB results in context")
                for i, result in enumerate(search_results[:7], 1):  # Increased from 3 to 7 for better context
                    if result.get('type') == 'faq':
                        context_parts.append(f"{i}. FAQ - {result.get('question', 'N/A')}")
                        context_parts.append(f"   Answer: {result.get('answer', 'N/A')}")
                    else:
                        context_parts.append(f"{i}. Article - {result.get('article', 'N/A')}")
                        content = result.get('content', '')
                        # Removed content truncation to preserve full context
                        context_parts.append(f"   Content: {content}")
                    context_parts.append("")
            
            # Add tool results context
            if tools_used:
                context_parts.append("=== TOOL RESULTS ===")
                print(f"AI Agent: Including {len(tools_used)} tool results in context")
                for tool in tools_used:
                    if tool.success and tool.result.get('data'):
                        context_parts.append(f"Tool: {tool.tool_name}")
                        context_parts.append(f"Result: {tool.result['data']}")
                        context_parts.append("")
            
            # Prepare user message
            context_text = "\n".join(context_parts) if context_parts else "No specific context available."
            user_message = f"""Question: {question}

Context:
{context_text}

Please provide a helpful response based ONLY on the question and available context above. 
- If the context contains the answer, provide it directly and clearly.
- If the question is about your identity, introduce yourself as "ACD Direct's Knowledge Base AI System".
- If the context does not contain enough information to answer the question, clearly state that you don't have that specific information in your knowledge base."""

            print("AI Agent: Making OpenAI API call...")
            
            # Make OpenAI API call
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_completion_tokens=1500  # Increased from 500 to allow for more comprehensive responses
            )
            
            ai_answer = response.choices[0].message.content.strip()
            print(f"AI Agent: OpenAI API call successful, generated {len(ai_answer)} character response")
            return ai_answer
            
        except Exception as e:
            print(f"AI Agent Error: Failed to generate AI response: {str(e)}")
            return None
    
    async def answer_question(self, project_id: str, question: str, use_tools: bool = True) -> QueryResponse:
        """Generate answer with sources and structured AI flow"""
        print(f"\n=== AI AGENT PROCESSING QUERY ===")
        print(f"Project ID: {project_id}")
        print(f"Question: {question}")
        print(f"Tools enabled: {use_tools}")
        
        # Get retriever
        retriever = self.get_retriever(project_id)
        
        # STEP 1: Check if this is a time-based question
        tools_used = []
        datetime_keywords = ['time', 'date', 'when', 'today', 'now', 'current', 
                           'year', 'month', 'day', 'hour', 'minute', 'clock',
                           'calendar', 'schedule', 'deadline']
        
        is_time_based = any(keyword in question.lower() for keyword in datetime_keywords)
        
        if is_time_based and use_tools:
            print(f"\n--- STEP 1: Time-based query detected ---")
            print(f"AI Agent Context: Detected time-related keywords in query")
            
            try:
                # Use datetime tool for time-based questions
                tool_params = self._prepare_tool_parameters("datetime", question)
                print(f"AI Agent: Executing datetime tool with params: {tool_params}")
                
                tool_result = await self.tool_manager.execute_tool("datetime", **tool_params)
                print(f"AI Agent: Datetime tool result - Success: {tool_result.success}")
                
                if tool_result.success:
                    print(f"AI Agent: Current datetime: {tool_result.data.get('current_datetime', 'N/A')}")
                
                tools_used.append(ToolUsage(
                    tool_name="datetime",
                    parameters=tool_params,
                    result=tool_result.to_dict(),
                    success=tool_result.success,
                    execution_time=tool_result.execution_time
                ))
                
            except Exception as e:
                print(f"AI Agent Error: Failed to execute datetime tool: {str(e)}")
        else:
            print(f"\n--- STEP 1: Non-time-based query ---")
            print(f"AI Agent Context: No time-related keywords detected")
        
        # STEP 2: Search the knowledge base articles
        print(f"\n--- STEP 2: Searching Knowledge Base ---")
        print(f"AI Agent Context: Querying knowledge base for relevant information")
        
        search_results = retriever.search(question, top_k=5)
        print(f"AI Agent: Found {len(search_results)} results in knowledge base")
        
        # Log search results details
        for i, result in enumerate(search_results[:3]):  # Show top 3
            result_type = result.get('type', 'unknown')
            score = result.get('score', 0)
            title = result.get('question' if result_type == 'faq' else 'article', 'N/A')
            print(f"AI Agent: Result {i+1} - Type: {result_type}, Score: {score:.2f}, Title: {title[:60]}...")
        
        # Generate sources from KB results
        sources = []
        for result in search_results:
            source_type = result.get('type', 'unknown')
            
            if source_type == 'faq':
                title = f"FAQ: {result.get('question', 'Unknown Question')}"
                url = f"/v1/projects/{project_id}/faqs/{result['id']}"
            else:
                title = result.get('article', 'Unknown Article')
                url = f"/v1/projects/{project_id}/kb/{result['id']}"
            
            sources.append(Source(
                id=result['id'],
                type=source_type,
                title=title,
                url=url,
                relevance_score=result.get('score', 0.0)
            ))
        
        # STEP 3: Try to generate AI response with KB context first
        print(f"\n--- STEP 3: Attempting AI Response with Knowledge Base Context ---")
        print(f"AI Agent Context: Trying to answer using available KB context")
        
        project_name = self.projects.get(project_id, "Knowledge Base")
        ai_response = await self._generate_ai_response_with_kb_check(question, search_results, tools_used, project_name)
        
        # STEP 4: If AI indicates insufficient context and tools are enabled, try web search
        needs_web_search = False
        if ai_response and "INSUFFICIENT_CONTEXT" in ai_response and use_tools and not is_time_based:
            print(f"\n--- STEP 4: AI indicates insufficient context, using Web Search ---")
            print(f"AI Agent Context: AI determined KB context insufficient, attempting web search")
            needs_web_search = True
            
            try:
                # Use web search tool when AI indicates KB is insufficient
                web_search_params = self._prepare_tool_parameters("web_search", question)
                print(f"AI Agent: Executing web search with params: {web_search_params}")
                
                web_tool_result = await self.tool_manager.execute_tool("web_search", **web_search_params)
                print(f"AI Agent: Web search result - Success: {web_tool_result.success}")
                
                if web_tool_result.success and web_tool_result.data:
                    web_results = web_tool_result.data.get('results', [])
                    print(f"AI Agent: Found {len(web_results)} web search results")
                    
                    # Log web search results
                    for i, result in enumerate(web_results[:2]):  # Show top 2
                        title = result.get('title', 'N/A')
                        print(f"AI Agent: Web Result {i+1} - {title[:60]}...")
                
                tools_used.append(ToolUsage(
                    tool_name="web_search",
                    parameters=web_search_params,
                    result=web_tool_result.to_dict(),
                    success=web_tool_result.success,
                    execution_time=web_tool_result.execution_time
                ))
                
                # Regenerate AI response with both KB and web search results
                print(f"AI Agent Context: Regenerating response with KB + web search context")
                ai_response = await self._generate_ai_response(question, search_results, tools_used, project_name)
                
            except Exception as e:
                print(f"AI Agent Error: Failed to execute web search: {str(e)}")
                # Remove INSUFFICIENT_CONTEXT marker from response since web search failed
                if ai_response and "INSUFFICIENT_CONTEXT" in ai_response:
                    ai_response = ai_response.replace("INSUFFICIENT_CONTEXT", "").strip()
        
        elif ai_response and "INSUFFICIENT_CONTEXT" not in ai_response:
            print(f"\n--- STEP 4: AI successfully answered with Knowledge Base context ---")
            print(f"AI Agent Context: AI found sufficient information in KB context")
        elif not use_tools or is_time_based:
            print(f"\n--- STEP 4: Skipping web search (time-based query or tools disabled) ---")
            if ai_response and "INSUFFICIENT_CONTEXT" in ai_response:
                ai_response = ai_response.replace("INSUFFICIENT_CONTEXT", "").strip()
        
        # STEP 5: Final response generation and fallback handling
        print(f"\n--- STEP 5: Finalizing Response ---")
        print(f"AI Agent Context: Preparing final response")
        
        if not ai_response:
            print(f"AI Agent: AI response generation failed, using fallback")
            # Intelligent fallback when AI is unavailable
            ai_response = self._generate_fallback_response(question, search_results, tools_used, project_name)
        else:
            # Clean up any remaining INSUFFICIENT_CONTEXT markers
            if "INSUFFICIENT_CONTEXT" in ai_response:
                ai_response = ai_response.replace("INSUFFICIENT_CONTEXT", "").strip()
            print(f"AI Agent: Successfully generated final response ({len(ai_response)} characters)")
        
        print(f"AI Agent: Process completed with {len(tools_used)} tools used and {len(sources)} sources")
        print(f"=== AI AGENT PROCESSING COMPLETE ===\n")
        
        return QueryResponse(
            answer=ai_response,
            sources=sources,
            project_id=project_id,
            timestamp=datetime.utcnow().isoformat(),
            tools_used=tools_used if tools_used else None
        )
    
    def _prepare_tool_parameters(self, tool_name: str, question: str) -> Dict[str, Any]:
        """Prepare parameters for tool execution based on the question"""
        if tool_name == "datetime":
            # For datetime tool, check if user wants specific format
            if "format" in question.lower() or "yyyy" in question.lower() or "mm/dd" in question.lower():
                return {"format": "%Y-%m-%d %H:%M:%S"}
            return {}
        
        elif tool_name == "web_search":
            # For web search, use the question as the query
            return {"query": question, "max_results": 3}
        
        return {}
    
    def _incorporate_tool_result(self, question: str, tool_name: str, tool_data: Any, kb_results: List[Dict]) -> str:
        """Incorporate tool results into the answer"""
        
        if tool_name == "datetime":
            if isinstance(tool_data, dict):
                current_time = tool_data.get('current_datetime', '')
                weekday = tool_data.get('weekday', '')
                
                # Create a natural language response
                if any(word in question.lower() for word in ['time', 'clock']):
                    return f"The current time is {current_time}."
                elif any(word in question.lower() for word in ['date', 'today']):
                    return f"Today is {weekday}, {current_time.split('T')[0]}."
                else:
                    return f"The current date and time is {current_time} ({weekday})."
        
        elif tool_name == "web_search":
            if isinstance(tool_data, dict) and tool_data.get('results'):
                results = tool_data['results']
                
                # Only use web search if it has valid results and no datetime tool was used for time questions
                if results and not any(r.get('source') == 'error' for r in results):
                    # If we have KB results, combine them with web results
                    if kb_results:
                        kb_answer = kb_results[0].get('answer') or kb_results[0].get('content', '')[:200]
                        web_info = results[0].get('snippet', '') if results else ''
                        
                        if kb_answer and web_info:
                            return f"Based on our knowledge base: {kb_answer}\n\nAdditional current information: {web_info}"
                        elif kb_answer:
                            return kb_answer
                    
                    # If no KB results, use web results
                    if results:
                        top_result = results[0]
                        return f"According to current web sources: {top_result.get('snippet', 'No information available.')}"
        
        return None

    async def ingest_document(self, project_id: str, file, article_title: str = None) -> DocumentUploadResponse:
        """Ingest a document into the knowledge base"""
        try:
            # Validate project
            if project_id not in self.projects:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            # Validate file type
            if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
                return DocumentUploadResponse(
                    success=False,
                    message="Only PDF and DOCX files are supported"
                )
            
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Save uploaded file temporarily
            temp_file = f"/tmp/{doc_id}_{file.filename}"
            with open(temp_file, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            try:
                # Process document
                full_text, chunks, metadata = process_document_for_kb(
                    temp_file, 
                    article_title or Path(file.filename).stem
                )
                
                # Save attachment file
                attachment_filename = f"{doc_id}-kb{Path(file.filename).suffix}"
                self.storage.save_attachment(project_id, attachment_filename, content)
                
                # Create KB entries from chunks
                kb_entries = []
                created_ids = []
                
                for i, chunk in enumerate(chunks):
                    kb_entry = KBEntry.from_content(
                        project_id=project_id,
                        article=metadata['article_title'],
                        content=chunk,
                        source="upload",
                        source_file=attachment_filename,
                        chunk_index=i if len(chunks) > 1 else None
                    )
                    kb_entries.append(kb_entry)
                    created_ids.append(kb_entry.id)
                
                # Save KB entries
                if kb_entries:
                    self.storage.upsert_kb_entries(project_id, kb_entries)
                
                # Start index rebuild in background
                index_build_started = False
                try:
                    builder = IndexBuilder(project_id, str(self.base_dir))
                    if builder.version_manager.needs_rebuild():
                        # Start background task for index rebuild
                        asyncio.create_task(self._rebuild_indexes_async(project_id))
                        index_build_started = True
                except Exception as e:
                    print(f"Warning: Could not start index rebuild: {e}")
                
                return DocumentUploadResponse(
                    success=True,
                    message=f"Document processed successfully. Created {len(kb_entries)} KB entries.",
                    document_id=doc_id,
                    kb_entries_created=created_ids,
                    index_build_started=index_build_started
                )
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            return DocumentUploadResponse(
                success=False,
                message=f"Document processing failed: {str(e)}"
            )
    
    async def add_faq(self, project_id: str, question: str, answer: str) -> DocumentUploadResponse:
        """Add a new FAQ entry"""
        try:
            # Validate project
            if project_id not in self.projects:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            # Create FAQ entry
            faq = FAQEntry.from_qa(
                project_id=project_id,
                question=question.strip(),
                answer=answer.strip(),
                source="manual"
            )
            
            # Save FAQ
            created_ids, updated_ids = self.storage.upsert_faqs(project_id, [faq])
            
            # Start index rebuild in background
            index_build_started = False
            try:
                builder = IndexBuilder(project_id, str(self.base_dir))
                if builder.version_manager.needs_rebuild():
                    asyncio.create_task(self._rebuild_indexes_async(project_id))
                    index_build_started = True
            except Exception as e:
                print(f"Warning: Could not start index rebuild: {e}")
            
            action = "updated" if updated_ids else "created"
            return DocumentUploadResponse(
                success=True,
                message=f"FAQ {action} successfully",
                document_id=faq.id,
                kb_entries_created=[faq.id],
                index_build_started=index_build_started
            )
            
        except Exception as e:
            return DocumentUploadResponse(
                success=False,
                message=f"FAQ creation failed: {str(e)}"
            )
    
    async def delete_faq(self, project_id: str, faq_id: str) -> DocumentUploadResponse:
        """Delete a FAQ entry"""
        try:
            # Validate project
            if project_id not in self.projects:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            # Delete FAQ
            deleted = self.storage.delete_faq(project_id, faq_id)
            
            if not deleted:
                return DocumentUploadResponse(
                    success=False,
                    message=f"FAQ {faq_id} not found"
                )
            
            # Start index rebuild in background
            index_build_started = False
            try:
                builder = IndexBuilder(project_id, str(self.base_dir))
                if builder.version_manager.needs_rebuild():
                    asyncio.create_task(self._rebuild_indexes_async(project_id))
                    index_build_started = True
            except Exception as e:
                print(f"Warning: Could not start index rebuild: {e}")
            
            return DocumentUploadResponse(
                success=True,
                message=f"FAQ deleted successfully",
                document_id=faq_id,
                index_build_started=index_build_started
            )
            
        except Exception as e:
            return DocumentUploadResponse(
                success=False,
                message=f"FAQ deletion failed: {str(e)}"
            )
    
    async def add_kb_article(self, project_id: str, title: str, content: str) -> DocumentUploadResponse:
        """Add a new KB article entry"""
        try:
            # Validate project
            if project_id not in self.projects:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            # Create KB entry
            kb_entry = KBEntry.from_content(
                project_id=project_id,
                article=title.strip(),
                content=content.strip(),
                source="manual"
            )
            
            # Save KB entry
            created_ids, updated_ids = self.storage.upsert_kb_entries(project_id, [kb_entry])
            
            # Start index rebuild in background
            index_build_started = False
            try:
                builder = IndexBuilder(project_id, str(self.base_dir))
                if builder.version_manager.needs_rebuild():
                    asyncio.create_task(self._rebuild_indexes_async(project_id))
                    index_build_started = True
            except Exception as e:
                print(f"Warning: Could not start index rebuild: {e}")
            
            action = "updated" if updated_ids else "created"
            return DocumentUploadResponse(
                success=True,
                message=f"KB article {action} successfully",
                document_id=kb_entry.id,
                kb_entries_created=[kb_entry.id],
                index_build_started=index_build_started
            )
            
        except Exception as e:
            return DocumentUploadResponse(
                success=False,
                message=f"KB article creation failed: {str(e)}"
            )
    
    async def delete_kb_article(self, project_id: str, kb_id: str) -> DocumentUploadResponse:
        """Delete a KB article entry"""
        try:
            # Validate project
            if project_id not in self.projects:
                return DocumentUploadResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            # Delete KB entry
            deleted = self.storage.delete_kb_entry(project_id, kb_id)
            
            if not deleted:
                return DocumentUploadResponse(
                    success=False,
                    message=f"KB article {kb_id} not found"
                )
            
            # Start index rebuild in background
            index_build_started = False
            try:
                builder = IndexBuilder(project_id, str(self.base_dir))
                if builder.version_manager.needs_rebuild():
                    asyncio.create_task(self._rebuild_indexes_async(project_id))
                    index_build_started = True
            except Exception as e:
                print(f"Warning: Could not start index rebuild: {e}")
            
            return DocumentUploadResponse(
                success=True,
                message=f"KB article deleted successfully",
                document_id=kb_id,
                index_build_started=index_build_started
            )
            
        except Exception as e:
            return DocumentUploadResponse(
                success=False,
                message=f"KB article deletion failed: {str(e)}"
            )
    
    def get_faq_by_id(self, project_id: str, faq_id: str) -> Optional[FAQEntry]:
        """Get FAQ by ID"""
        return self.storage.get_faq_by_id(project_id, faq_id)
    
    def get_kb_by_id(self, project_id: str, kb_id: str) -> Optional[KBEntry]:
        """Get KB entry by ID"""
        return self.storage.get_kb_entry_by_id(project_id, kb_id)
    
    async def rebuild_indexes(self, project_id: str) -> IndexBuildResponse:
        """Manually trigger index rebuild"""
        try:
            if project_id not in self.projects:
                return IndexBuildResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            builder = IndexBuilder(project_id, str(self.base_dir))
            
            # Check if build is already in progress
            if builder.version_manager.is_building():
                return IndexBuildResponse(
                    success=False,
                    message="Index build already in progress",
                    build_status=builder.version_manager.get_build_status()
                )
            
            # Start build
            new_version = builder.build_new_version()
            
            # Reload retrievers to use new index
            if project_id in self.retrievers:
                self.retrievers[project_id].reload_indexes()
            
            return IndexBuildResponse(
                success=True,
                message=f"Index rebuild completed",
                version=new_version,
                build_status=builder.version_manager.get_build_status()
            )
            
        except Exception as e:
            return IndexBuildResponse(
                success=False,
                message=f"Index rebuild failed: {str(e)}"
            )
    
    async def get_build_status(self, project_id: str) -> IndexBuildResponse:
        """Get index build status"""
        try:
            if project_id not in self.projects:
                return IndexBuildResponse(
                    success=False,
                    message=f"Project {project_id} not found"
                )
            
            version_manager = IndexVersionManager(project_id, str(self.base_dir))
            build_status = version_manager.get_build_status()
            
            return IndexBuildResponse(
                success=True,
                message="Build status retrieved",
                build_status=build_status
            )
            
        except Exception as e:
            return IndexBuildResponse(
                success=False,
                message=f"Failed to get build status: {str(e)}"
            )
    
    async def _rebuild_indexes_async(self, project_id: str):
        """Background task to rebuild indexes"""
        try:
            builder = IndexBuilder(project_id, str(self.base_dir))
            new_version = builder.build_new_version()
            
            # Reload retrievers to use new index
            if project_id in self.retrievers:
                self.retrievers[project_id].reload_indexes()
                
            print(f"Background index rebuild completed for project {project_id}, version {new_version}")
            
        except Exception as e:
            print(f"Background index rebuild failed for project {project_id}: {e}")