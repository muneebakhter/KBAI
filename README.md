# KBAI Combined API

A professional Knowledge Base AI API that combines advanced AI query processing with JWT authentication, request tracing, project management, and comprehensive document processing capabilities.

## ✨ Features

- **🤖 AI-Powered Query Processing** - Advanced semantic search with OpenAI integration and tool execution
- **🔐 Dual Authentication** - Both JWT tokens and API key authentication
- **📊 Request Tracing** - Comprehensive logging of all API requests and responses
- **📈 Metrics & Monitoring** - Prometheus metrics and performance monitoring
- **🗂️ Project Management** - Create and manage knowledge base projects
- **❓ FAQ Management** - Add, update, and manage frequently asked questions
- **📚 Knowledge Base** - Store and organize knowledge base articles with vector search
- **📁 Document Processing** - Upload and process PDF/DOCX files with automatic indexing
- **🔧 AI Tools Integration** - Datetime, web search, and extensible tool framework
- **📱 Admin Dashboard** - Web-based administration interface
- **🏗️ SQLite Database** - Simple, reliable SQLite3 database storage

## 🚀 Quick Start

### Prerequisites

- Python 3.8+ 
- SQLite3

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KBAI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings including OpenAI API key
   ```

4. **Initialize the database**
   ```bash
   ./init_db.sh
   ```

5. **Create sample data and build indexes**
   ```bash
   python3 create_sample_data.py
   python3 prebuild_kb.py
   ```

6. **Start the combined API server**
   ```bash
   ./run_api.sh
   ```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc  
- **Admin Dashboard**: http://localhost:8000/admin

## 🔑 Authentication

The API supports two authentication methods:

### 1. JWT Token Authentication (Interactive)

For interactive access or when you need scoped permissions:

#### Getting a JWT Token

```bash
curl -X POST http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin",
    "client_name": "my-client",
    "scopes": ["read:basic", "write:projects"],
    "ttl_seconds": 3600
  }'
```

#### Using JWT Token

```bash
curl -H "Authorization: Bearer <your-token>" \
  http://localhost:8000/v1/test/ping
```

### 2. API Key Authentication (Programmatic)

For programmatic access, scripts, or when you need full permissions:

#### Setting Up API Key

Set the `KBAI_API_TOKEN` environment variable:

```bash
export KBAI_API_TOKEN="your-secure-api-key-here"
./run_api.sh
```

If no API key is set, the system will auto-generate one on startup (shown in console).

#### Using API Key

```bash
curl -H "X-API-Key: your-api-key-here" \
  http://localhost:8000/v1/test/ping
```

## 🤖 AI Query Processing

The combined API provides advanced AI-powered query processing:

### Basic Query

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "95",
    "question": "What does ASPCA stand for?"
  }'
```

### Response Format

```json
{
  "answer": "American Society for the Prevention of Cruelty to Animals",
  "sources": [
    {
      "id": "faq-uuid",
      "type": "faq",
      "title": "FAQ: What does ASPCA stand for?",
      "url": "/v1/projects/95/faqs/faq-uuid",
      "relevance_score": 22.5
    }
  ],
  "project_id": "95",
  "timestamp": "2025-08-13T04:17:38.283753",
  "tools_used": []
}
```

## 📁 Document Processing

Upload and process documents for automatic knowledge base integration:

```bash
curl -X POST http://localhost:8000/v1/projects/95/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.docx" \
  -F "article_title=My Document Title"
```

## 🔧 AI Tools

The API includes integrated AI tools:

### List Available Tools

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/tools
```

### Execute Tools

```bash
curl -X POST http://localhost:8000/v1/tools/datetime \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 🧪 Testing

A comprehensive test script is provided to validate all functionality:

```bash
# Start the server first
./run_api.sh

# In another terminal, run the test suite
./test_combined_api.sh
```

The test script validates:
- ✅ JWT and API key authentication
- ✅ Query processing before/after document upload
- ✅ Document upload and index rebuilding
- ✅ Source document access
- ✅ AI tools integration
- ✅ Request tracing

## 📊 API Endpoints

### Authentication
- `GET /v1/auth/modes` - Get available authentication methods
- `POST /v1/auth/token` - Get JWT token

### AI Query Processing
- `POST /v1/query` - AI-powered query with sources and tools

### Document Management
- `POST /v1/projects/{id}/documents` - Upload and process documents
- `POST /v1/projects/{id}/faqs/add` - Add FAQ entries
- `GET /v1/projects/{id}/faqs/{faq_id}` - Get FAQ (with file download)
- `GET /v1/projects/{id}/kb/{kb_id}` - Get KB entry (with file download)

### Index Management
- `POST /v1/projects/{id}/rebuild-indexes` - Trigger index rebuild
- `GET /v1/projects/{id}/build-status` - Get build status

### AI Tools
- `GET /v1/tools` - List available tools
- `POST /v1/tools/{tool_name}` - Execute specific tool

