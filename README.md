# KBAI - Knowledge Base AI API

**Enterprise-Grade AI-Powered Knowledge Management Platform**

A comprehensive Knowledge Base AI API that combines advanced semantic search, real-time AI query processing, enterprise authentication, and intelligent document management. Built for scalability, observability, and seamless integration into enterprise workflows.

## 🏢 Enterprise Features

### Core AI Capabilities
- **🤖 Advanced AI Query Processing** - GPT-4 powered semantic search with context-aware responses
- **🔍 Hybrid Search Engine** - Vector similarity + full-text search for optimal relevance
- **🔧 Intelligent Tool Integration** - Dynamic tool execution (datetime, web search, custom tools)
- **📊 Source Attribution** - Complete traceability with relevance scoring and source linking
- **🧠 Context-Aware Responses** - Multi-source synthesis with intelligent prompt construction

### Enterprise Infrastructure
- **🔐 Dual Authentication System** - JWT tokens for interactive access, API keys for programmatic integration
- **📈 Comprehensive Monitoring** - Prometheus metrics, request tracing, real-time dashboards
- **🛡️ Security & Compliance** - CORS configuration, request limits, audit trails
- **⚡ High Performance** - Optimized indexing, background processing, efficient caching
- **🔄 Real-time Updates** - Live metrics streaming, automatic index rebuilds

### Document & Knowledge Management
- **📁 Intelligent Document Processing** - PDF/DOCX upload with automatic text extraction and chunking
- **📚 Knowledge Base Management** - Structured article storage with metadata and categorization
- **❓ FAQ System** - Dynamic FAQ management with automatic indexing
- **🗂️ Project Organization** - Multi-tenant project structure with isolated data

## 🚀 Quick Start

### System Requirements

- **Python**: 3.8+ with pip and venv support
- **Database**: SQLite3 (embedded)
- **Memory**: Minimum 1GB RAM (2GB+ recommended for large documents)
- **Storage**: 100MB+ free space for indexes and data

### Production-Ready Installation

1. **Clone and Setup Environment**
   ```bash
   git clone https://github.com/muneebakhter/KBAI.git
   cd KBAI
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure for Production**
   ```bash
   cp .env.example .env
   # REQUIRED: Edit .env with production settings:
   # - Set OPENAI_API_KEY for AI features
   # - Change AUTH_SIGNING_KEY for JWT security  
   # - Update KBAI_API_TOKEN for API access
   # - Configure ALLOWED_ORIGINS for CORS
   ```

3. **Initialize System**
   ```bash
   ./init_db.sh                    # Initialize SQLite database
   python3 create_sample_data.py   # Create sample projects (ACLU, ASPCA)
   python3 prebuild_kb.py          # Build search indexes
   ```

4. **Launch API Server**
   ```bash
   ./run_api.sh
   ```

### Access Points

- **API Base**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Enterprise Dashboard**: `http://localhost:8000/admin`
- **Frontend Interface**: `http://localhost:8000/frontend`
- **Architecture Overview**: `http://localhost:8000/` (System Documentation)

### Quick Validation

```bash
# Health check
curl http://localhost:8000/healthz

# Test authentication (use API key from startup logs)
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:8000/v1/test/ping

# Sample AI query
curl -X POST http://localhost:8000/v1/query \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What does ASPCA stand for?"}'
```

## 🏗️ Enterprise Architecture

### Platform Overview

The KBAI platform provides a comprehensive enterprise architecture with multiple access points and interfaces:

#### **🌐 Main Route (/) - System Architecture Dashboard** 
`http://localhost:8000/`

Interactive architectural overview featuring:
- **System Flow Diagrams** - Visual representation of query processing pipeline
- **Component Architecture** - Detailed view of microservice interactions  
- **API Endpoint Catalog** - Complete route documentation with descriptions
- **Tool Chain Visualization** - AI tool integration and execution flows
- **Performance Monitoring** - System health and metrics overview

#### **📊 Admin Dashboard (/admin)**
`http://localhost:8000/admin`

Enterprise-grade administrative interface with:
- **Real-time Metrics** - Live charts and performance statistics
- **Request Tracing** - Detailed audit trail with filtering and drill-down
- **Authentication Management** - JWT and API key administration
- **System Monitoring** - Health checks, uptime tracking, and alerts
- **Server-Sent Events** - Low-latency real-time updates
- **Dual Authentication** - Support for both JWT tokens and API keys

#### **🎯 Frontend Interface (/frontend)**
`http://localhost:8000/frontend` 

Interactive user interface providing:
- **AI Query Interface** - Natural language query processing
- **Project Management** - Visual project selection and management
- **Document Upload** - Drag-and-drop document processing
- **Knowledge Base Browser** - FAQ and article exploration
- **Authentication Portal** - User login and session management

### System Components

```
KBAI Enterprise Platform
├── 🌐 Web Layer
│   ├── FastAPI Application (main.py)
│   ├── Authentication Middleware (JWT + API Key)
│   ├── CORS & Security Middleware
│   └── Request Tracing Middleware
├── 🤖 AI Processing Engine
│   ├── OpenAI Integration (GPT-4)
│   ├── Vector Search Engine
│   ├── Full-text Search (SQLite FTS)
│   └── Tool Chain Manager
├── 📊 Data Layer
│   ├── SQLite Database (requests, sessions, traces)
│   ├── File System Storage (projects, documents)
│   ├── Vector Indexes (embeddings)
│   └── Search Indexes (FTS)
├── 🔧 Tool Framework
│   ├── DateTime Tool
│   ├── Web Search Tool
│   └── Extensible Tool Manager
└── 📈 Observability
    ├── Prometheus Metrics
    ├── Request Tracing
    ├── Health Monitoring
    └── Real-time Streaming
```

## 📚 API Documentation & Access Points

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs` - Complete API testing interface
- **ReDoc**: `http://localhost:8000/redoc` - Beautiful API documentation  
- **Architecture Overview**: `http://localhost:8000/` - System design and flow diagrams

### Management Interfaces
- **Admin Dashboard**: `http://localhost:8000/admin` - Enterprise monitoring and administration
- **Frontend Interface**: `http://localhost:8000/frontend` - User-friendly query and management interface

## 🔑 Enterprise Authentication

The platform implements enterprise-grade dual authentication supporting both interactive and programmatic access patterns.

### Authentication Methods

#### 1. JWT Token Authentication (Interactive Users)

