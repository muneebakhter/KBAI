# DARKBO - Document Augmented Retrieval Knowledge Base Operator

A simplified AI knowledge base system with external tools support and unified data management.

## 🎯 Overview

DARKBO is a streamlined two-script architecture that provides:
- **Unified Data Storage**: All project data lives in the `data/` folder
- **Auto-Discovery**: Projects are automatically detected without configuration files
- **External Tools**: DateTime and web search tools with extensible framework  
- **AI-Powered Responses**: OpenAI GPT integration with RAG (Retrieval-Augmented Generation)
- **Hybrid Search**: Dense semantic + sparse keyword search with graceful fallback
- **Source Citations**: All answers include clickable source links

### Core Components

1. **create_sample_data.py** - Creates sample data in the unified `data/` folder
2. **prebuild_kb.py** - Auto-discovers projects and builds search indexes 
3. **ai_worker.py** - FastAPI server with AI-enhanced responses and tools support

## 🚀 Quick Start

### 1. Generate Sample Data
```bash
python3 create_sample_data.py
```
Creates a `data/` directory with sample ACLU and ASPCA projects.

### 2. Build Knowledge Base Indexes
```bash
cd data
python3 ../prebuild_kb.py
```
Auto-discovers projects and builds search indexes.

### 3. Start the AI Worker Server
```bash
python3 ../ai_worker.py
```
Starts server on `http://localhost:8000` with full functionality.

### 4. Run Complete Demo
```bash
./demo_unified.sh
```
Comprehensive demo covering all features end-to-end.

## 📁 Unified Data Structure

```
data/                                    # Unified data home
├── 95/                                  # ASPCA project (auto-discovered)
│   ├── attachments/                     # Sample documents
│   ├── 95.faq.json                     # FAQ entries
│   ├── 95.kb.json                      # Knowledge base entries
│   └── index/                          # Generated search indexes
│       ├── dense/                      # FAISS vector indexes
│       ├── sparse/                     # Whoosh text indexes
│       └── meta.json                   # Index metadata
├── 175/                                # ACLU project (auto-discovered)
│   ├── attachments/
│   ├── 175.faq.json
│   ├── 175.kb.json
│   └── index/
└── proj_mapping.txt                    # Auto-generated (no longer required)
```

## 🛠️ External Tools Framework

DARKBO automatically enhances responses using external tools:

### Available Tools
- **DateTime Tool**: Current date, time, and timezone information
- **Web Search Tool**: Searx search integration
- **Extensible Framework**: Easy to add new tools

### Tool Usage Examples
```bash
# DateTime integration
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What time is it now?"}'

# Web search integration
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What is machine learning?"}'

# Direct tool access
curl "http://localhost:8000/tools"
curl -X POST "http://localhost:8000/tools/datetime" -d '{"format": "%B %d, %Y"}'
```

## 🤖 AI-Enhanced Responses

### AI Agent Features
- **Intelligent Identity**: Introduces itself as "ACD Direct's Knowledge Base AI System"
- **Context-Aware**: Combines knowledge base content with AI generation
- **Tool Integration**: Incorporates external tool results into responses
- **Graceful Fallback**: Enhanced responses even without OpenAI API key

### Configuration
Create `.env` file for AI features:
```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## 📡 API Endpoints

### Core Query System
```bash
# Ask questions with AI enhancement
POST /query
{
  "project_id": "95",
  "question": "What does ASPCA stand for?"
}