### Project Management
- `GET /v1/projects` - List all projects
- `POST /v1/projects` - Create/update project
- `GET /v1/projects/{id}` - Get project details

### Testing & Health
- `GET /v1/test/ping` - Test authenticated access
- `GET /healthz` - Health check
- `GET /readyz` - Readiness check

## 🏗️ Project Structure

```
KBAI/
├── app/                    # Main combined application
│   ├── main.py            # Combined FastAPI app with AI integration
│   ├── models.py          # Pydantic models
│   ├── auth.py            # JWT authentication logic
│   ├── deps.py            # Unified authentication dependencies
│   ├── storage.py         # Database operations
│   ├── middleware.py      # Request middleware
│   ├── templates/         # HTML templates
│   └── schema.sql         # Database schema
├── kb_api/                # Knowledge base processing
├── tools/                 # AI tools framework
├── ai_worker.py           # Legacy AI worker (integrated into main app)
├── init_db.sh             # Database initialization script
├── run_api.sh             # Combined API run script
├── cleanup.sh             # Cleanup script (handles DB + data)
├── test_combined_api.sh   # Comprehensive test suite
├── create_sample_data.py  # Sample data creation
├── prebuild_kb.py         # Index building
├── requirements.txt       # Python dependencies
├── .env.example          # Environment configuration example
└── README.md             # This file
```

## 🔧 Configuration

### Environment Variables

All configuration is done through environment variables. See `.env.example` for available options:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `TRACE_DB_PATH` | `./app/kbai_api.db` | Database file path |
| `AUTH_SIGNING_KEY` | `dev-signing-key-change-me` | JWT signing key |
| `KBAI_API_TOKEN` | *auto-generated* | API key for authentication |
| `OPENAI_API_KEY` | *none* | OpenAI API key for enhanced AI responses |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `MAX_REQUEST_BYTES` | `65536` | Maximum request body size |
| `ALLOWED_ORIGINS` | `*` | CORS allowed origins |

## 🧹 Cleanup

To clean up all data and start fresh:

```bash
./cleanup.sh
```

This removes:
- SQLite database and related files
- Project data directories
- Index files
- Python cache files
- Temporary files

## 🔒 Security

- JWT tokens are used for scoped authentication
- API keys provide full access for programmatic use
- All requests are logged and traced
- Sensitive headers are scrubbed from logs
- Request body size limits prevent abuse
- CORS is configurable for security
- Admin/observability endpoints are hidden from public documentation

## 📈 Monitoring

The API includes comprehensive monitoring:

### Features

- **Request Tracing**: Every request is logged with timing, status, and metadata
- **Prometheus Metrics**: Built-in metrics for monitoring and alerting  
- **Health Checks**: `/healthz` and `/readyz` endpoints for health monitoring
- **Enhanced Dashboard**: Web-based admin interface with real-time updates

### Admin Dashboard

Access the dashboard at `http://localhost:8000/admin` with features including:

- **Dual Authentication**: Login with JWT tokens or API keys
- **Live Metrics**: Real-time charts and statistics
- **Request Tracing**: Filterable trace table with detailed drill-down
- **Real-time Updates**: Server-Sent Events for low-latency data

## 🆕 What's New in the Combined API

This version combines the original KBAI API with the AI Worker functionality:

### Removed
- ❌ Mock/placeholder endpoints for KB and FAQ queries
- ❌ Separate `ai_worker.py` server requirement

### Added
- ✅ Real AI-powered query processing with OpenAI integration
- ✅ Advanced semantic search with vector similarity and full-text search
- ✅ Document upload and processing (PDF, DOCX)
- ✅ Automatic index building and rebuilding
- ✅ AI tools integration (datetime, web search)
- ✅ Enhanced FAQ and KB endpoints with file download
- ✅ Comprehensive authentication for all endpoints
- ✅ Request tracing for AI operations
- ✅ Hidden admin routes from public API docs

### Testing Steps (As Required)

1. ✅ **Environment Setup** - Configure API key, auth signing key
2. ✅ **Database Setup** - `./init_db.sh` creates SQLite database
3. ✅ **Sample Data** - `create_sample_data.py` creates ASPCA/ACLU projects
4. ✅ **Index Building** - `prebuild_kb.py` builds vector/text indexes
5. ✅ **Combined API** - `./run_api.sh` starts single unified server
6. ✅ **Authentication** - Get token using admin/admin credentials
7. ✅ **Query Testing** - All routes require authentication
8. ✅ **Document Upload** - ASPCATEST.docx processing with index rebuild
9. ✅ **Source Access** - Document download via provided URLs
10. ✅ **Tracing** - All operations logged to database

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🆘 Support

For support and questions:

1. Check the API documentation at `/docs`
2. Review the logs in the database traces
3. Run the test suite with `./test_combined_api.sh`
4. Open an issue in the repository

---

**Note**: Change the default authentication credentials and JWT signing key in production!