**Use Case**: Web applications, user interfaces, scoped access control
**Features**: Expiration handling, scope-based permissions, session management

```bash
# Obtain JWT token
curl -X POST http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin", 
    "client_name": "my-application",
    "scopes": ["read:basic", "write:projects"],
    "ttl_seconds": 3600
  }'

# Use JWT token for API calls
curl -H "Authorization: Bearer <jwt-token>" \
  http://localhost:8000/v1/test/ping
```

#### 2. API Key Authentication (Programmatic Access)

**Use Case**: Scripts, integrations, CI/CD pipelines, full system access
**Features**: Long-lived tokens, full permissions, simple header-based auth

```bash
# Configure API key (set in environment or auto-generated at startup)
export KBAI_API_TOKEN="your-secure-api-key"

# Use API key for programmatic access
curl -H "X-API-Key: your-api-key" \
  http://localhost:8000/v1/test/ping
```

### Security Features

- **JWT Signing**: Configurable signing keys with HS256 algorithm
- **Scope-based Access**: Granular permission control for JWT tokens
- **Request Logging**: All authenticated requests traced and audited
- **Header Scrubbing**: Sensitive authentication headers excluded from logs
- **CORS Protection**: Configurable cross-origin resource sharing
- **Rate Limiting**: Request body size limits prevent abuse

## 🤖 Advanced AI Query Processing

### Enterprise AI Capabilities

The KBAI platform provides state-of-the-art AI query processing with enterprise-grade reliability and performance.

#### **Hybrid Search Architecture**
- **Vector Similarity Search** - Semantic understanding using embeddings
- **Full-Text Search** - Keyword matching with SQLite FTS5
- **Relevance Scoring** - Intelligent ranking and source attribution
- **Multi-source Synthesis** - Combining results from FAQs, KB articles, and documents

#### **AI Query Workflow**

```bash
# Enterprise AI Query Example
curl -X POST http://localhost:8000/v1/query \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "95",
    "question": "What are the emergency procedures for animal rescue?",
    "max_sources": 5,
    "use_tools": true
  }'
```

#### **Enterprise Response Format**

```json
{
  "answer": "Comprehensive AI-generated response synthesized from multiple sources",
  "sources": [
    {
      "id": "kb-article-uuid",
      "type": "kb_article", 
      "title": "Emergency Animal Rescue Procedures",
      "url": "/v1/projects/95/kb/kb-article-uuid",
      "relevance_score": 24.7,
      "file_attachment": true
    }
  ],
  "project_id": "95",
  "timestamp": "2025-01-13T10:30:45.123Z",
  "tools_used": [
    {
      "tool": "datetime",
      "result": "Current emergency contact hours: 24/7 availability"
    }
  ],
  "processing_time_ms": 1247,
  "model_used": "gpt-4o-mini"
}
```

#### **Intelligent Tool Integration**

The AI system automatically determines when to use tools based on query context:

- **📅 DateTime Tool** - Time-sensitive queries, business hours, scheduling
- **🌐 Web Search Tool** - Real-time information, current events, external data
- **🔧 Custom Tools** - Extensible framework for domain-specific functionality

#### **Query Optimization Features**

- **Context-Aware Prompts** - Dynamic prompt construction based on available sources
- **Chunk-based Processing** - Efficient handling of large documents
- **Source Deduplication** - Intelligent filtering of redundant information  
- **Relevance Thresholds** - Quality control for source inclusion

## 📁 Enterprise Document Management

### Document Processing Pipeline

The platform provides intelligent document processing with automatic knowledge base integration.

#### **Supported Formats**
- **PDF Documents** - Text extraction with layout preservation
- **Microsoft Word** - DOCX files with formatting retention
- **Text Files** - Direct content ingestion
- **Future Support** - PowerPoint, Excel, markdown files

#### **Document Upload & Processing**

```bash
# Upload document with automatic processing
curl -X POST http://localhost:8000/v1/projects/95/documents \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@company_policies.pdf" \
  -F "article_title=Company Policy Manual 2024"
```

#### **Intelligent Document Features**

- **Automatic Chunking** - Large documents split into searchable segments
- **Metadata Extraction** - Title, author, creation date preservation
- **Content Indexing** - Immediate vector and full-text search integration
- **Source Linking** - Direct access to original files through API
- **Attachment Management** - Secure file storage with retrieval URLs

#### **Document Retrieval**

```bash
# Get processed document content
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/projects/95/kb/{document_id}"

# Download original file
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/projects/95/kb/{document_id}" \
  -o "downloaded_document.pdf"
```

### Knowledge Base Architecture

#### **Content Types**
- **FAQ Entries** - Question/answer pairs with instant searchability
- **Knowledge Articles** - Structured content with titles and rich text
- **Document Chunks** - Processed document segments with source attribution
- **Metadata Records** - Searchable document properties and classifications

#### **Automatic Processing**
- **Index Rebuilding** - Automatic search index updates after content changes
- **Vector Embeddings** - Semantic search capability for all content
- **Cross-References** - Intelligent linking between related content
- **Version Control** - Change tracking and content history

## 🔧 AI Tools Framework

### Enterprise Tool Integration

The platform features an extensible AI tools framework for dynamic capability expansion.

#### **Built-in Tools**

**📅 DateTime Tool**
```bash
# Get current time and date information
curl -X POST http://localhost:8000/v1/tools/datetime \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**🌐 Web Search Tool**
```bash
# Perform real-time web searches (when available)
curl -X POST http://localhost:8000/v1/tools/web_search \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "latest AI developments 2024"}'
```

#### **Tool Discovery**

```bash
# List all available tools with capabilities
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/tools"
```

Response includes tool metadata, parameters, and usage examples:

```json
{
  "tools": [
    {
      "name": "datetime",
      "description": "Get current date, time, and timezone information",
      "parameters": {},
      "examples": ["What time is it?", "What's today's date?"]
    },
    {
      "name": "web_search", 
      "description": "Search the web for current information",
      "parameters": {"query": "string"},
      "examples": ["Latest news about...", "Current weather in..."]
    }
  ]
}
```

#### **Automatic Tool Selection**

The AI system intelligently determines when to use tools based on query analysis:

- **Time-related queries** → DateTime tool activation
- **Current events/real-time data** → Web search tool activation  
- **Mathematical calculations** → Future calculator tool
- **Custom business logic** → Extensible tool framework

#### **Tool Extensibility**

The framework supports custom tool development:

```python
# Example custom tool structure
from tools.base import BaseTool