# Response includes AI-generated answer, sources, and tools used
{
  "answer": "ASPCA stands for the American Society for the Prevention of Cruelty to Animals...",
  "sources": [...],
  "tools_used": [...],
  "project_id": "95",
  "timestamp": "2025-08-12T20:15:00"
}
```

### Project Management
```bash
GET /projects                            # List all auto-discovered projects
GET /projects/{id}/build-status          # Check index build status  
POST /projects/{id}/rebuild-indexes      # Manually trigger rebuild
POST /projects/{id}/faqs                 # Add new FAQs (triggers rebuild)
```

### Source Retrieval
```bash
GET /v1/projects/{id}/faqs/{faq_id}      # Get FAQ by ID
GET /v1/projects/{id}/kb/{kb_id}         # Get KB entry by ID
```

### Tools Management
```bash
GET /tools                               # List available tools
POST /tools/{tool_name}                  # Execute tool directly
```

## 📦 Installation

### Minimal Installation (Core functionality)
```bash
pip install fastapi uvicorn pydantic requests
```

### Full Installation (Enhanced search)
```bash
pip install fastapi uvicorn pydantic sentence-transformers faiss-cpu whoosh requests
```

### AI Enhancement (Optional)
```bash
pip install openai
```

### Document Processing (Optional)
```bash
pip install python-multipart python-docx PyPDF2
```

## 🔧 Key Features

### Simplified Architecture
- **No Configuration Files**: Auto-discovery eliminates proj_mapping.txt
- **Unified Data Home**: All data in `data/` folder for easy management
- **Two-Script Workflow**: Simple prebuild + server architecture
- **Graceful Degradation**: Works with minimal dependencies

### Advanced Search
- **Hybrid Search**: Dense semantic + sparse keyword search
- **Auto-Fallback**: Basic keyword search when ML dependencies unavailable
- **Source Citations**: All results include clickable source links
- **Stable IDs**: UUID5-based IDs for reliable references

### Document Management
- **Versioned Indexes**: Atomic updates with background rebuilding
- **Attachment Support**: Serves original uploaded documents
- **Change Detection**: Only rebuilds when data actually changes
- **Build Monitoring**: Real-time build status tracking

### Tool Integration
- **Smart Selection**: Automatic tool selection based on query content
- **Error Resilience**: Tool failures don't break main functionality
- **Extensible Framework**: Easy to add new tool capabilities
- **Graceful Handling**: Network issues handled transparently

## 🧹 Maintenance

### Cleanup Script
```bash
./cleanup.sh                            # Remove all generated data and indexes
```

### Regenerate Data
```bash
python3 create_sample_data.py           # Create fresh sample data
cd data && python3 ../prebuild_kb.py    # Rebuild indexes
```

## 🧪 Testing & Demo

### Run Unified Demo
```bash
./demo_unified.sh                       # Complete system demonstration
```

### Manual Testing
```bash
# Generate data and start server
python3 create_sample_data.py
cd data
python3 ../prebuild_kb.py
python3 ../ai_worker.py

# Test in another terminal
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What does ASPCA stand for?"}'
```

## 🔄 Migration & Changes

### Key Improvements
- **Unified Data Structure**: `sample_data/` → `data/` (single source of truth)
- **Auto-Discovery**: Removed dependency on `proj_mapping.txt`
- **Consolidated Demos**: 3 separate demo scripts → 1 comprehensive script
- **Enhanced Documentation**: 4 separate .md files → 1 consolidated guide
- **Improved Tools**: Better integration and error handling

### Removed Components
- Multiple demo scripts (demo.sh, demo_new_features.sh, tools_demo.sh)
- Project mapping file requirement (proj_mapping.txt)
- Scattered documentation files
- Complex configuration requirements

## 🎯 Use Cases

### Knowledge Base Management
- FAQ systems with intelligent search
- Document repositories with AI enhancement  
- Customer support knowledge bases
- Internal documentation systems

### External Data Integration
- Real-time information with web search
- Time-sensitive queries with datetime tools
- Combined internal + external knowledge responses
- Tool-enhanced customer support

### Development & Integration
- RESTful API for easy integration
- File-based storage for simple deployment
- Modular tool framework for extensions
- AI-ready architecture for enhanced responses

This simplified, unified architecture focuses on core functionality while maintaining powerful features and easy extensibility.