class CustomBusinessTool(BaseTool):
    name = "business_hours"
    description = "Check business operating hours and availability"
    
    def execute(self, location: str = None) -> dict:
        # Custom business logic
        return {"status": "open", "hours": "9 AM - 5 PM"}
```

## 🧪 Enterprise Testing & Validation

### Comprehensive Test Suite

The platform includes enterprise-grade testing with full API coverage and integration validation.

#### **Automated Integration Testing**

```bash
# Complete automated test suite
./test_combined_api.sh
```

**Test Coverage Includes:**
- ✅ **System Health** - Health checks and readiness validation
- ✅ **Authentication** - JWT and API key authentication flows  
- ✅ **Project Management** - CRUD operations and project lifecycle
- ✅ **Document Processing** - Upload, indexing, and retrieval workflows
- ✅ **AI Query Processing** - Semantic search and tool integration
- ✅ **FAQ Management** - Create, read, update, delete operations
- ✅ **Knowledge Base** - Article management and search integration
- ✅ **Index Management** - Rebuild triggers and status monitoring
- ✅ **Request Tracing** - Audit trail validation and filtering
- ✅ **Tool Execution** - AI tool functionality and integration

#### **Manual Testing Walkthrough**

```bash
# Follow the comprehensive step-by-step guide
cat walkthrough.md
```

The walkthrough provides detailed manual testing covering:
- Environment setup and configuration
- Database initialization and sample data creation
- Authentication method testing
- Core functionality validation
- Document upload and processing
- AI query testing with source attribution
- Monitoring and observability features

#### **Performance Testing**

```bash
# Load testing example with curl
for i in {1..100}; do
  curl -X POST http://localhost:8000/v1/query \
    -H "X-API-Key: YOUR_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"project_id": "95", "question": "performance test query"}' &
done
wait

# Check performance metrics
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/metrics/summary"
```

#### **API Validation Tools**

**Using Swagger UI**
- Access `http://localhost:8000/docs`
- Interactive API testing with request/response validation
- Authentication testing with JWT and API keys
- Schema validation and example requests

**Using cURL Scripts**
```bash
# Test all endpoints systematically
API_KEY="your-api-key-here"
BASE_URL="http://localhost:8000"

# Health endpoints
curl $BASE_URL/healthz
curl $BASE_URL/readyz

# Authentication
curl -X POST $BASE_URL/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin", "client_name": "test"}'

# Projects
curl -H "X-API-Key: $API_KEY" $BASE_URL/v1/projects

# AI Query
curl -X POST $BASE_URL/v1/query \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "test query"}'
```

### Quality Assurance

#### **Test Data Management**
- **Sample Projects** - Pre-configured ACLU and ASPCA organizations
- **Test Documents** - Sample DOCX file for document processing validation
- **Sample Queries** - Predefined test cases for AI functionality
- **Cleanup Scripts** - Reset environment to pristine state

#### **Error Handling Validation**
- **Invalid Authentication** - 401 Unauthorized responses
- **Missing Resources** - 404 Not Found handling
- **Malformed Requests** - 400 Bad Request validation
- **Server Errors** - 500 Internal Server Error logging
- **Rate Limiting** - Request size and frequency limits

#### **Data Integrity Testing**
- **Index Consistency** - Vector and full-text search synchronization
- **File Attachment Validation** - Original document preservation
- **Cross-reference Integrity** - Source attribution accuracy
- **Concurrent Access** - Multi-user data consistency

## 📊 Complete API Reference

### 🔐 Authentication & Authorization

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/v1/auth/modes` | Get available authentication methods | ❌ |
| `POST` | `/v1/auth/token` | Issue JWT token for interactive access | ❌ |

### 🧪 System Health & Testing

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/healthz` | Basic health check (returns "ok") | ❌ |
| `GET` | `/readyz` | Readiness check (returns "ready") | ❌ |
| `GET` | `/v1/test/ping` | Authenticated endpoint test | ✅ |

### 🗂️ Project Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/v1/projects` | List all projects with metadata | ✅ |
| `POST` | `/v1/projects` | Create or update project | ✅ |
| `GET` | `/v1/projects/{id}` | Get specific project details | ✅ |
| `DELETE` | `/v1/projects/{id}` | Deactivate project (soft delete) | ✅ |
| `GET` | `/v1/projects/{id}/stats` | Get project statistics and metrics | ✅ |

### ❓ FAQ Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/v1/projects/{id}/faqs` | List all FAQs for project | ✅ |
| `POST` | `/v1/projects/{id}/faqs/add` | Add new FAQ with auto-indexing | ✅ |
| `GET` | `/v1/projects/{id}/faqs/{faq_id}` | Get FAQ details or download source file | ✅ |
| `DELETE` | `/v1/projects/{id}/faqs/{faq_id}` | Delete FAQ and rebuild indexes | ✅ |
| `POST` | `/v1/projects/{id}/faqs:batch_upsert` | Bulk FAQ operations | ✅ |

### 📚 Knowledge Base Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/v1/projects/{id}/kb` | List all knowledge base articles | ✅ |
| `POST` | `/v1/projects/{id}/kb/add` | Add new KB article with indexing | ✅ |
| `GET` | `/v1/projects/{id}/kb/{kb_id}` | Get KB article or download source document | ✅ |
| `DELETE` | `/v1/projects/{id}/kb/{kb_id}` | Delete KB article and rebuild indexes | ✅ |
| `POST` | `/v1/projects/{id}/kb:batch_upsert` | Bulk knowledge base operations | ✅ |

### 📁 Document Processing

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/v1/projects/{id}/documents` | Upload and process PDF/DOCX files | ✅ |
| `POST` | `/v1/projects/{id}/ingest` | Ingest document content with metadata | ✅ |

### 🔍 Search & Indexing

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/v1/projects/{id}/rebuild-indexes` | Manually trigger index rebuild | ✅ |
| `GET` | `/v1/projects/{id}/build-status` | Check index build status and progress | ✅ |
| `POST` | `/v1/projects/{id}/reindex` | Legacy reindex endpoint | ✅ |

### 🤖 AI Query Processing

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/v1/query` | AI-powered query with source attribution | ✅ |

### 🔧 AI Tools

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/v1/tools` | List available AI tools and capabilities | ✅ |
| `POST` | `/v1/tools/{tool_name}` | Execute specific tool (datetime, web_search) | ✅ |

### 📈 Monitoring & Observability

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/metrics` | Prometheus metrics endpoint | ❌ |
| `GET` | `/v1/traces` | Request trace history with filtering | ✅ |
| `GET` | `/v1/traces/{trace_id}` | Detailed trace information | ✅ |
| `GET` | `/v1/metrics/summary` | Aggregated metrics summary | ✅ |

### 🖥️ Web Interfaces

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/` | System architecture overview and documentation | ❌ |
| `GET` | `/admin` | Enterprise admin dashboard | ❌* |
| `GET` | `/dashboard` | Dashboard redirect (alias for /admin) | ❌* |
| `GET` | `/frontend` | Interactive frontend interface | ❌* |

### 🛠️ Admin & Internal

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/admin/health/status` | Detailed system health with uptime | ✅ |
| `GET` | `/admin/metrics/stream` | Server-sent events for real-time metrics | ✅ |

**Note**: Web interfaces (marked with *) don't require API authentication but may require login through the interface itself.

## 🏗️ Enterprise Project Structure

### Repository Architecture

```
KBAI/ - Enterprise Knowledge Base AI Platform
├── 📁 app/                          # Core FastAPI Application
│   ├── main.py                      # Primary API server with 38+ endpoints
│   ├── models.py                    # Pydantic data models and schemas
│   ├── auth.py                      # JWT authentication and session management
│   ├── deps.py                      # Unified authentication dependencies
│   ├── storage.py                   # Database operations and data access
│   ├── middleware.py                # Request tracing and monitoring middleware
│   ├── ai_worker.py                 # AI processing engine and tool integration
│   ├── schema.sql                   # SQLite database schema definition
│   └── templates/                   # HTML interfaces and dashboards
│       ├── index.html               # System architecture overview (/)
│       ├── admin.html               # Enterprise admin dashboard (/admin)
│       └── frontend.html            # User interface (/frontend)
├── 📁 kb_api/                       # Knowledge Base Processing Engine
│   ├── document_processor.py        # PDF/DOCX text extraction and chunking
│   ├── simple_processor.py          # Text processing and normalization
│   ├── storage.py                   # File system and metadata management
│   ├── models.py                    # Knowledge base data structures
│   └── index_versioning.py          # Search index management and versioning
├── 📁 tools/                        # AI Tools Framework
│   ├── base.py                      # Base tool interface and contracts
│   ├── manager.py                   # Tool discovery and execution engine
│   ├── datetime_tool.py             # Date/time information tool
│   └── web_search_tool.py           # Web search integration tool
├── 📁 scripts/                      # Deployment and Management Scripts
│   ├── init_db.sh                   # Database initialization and schema setup
│   ├── run_api.sh                   # Production server launcher
│   ├── cleanup.sh                   # System cleanup and reset utility
│   └── test_combined_api.sh         # Comprehensive integration test suite
├── 📁 data/                         # Runtime Data and Indexes
│   ├── proj_mapping.txt             # Project registry and metadata
│   ├── {project_id}/               # Per-project data isolation
│   │   ├── faqs.json               # FAQ entries with metadata
│   │   ├── kb.json                 # Knowledge base articles
│   │   ├── index/                  # Search indexes (vector + FTS)
│   │   └── attachments/            # Uploaded document storage
│   └── logs/                       # Application logs and traces
├── 📄 Configuration Files
│   ├── .env.example                # Production configuration template
│   ├── requirements.txt            # Python dependencies with versions
│   └── README.md                   # Comprehensive documentation (this file)
├── 📄 Sample Data and Documentation
│   ├── create_sample_data.py       # Sample project creation (ACLU, ASPCA)
│   ├── prebuild_kb.py              # Index building and optimization
│   ├── walkthrough.md              # Step-by-step testing guide
│   └── ASPCATEST.docx             # Sample document for testing
└── 📄 Database and Runtime
    ├── app/kbai_api.db             # SQLite database (sessions, traces, metrics)
    └── .venv/                      # Python virtual environment
```

### Data Architecture

#### **Project Organization**
- **Multi-tenant Structure** - Isolated data per project ID
- **Hierarchical Storage** - Projects → FAQs/KB → Documents → Indexes
- **Metadata Management** - Comprehensive tracking of content and versions
- **Attachment Handling** - Secure file storage with retrieval mechanisms

#### **Database Schema**
```sql
-- Session management
CREATE TABLE sessions (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMP NOT NULL,
  scopes TEXT NOT NULL
);

-- Request tracing  
CREATE TABLE traces (
  id TEXT PRIMARY KEY,
  timestamp REAL NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  latency_ms REAL NOT NULL,
  ip_address TEXT,
  user_agent TEXT,
  headers_slim TEXT,
  query_params TEXT,
  body_sha256 TEXT,
  token_subject TEXT,
  error_message TEXT
);
```

#### **Search Architecture**
- **Vector Embeddings** - Semantic similarity using OpenAI embeddings
- **Full-Text Search** - SQLite FTS5 for keyword matching
- **Hybrid Ranking** - Combined relevance scoring algorithm
- **Index Versioning** - Automatic rebuild detection and management

### File System Layout

#### **Project Data Structure**
```
data/{project_id}/
├── faqs.json                    # Structured FAQ data with IDs
├── kb.json                      # Knowledge base articles with metadata
├── attachments/                 # Original uploaded files
│   ├── {uuid}.pdf              # Preserved original documents
│   └── {uuid}.docx             # With content-type mapping
└── index/                       # Search indexes
    ├── vector_index.json        # Embedding vectors and mappings
    ├── fts_index.db            # SQLite full-text search
    └── metadata.json           # Index version and statistics
```

#### **Configuration Management**
```bash
# Environment-based configuration
.env                            # Production settings (not in repo)
├── OPENAI_API_KEY             # AI processing capability
├── AUTH_SIGNING_KEY           # JWT security
├── KBAI_API_TOKEN             # API access key
├── TRACE_DB_PATH              # Database location
├── ALLOWED_ORIGINS            # CORS configuration
└── MAX_REQUEST_BYTES          # Security limits
```

## ⚙️ Enterprise Configuration

### Environment Configuration

All system configuration is managed through environment variables for security and deployment flexibility.

#### **Core Configuration Variables**

| Variable | Default | Description | Required |
|----------|---------|-------------|----------|
| `OPENAI_API_KEY` | *none* | OpenAI API key for AI processing | **Yes** for AI features |
| `AUTH_SIGNING_KEY` | `dev-signing-key-change-me` | JWT token signing key | **Production** |
| `KBAI_API_TOKEN` | *auto-generated* | API key for programmatic access | **Recommended** |

#### **Server Configuration**

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port number |
| `RELOAD` | `false` | Enable auto-reload for development |

#### **Database & Storage**

| Variable | Default | Description |
|----------|---------|-------------|
| `TRACE_DB_PATH` | `./app/kbai_api.db` | SQLite database file path |
| `DATA_DIR` | `./data` | Project data storage directory |

#### **Security & Limits**

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_REQUEST_BYTES` | `65536` | Maximum request body size (64KB) |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins (comma-separated) |
| `AUTH_JWT_ALG` | `HS256` | JWT signing algorithm |
| `AUTH_DEFAULT_TTL_SECONDS` | `3600` | Default token lifetime (1 hour) |

#### **AI & Processing**

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model for AI processing |
| `EMBEDDING_MODEL` | `text-embedding-ada-002` | Model for vector embeddings |

#### **Monitoring & Observability**

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_TRACING` | `true` | Enable request tracing |
| `ENABLE_METRICS` | `true` | Enable Prometheus metrics |
| `LOG_LEVEL` | `INFO` | Application logging level |

### Production Configuration Example

```bash
# Copy and customize the configuration template
cp .env.example .env

# Essential production settings
cat > .env << EOF
# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=false

# Security (CHANGE THESE!)
AUTH_SIGNING_KEY=$(openssl rand -hex 32)
KBAI_API_TOKEN=$(openssl rand -hex 16)

# AI Configuration (REQUIRED)
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini

# Security & CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
MAX_REQUEST_BYTES=1048576  # 1MB for large documents

# Database
TRACE_DB_PATH=/var/lib/kbai/kbai_api.db

# Monitoring
ENABLE_TRACING=true
ENABLE_METRICS=true
LOG_LEVEL=INFO
EOF
```

### Deployment Configurations

#### **Development Environment**
```bash
# .env.development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
ALLOWED_ORIGINS=*
AUTH_SIGNING_KEY=dev-signing-key-change-me
```

#### **Staging Environment**
```bash
# .env.staging  
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://staging.yourdomain.com
AUTH_SIGNING_KEY=staging-signing-key-unique
TRACE_DB_PATH=/opt/kbai/staging/kbai_api.db
```

#### **Production Environment**
```bash
# .env.production
DEBUG=false
RELOAD=false
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://yourdomain.com
AUTH_SIGNING_KEY=$(vault kv get -field=signing_key secret/kbai)
KBAI_API_TOKEN=$(vault kv get -field=api_token secret/kbai)
OPENAI_API_KEY=$(vault kv get -field=openai_key secret/kbai)
TRACE_DB_PATH=/var/lib/kbai/production/kbai_api.db
MAX_REQUEST_BYTES=10485760  # 10MB for enterprise documents
```

### Security Considerations

#### **Authentication Security**
- **JWT Signing Keys** - Use cryptographically secure random keys
- **Token Rotation** - Regular API key rotation recommended
- **Scope Limitations** - JWT tokens support granular permissions
- **Session Management** - Automatic cleanup of expired sessions

#### **Data Protection**
- **Request Sanitization** - Sensitive headers excluded from logs
- **File Validation** - Upload type and size restrictions
- **Path Traversal Protection** - Secure file storage isolation
- **Database Security** - Parameterized queries prevent injection

#### **Network Security**
- **CORS Configuration** - Restrict origins to known domains
- **Request Limits** - Body size limits prevent abuse
- **TLS Termination** - HTTPS recommended for production
- **Rate Limiting** - Consider reverse proxy rate limiting

## 🚀 Enterprise Deployment

### Production Deployment Options

#### **Containerized Deployment (Docker)**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x *.sh

EXPOSE 8000
CMD ["./run_api.sh"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  kbai-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AUTH_SIGNING_KEY=${AUTH_SIGNING_KEY}
      - KBAI_API_TOKEN=${KBAI_API_TOKEN}
      - ALLOWED_ORIGINS=https://yourdomain.com
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

#### **Kubernetes Deployment**

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kbai-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kbai-api
  template:
    metadata:
      labels:
        app: kbai-api
    spec:
      containers:
      - name: kbai-api
        image: kbai:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: kbai-secrets
              key: openai-api-key
        - name: AUTH_SIGNING_KEY
          valueFrom:
            secretKeyRef:
              name: kbai-secrets
              key: auth-signing-key
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: kbai-data-pvc
```

#### **Traditional Server Deployment**

```bash
# Production server setup script
#!/bin/bash

# Create application user
sudo useradd -r -s /bin/false kbai
sudo mkdir -p /opt/kbai /var/lib/kbai /var/log/kbai
sudo chown kbai:kbai /opt/kbai /var/lib/kbai /var/log/kbai

# Deploy application
sudo -u kbai git clone https://github.com/muneebakhter/KBAI.git /opt/kbai
cd /opt/kbai
sudo -u kbai python3 -m venv .venv
sudo -u kbai .venv/bin/pip install -r requirements.txt

# Configure environment
sudo -u kbai cp .env.example .env
# Edit .env with production settings

# Create systemd service
sudo tee /etc/systemd/system/kbai-api.service > /dev/null <<EOF
[Unit]
Description=KBAI Knowledge Base AI API
After=network.target

[Service]
Type=simple
User=kbai
Group=kbai
WorkingDirectory=/opt/kbai
Environment=PATH=/opt/kbai/.venv/bin
ExecStart=/opt/kbai/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable kbai-api
sudo systemctl start kbai-api
```

### Infrastructure Requirements

#### **Minimum System Requirements**
- **CPU**: 2 cores (4+ recommended for production)
- **RAM**: 2GB (4GB+ recommended for large documents)
- **Storage**: 1GB + data requirements
- **Network**: Outbound HTTPS for OpenAI API access

#### **Recommended Production Setup**
- **CPU**: 4+ cores for concurrent request handling
- **RAM**: 8GB+ for optimal performance and caching
- **Storage**: SSD with 10GB+ for database and indexes
- **Network**: Load balancer with SSL termination
- **Monitoring**: Prometheus + Grafana for metrics collection

### Scaling Considerations

#### **Horizontal Scaling**
- **Stateless Design** - API instances can be load balanced
- **Shared Database** - SQLite suitable for moderate loads, consider PostgreSQL for high volume
- **File Storage** - Use shared storage (NFS, S3) for multi-instance deployments
- **Session Affinity** - Not required due to stateless JWT authentication

#### **Performance Optimization**
- **Index Caching** - Pre-built indexes for faster query response
- **Connection Pooling** - Database connection management
- **Request Queueing** - Background processing for long-running operations
- **CDN Integration** - Static asset delivery optimization

## 🧹 System Maintenance

### Regular Maintenance Tasks

#### **Database Maintenance**
```bash
# Cleanup old traces (keep last 30 days)
sqlite3 app/kbai_api.db "DELETE FROM traces WHERE timestamp < datetime('now', '-30 days');"

# Vacuum database to reclaim space
sqlite3 app/kbai_api.db "VACUUM;"

# Backup database
cp app/kbai_api.db "backups/kbai_api_$(date +%Y%m%d_%H%M%S).db"
```

#### **Index Optimization**
```bash
# Rebuild all project indexes
python3 prebuild_kb.py

# Check index health for specific project
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/projects/95/build-status"
```

#### **Log Management**
```bash
# Rotate application logs
sudo logrotate -f /etc/logrotate.d/kbai-api

# Clean old request logs
find ~/.kbai -name "requests.jsonl.*" -mtime +30 -delete
```

### System Reset and Cleanup

#### **Complete System Reset**
```bash
# Use the provided cleanup script
./cleanup.sh
```

This removes:
- SQLite database and related files
- Project data directories and indexes
- Uploaded document attachments
- Python cache files and temporary data
- Application logs and traces

#### **Selective Cleanup**
```bash
# Remove specific project data
rm -rf data/{project_id}/

# Clear specific trace data
sqlite3 app/kbai_api.db "DELETE FROM traces WHERE path LIKE '/v1/projects/{project_id}%';"

# Rebuild indexes after cleanup
python3 prebuild_kb.py
```

### Monitoring and Alerting

#### **Health Monitoring**
```bash
# Set up health check monitoring
*/5 * * * * curl -f http://localhost:8000/healthz || echo "KBAI API health check failed" | mail -s "KBAI Alert" admin@yourdomain.com
```

#### **Performance Monitoring**
```bash
# Monitor response times
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/metrics/summary" | \
  jq '.p95_latency_ms' | \
  awk '{if($1 > 1000) print "High latency detected: " $1 "ms"}'
```

#### **Disk Space Monitoring**
```bash
# Monitor data directory usage
du -sh data/ | awk '{if($1 ~ /G/ && $1+0 > 5) print "High disk usage: " $1}'
```

## 🔒 Enterprise Security & Compliance

### Security Architecture

The platform implements enterprise-grade security with comprehensive protection layers.

#### **Authentication & Authorization**
- **Multi-factor Authentication** - JWT tokens with configurable scopes
- **API Key Management** - Secure programmatic access with rotation support
- **Session Security** - Automatic cleanup and expiration handling
- **Scope-based Access Control** - Granular permission management
- **Token Validation** - Cryptographic signature verification

#### **Data Protection**
- **Request Sanitization** - Sensitive header data excluded from logs
- **SQL Injection Prevention** - Parameterized queries and input validation
- **Path Traversal Protection** - Secure file system access controls
- **File Type Validation** - Upload restrictions and content verification
- **Data Encryption** - JWT payload encryption and secure storage

#### **Network Security**
- **CORS Configuration** - Cross-origin request controls
- **Request Size Limits** - Protection against payload overflow attacks
- **Rate Limiting** - Configurable request frequency controls
- **TLS Support** - HTTPS termination and secure transport
- **Header Security** - Security header injection and validation

#### **Audit & Compliance**
- **Complete Request Tracing** - Full audit trail with timing and metadata
- **Authentication Logging** - Security event tracking and monitoring
- **Error Tracking** - Exception logging and security incident detection
- **Data Access Logging** - File and database access audit trails
- **Compliance Reporting** - Structured log formats for compliance tools

### Security Best Practices

#### **Production Deployment**
```bash
# Generate secure authentication keys
AUTH_SIGNING_KEY=$(openssl rand -hex 32)
KBAI_API_TOKEN=$(openssl rand -hex 24)

# Configure restrictive CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://api.yourdomain.com

# Set appropriate request limits
MAX_REQUEST_BYTES=10485760  # 10MB max

# Enable comprehensive logging
LOG_LEVEL=WARNING
ENABLE_TRACING=true
```

#### **Network Configuration**
```nginx
# Example Nginx reverse proxy configuration
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Compliance Features

#### **Data Governance**
- **Data Retention** - Configurable trace and log retention policies
- **Right to Deletion** - User data removal and cleanup procedures
- **Data Export** - Structured data export for compliance requests
- **Access Logging** - Complete audit trail for data access events

#### **Security Monitoring**
- **Failed Authentication Tracking** - Brute force detection and alerting
- **Unusual Access Patterns** - Anomaly detection and reporting
- **Error Rate Monitoring** - Security incident detection
- **Resource Usage Tracking** - Abuse detection and prevention

## 📈 Enterprise Monitoring & Observability

### Comprehensive Monitoring Stack

The KBAI platform includes enterprise-grade monitoring, observability, and real-time analytics.

#### **🎛️ Admin Dashboard (`/admin`)**

**Access**: `http://localhost:8000/admin`

The enterprise admin dashboard provides comprehensive system oversight:

##### **Real-time Metrics**
- **Request Volume Charts** - Live traffic visualization with time-series data
- **Response Time Histograms** - Performance analysis and latency tracking  
- **Status Code Distribution** - Error rate monitoring and success metrics
- **Authentication Analytics** - JWT vs API key usage patterns
- **Project Activity Metrics** - Per-project query and document statistics

##### **Request Tracing & Audit**
- **Complete Request History** - Every API call logged with full context
- **Filterable Trace Table** - Search by method, path, status, user, time range
- **Detailed Trace Drill-down** - Headers, body, timing, authentication details
- **Error Investigation** - Exception tracking and debugging information
- **Security Audit Trail** - Authentication attempts and access patterns

##### **Live Monitoring Features**
- **Server-Sent Events (SSE)** - Real-time updates without page refresh
- **Dual Authentication Support** - Login with JWT tokens or API keys
- **Health Status Indicators** - System uptime, database connectivity
- **Memory and Performance Metrics** - Resource utilization tracking

##### **Dashboard Interface Elements**
```html
<!-- Live Connection Status -->
<div class="sse-indicator connected" title="Real-time connection active"></div>

<!-- Authentication Panel -->
<div class="auth-section">
  <input type="text" placeholder="Username" value="admin">
  <input type="password" placeholder="Password" value="admin">  
  <button onclick="authenticate()">Login (JWT)</button>
  <input type="text" placeholder="API Key">
  <button onclick="authenticateApiKey()">Use API Key</button>
</div>

<!-- Metrics Grid -->
<div class="charts-grid">
  <div class="chart-card">
    <canvas id="requestVolumeChart"></canvas>
  </div>
  <div class="chart-card">
    <canvas id="responseTimeChart"></canvas>
  </div>
</div>
```

#### **🌐 System Architecture Dashboard (`/`)**

**Access**: `http://localhost:8000/`

Interactive architectural documentation featuring:

##### **Visual Architecture Flow**
- **Query Processing Pipeline** - Step-by-step AI query workflow
- **Authentication Flow** - JWT and API key authentication processes  
- **Document Processing Chain** - Upload, extraction, indexing, retrieval
- **Tool Integration Workflow** - Dynamic tool selection and execution
- **Monitoring & Analytics Flow** - Data collection and visualization

##### **Component Documentation**
- **API Endpoint Catalog** - All 38+ endpoints with descriptions and examples
- **Technology Stack Overview** - FastAPI, SQLite, OpenAI, vector search
- **Data Flow Diagrams** - Information movement through system components
- **Security Architecture** - Authentication, authorization, and audit flows

##### **Interactive Navigation**
```javascript
// Tab-based interface with sections:
// - System Overview
// - API Endpoints  
// - Data Architecture
// - Security Model
// - Monitoring Setup
```

#### **🎯 Frontend Interface (`/frontend`)**

**Access**: `http://localhost:8000/frontend`

User-friendly interface for knowledge base interaction:

##### **Query Interface**
- **Natural Language Input** - Intuitive query composition
- **Project Selection** - Visual project picker with descriptions
- **Real-time Results** - Live search with source attribution
- **Authentication Portal** - User login and session management

##### **Document Management**
- **Drag-and-Drop Upload** - Simple document processing
- **Upload Progress Tracking** - Real-time processing status
- **Document Browser** - Visual knowledge base exploration
- **FAQ Management** - Add, edit, delete frequently asked questions

### System Health Endpoints

#### **Health Monitoring**
```bash
# Basic health check
curl http://localhost:8000/healthz
# Response: "ok"

# Detailed readiness check  
curl http://localhost:8000/readyz
# Response: "ready"

# Comprehensive system status (authenticated)
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/admin/health/status"
```

#### **Metrics Collection**

**Prometheus Metrics** (`/metrics`)
```bash
# Raw Prometheus metrics export
curl http://localhost:8000/metrics
```

**Aggregated Metrics Summary** (authenticated)
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/metrics/summary"
```

#### **Request Tracing**

**Trace History** (authenticated)
```bash
# Recent traces with filtering
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/traces?limit=50&status=200"

# Specific trace details
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/v1/traces/{trace_id}"
```

### Real-time Streaming

**Live Metrics Stream** (Server-Sent Events)
```bash
# Connect to live metrics feed
curl -H "X-API-Key: YOUR_API_KEY" \
  "http://localhost:8000/admin/metrics/stream"
```

Stream provides real-time updates for:
- New request traces
- System metrics changes  
- Health status updates
- Error notifications
- Performance alerts

## 🆕 Platform Evolution & Roadmap

### Current Release (v1.0)

This unified platform represents a significant evolution from separate components:

#### **Architecture Consolidation**
- ✅ **Unified API Server** - Single FastAPI application replacing separate services
- ✅ **Integrated AI Processing** - Built-in OpenAI integration with no external dependencies
- ✅ **Embedded Authentication** - JWT and API key support in core application
- ✅ **Comprehensive Monitoring** - Built-in tracing, metrics, and dashboards
- ✅ **Real-time Interfaces** - Live admin dashboard and user frontend

#### **Enhanced Capabilities**
- ✅ **Advanced Semantic Search** - Vector similarity + full-text hybrid search
- ✅ **Intelligent Document Processing** - PDF/DOCX upload with automatic chunking
- ✅ **Dynamic Tool Integration** - AI tools framework with datetime and web search
- ✅ **Source Attribution** - Complete traceability with relevance scoring
- ✅ **Enterprise Security** - Comprehensive authentication and audit trails

#### **Removed Legacy Components**
- ❌ **Separate AI Worker** - Functionality integrated into main application
- ❌ **Mock Endpoints** - Replaced with real AI-powered processing
- ❌ **External Dependencies** - Reduced complexity with unified architecture

### Future Roadmap

#### **Short-term Enhancements (Next 3 months)**
- 🔄 **Advanced Document Formats** - PowerPoint, Excel, markdown support
- 🔄 **Enhanced Tool Framework** - Calculator, calendar integration, custom tools
- 🔄 **Improved Caching** - Response caching and query optimization
- 🔄 **Bulk Operations** - Batch document upload and processing
- 🔄 **API Versioning** - Backward compatibility and feature flags

#### **Medium-term Goals (3-6 months)**
- 🎯 **PostgreSQL Support** - Enterprise database scaling option
- 🎯 **Microservices Architecture** - Component separation for high availability
- 🎯 **Advanced Analytics** - Usage patterns, query insights, performance metrics
- 🎯 **Multi-language Support** - Internationalization and localization
- 🎯 **Advanced Security** - OAuth2, SAML, multi-factor authentication

#### **Long-term Vision (6+ months)**
- 🚀 **Machine Learning Pipeline** - Custom model training and fine-tuning
- 🚀 **GraphQL API** - Alternative query interface for complex relationships
- 🚀 **Real-time Collaboration** - Multi-user editing and commenting
- 🚀 **Enterprise Integrations** - Slack, Teams, SharePoint connectors
- 🚀 **Cloud-native Deployment** - Kubernetes operators and helm charts

### Migration Guide

For users upgrading from previous versions:

#### **From Legacy AI Worker Setup**
1. **Stop separate services** - No longer need ai_worker.py server
2. **Update configuration** - Consolidate environment variables
3. **Migrate data** - Use existing project data and indexes
4. **Update client code** - Single API endpoint for all functionality
5. **Test authentication** - Verify JWT and API key flows

#### **Database Migration**
```bash
# Backup existing data
cp app/kbai_api.db app/kbai_api.db.backup

# Run migration script (if applicable)
python3 migrate_database.py

# Verify migration
./test_combined_api.sh
```

## 🤝 Enterprise Support & Contributing

### Professional Support

#### **Community Support**
- **GitHub Issues** - Bug reports and feature requests
- **Documentation** - Comprehensive guides and API reference
- **Test Suite** - Validation tools and integration examples

#### **Enterprise Support Options**
- **Professional Services** - Custom implementation and integration
- **Priority Support** - Dedicated support channels and SLA
- **Custom Development** - Feature development and customization
- **Training & Consulting** - Team training and best practices

### Contributing to the Platform

#### **Development Process**
1. **Fork the Repository** - Create your own copy for development
2. **Create Feature Branch** - Isolate changes in topic branches
3. **Follow Code Standards** - Maintain code quality and documentation
4. **Add Tests** - Ensure comprehensive test coverage
5. **Submit Pull Request** - Include detailed description and testing

#### **Development Setup**
```bash
# Clone and setup development environment
git clone https://github.com/muneebakhter/KBAI.git
cd KBAI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Setup pre-commit hooks
pre-commit install

# Run development server with auto-reload
RELOAD=true ./run_api.sh
```

#### **Code Quality Standards**
- **Type Hints** - Comprehensive typing for all functions
- **Documentation** - Docstrings for all public interfaces
- **Testing** - Unit tests and integration test coverage
- **Security** - Secure coding practices and vulnerability scanning
- **Performance** - Efficient algorithms and resource usage

### Enterprise Integration

#### **API Integration Patterns**
```python
# Python SDK example
import requests

class KBAIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def query(self, project_id: str, question: str) -> dict:
        response = requests.post(
            f"{self.base_url}/v1/query",
            headers=self.headers,
            json={"project_id": project_id, "question": question}
        )
        return response.json()

# Usage example
client = KBAIClient("https://api.yourdomain.com", "your-api-key")
result = client.query("95", "What are our company policies?")
```

#### **Webhook Integration**
```bash
# Example webhook for document processing completion
curl -X POST https://your-app.com/webhooks/kbai \
  -H "Content-Type: application/json" \
  -d '{
    "event": "document_processed",
    "project_id": "95",
    "document_id": "uuid-here",
    "status": "completed",
    "timestamp": "2025-01-13T10:30:45Z"
  }'
```

## 📄 License & Legal

### Open Source License

This project is released under the **MIT License**, providing:

- ✅ **Commercial Use** - Use in commercial applications and products
- ✅ **Modification** - Modify and adapt the code for your needs
- ✅ **Distribution** - Distribute copies and derivatives
- ✅ **Private Use** - Use privately without disclosure requirements

### Third-Party Dependencies

The platform includes dependencies with compatible licenses:
- **FastAPI** - MIT License (web framework)
- **SQLite** - Public Domain (database engine)
- **OpenAI** - Commercial API (requires separate agreement)
- **Python Libraries** - Various compatible open source licenses

### Privacy and Data Handling

#### **Data Processing Notice**
- **User Queries** - Processed through OpenAI API (subject to OpenAI terms)
- **Document Content** - Stored locally, embeddings may use external APIs
- **Request Traces** - Logged locally for monitoring and debugging
- **Authentication Data** - Stored securely with industry standards

#### **Compliance Considerations**
- **GDPR** - Supports data export and deletion requirements
- **CCPA** - Provides data access and deletion capabilities
- **SOC 2** - Audit trails and security controls available
- **HIPAA** - Additional controls required for healthcare use cases

## 🆘 Support & Resources

### Documentation Resources

- **📖 API Documentation** - Interactive Swagger UI at `/docs`
- **🎯 Quick Start Guide** - This README with comprehensive setup
- **📝 Step-by-Step Tutorial** - `walkthrough.md` for detailed testing
- **🏗️ Architecture Guide** - Visual documentation at `/` endpoint

### Getting Help

#### **Self-Service Resources**
1. **Check API Documentation** - `/docs` endpoint for complete reference
2. **Review Request Traces** - `/admin` dashboard for debugging
3. **Run Test Suite** - `./test_combined_api.sh` for validation
4. **Check Logs** - Application logs and trace database

#### **Community Support**
1. **GitHub Issues** - Report bugs and request features
2. **GitHub Discussions** - Community questions and best practices
3. **Documentation** - Comprehensive guides and examples
4. **Code Examples** - Reference implementations and patterns

#### **Professional Support**

For enterprise customers requiring dedicated support:

- **🎯 Priority Response** - Guaranteed response times and SLA
- **🔧 Custom Integration** - Tailored implementation assistance
- **📈 Performance Optimization** - Scaling and optimization consulting
- **🛡️ Security Review** - Security assessment and hardening
- **📚 Training Programs** - Team training and certification

Contact: [Insert contact information for professional support]

### Troubleshooting

#### **Common Issues**

**Database Connection Issues**
```bash
# Check database file permissions
ls -la app/kbai_api.db
# Recreate database if necessary
./init_db.sh
```

**Authentication Problems**
```bash
# Verify API key configuration
echo $KBAI_API_TOKEN
# Test authentication endpoint
curl -H "X-API-Key: $KBAI_API_TOKEN" http://localhost:8000/v1/test/ping
```

**AI Query Failures**
```bash
# Check OpenAI API key configuration
echo $OPENAI_API_KEY
# Test AI tools availability
curl -H "X-API-Key: $KBAI_API_TOKEN" http://localhost:8000/v1/tools
```

**Performance Issues**
```bash
# Check system resources
htop
# Monitor API metrics
curl -H "X-API-Key: $KBAI_API_TOKEN" http://localhost:8000/v1/metrics/summary
```

---

## 📞 Contact Information

**Repository**: https://github.com/muneebakhter/KBAI  
**Issues**: https://github.com/muneebakhter/KBAI/issues  
**Documentation**: Available at `/docs` endpoint when running  

**⚠️ Production Security Notice**: Always change default authentication credentials, use HTTPS in production, and regularly update API keys and signing keys for optimal security.