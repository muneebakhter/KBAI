#!/bin/bash
# DARKBO Unified Demo Script
# Comprehensive demonstration of all DARKBO functionality
# This script replaces demo.sh, demo_new_features.sh, and tools_demo.sh

set -e  # Exit on any error

echo "🚀 DARKBO Unified Demo - Complete System Walkthrough"
echo "====================================================="
echo ""

# Function to check if server is running
check_server() {
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for server to start
wait_for_server() {
    echo "⏳ Waiting for server to start..."
    for i in {1..30}; do
        if check_server; then
            echo "✅ Server is ready!"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    echo "❌ Server failed to start within 30 seconds"
    exit 1
}

# Function to stop server gracefully
stop_server() {
    if [ ! -z "$SERVER_PID" ]; then
        echo "🛑 Stopping DARKBO server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        echo "✅ Server stopped"
    fi
}

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    stop_server
    cd "$ORIGINAL_DIR"
}

# Set up cleanup trap
trap cleanup EXIT

# Store original directory
ORIGINAL_DIR=$(pwd)

echo "📦 Step 1: Install minimal dependencies"
echo "--------------------------------------"
pip install fastapi uvicorn pydantic requests

echo ""
echo "📁 Step 2: Generate sample data in data/ folder"
echo "----------------------------------------------"
python3 create_sample_data.py

echo ""
echo "🔧 Step 3: Build knowledge base indexes"
echo "--------------------------------------"
cd data
python3 ../prebuild_kb.py

echo ""
echo "🚀 Step 4: Start DARKBO AI Worker Server"
echo "---------------------------------------"
python3 ../ai_worker.py &
SERVER_PID=$!
echo "Server started with PID: $SERVER_PID"

# Wait for server to be ready
wait_for_server

echo ""
echo "🧪 Step 5: Core Knowledge Base Functionality"
echo "============================================"

echo ""
echo "1. List available projects:"
echo "curl http://localhost:8000/projects"
curl -s http://localhost:8000/projects | python3 -m json.tool

echo ""
echo ""
echo "2. Query ASPCA - What does ASPCA stand for?"
echo "curl -X POST http://localhost:8000/query -d '{\"project_id\": \"95\", \"question\": \"What does ASPCA stand for?\"}'"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What does ASPCA stand for?"}' | python3 -m json.tool

echo ""
echo ""
echo "3. Query ACLU - What is the ACLU?"
echo "curl -X POST http://localhost:8000/query -d '{\"project_id\": \"175\", \"question\": \"What is the ACLU?\"}'"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "175", "question": "What is the ACLU?"}' | python3 -m json.tool

echo ""
echo ""
echo "4. Get FAQ source directly:"
echo "curl http://localhost:8000/v1/projects/95/faqs/[faq-id]"
FAQ_ID=$(curl -s "http://localhost:8000/projects" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for project in data:
    if project['id'] == '95':
        print(project['faqs'][0]['id'])
        break
")
if [ ! -z "$FAQ_ID" ]; then
    curl -s "http://localhost:8000/v1/projects/95/faqs/$FAQ_ID" | python3 -m json.tool
else
    echo "(FAQ ID not found - this is expected in some configurations)"
fi

echo ""
echo ""
echo "🛠️  Step 6: External Tools Functionality"
echo "========================================"

echo ""
echo "5. List available tools:"
echo "curl http://localhost:8000/tools"
curl -s -X GET "http://localhost:8000/tools" | python3 -m json.tool

echo ""
echo ""
echo "6. DateTime tool - What time is it now?"
echo "curl -X POST http://localhost:8000/query -d '{\"project_id\": \"95\", \"question\": \"What time is it now?\"}'"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What time is it now?"}' | python3 -m json.tool

echo ""
echo ""
echo "7. DateTime tool - What date is today?"
echo "curl -X POST http://localhost:8000/query -d '{\"project_id\": \"95\", \"question\": \"What date is today?\"}'"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "What date is today?"}' | python3 -m json.tool

echo ""
echo ""
echo "8. Direct DateTime tool usage:"
echo "curl -X POST http://localhost:8000/tools/datetime -d '{}'"
curl -s -X POST "http://localhost:8000/tools/datetime" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool

echo ""
echo ""
echo "9. DateTime tool with custom format:"
echo "curl -X POST http://localhost:8000/tools/datetime -d '{\"format\": \"%B %d, %Y at %I:%M %p\"}'"
curl -s -X POST "http://localhost:8000/tools/datetime" \
  -H "Content-Type: application/json" \
  -d '{"format": "%B %d, %Y at %I:%M %p"}' | python3 -m json.tool

echo ""
echo ""
echo "10. Web search tool - direct usage:"
echo "curl -X POST http://localhost:8000/tools/web_search -d '{\"query\": \"Python programming\", \"max_results\": 2}'"
curl -s -X POST "http://localhost:8000/tools/web_search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python programming", "max_results": 2}' | python3 -m json.tool

echo ""
echo ""
echo "📄 Step 7: Document and FAQ Management Features"
echo "=============================================="

echo ""
echo "11. Check current project build status:"
echo "curl http://localhost:8000/projects/95/build-status"
curl -s "http://localhost:8000/projects/95/build-status" | python3 -m json.tool

echo ""
echo ""
echo "12. Add a new FAQ about document ingestion:"
echo "curl -X POST http://localhost:8000/projects/95/faqs -d '{\"question\": \"How do I upload documents?\", \"answer\": \"You can upload PDF and DOCX documents using the document ingestion endpoint.\"}'"
curl -s -X POST "http://localhost:8000/projects/95/faqs" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I upload documents to the knowledge base?",
    "answer": "You can upload PDF and DOCX documents using the document ingestion endpoint. The system will automatically extract text, create chunks, and rebuild the search indexes."
  }' | python3 -m json.tool

echo ""
echo ""
echo "13. Query for the new FAQ:"
echo "curl -X POST http://localhost:8000/query -d '{\"project_id\": \"95\", \"question\": \"How do I upload documents?\"}'"
sleep 2  # Wait for index rebuild
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "How do I upload documents?"}' | python3 -m json.tool

echo ""
echo ""
echo "14. Manually trigger index rebuild:"
echo "curl -X POST http://localhost:8000/projects/95/rebuild-indexes"
curl -s -X POST "http://localhost:8000/projects/95/rebuild-indexes" | python3 -m json.tool

echo ""
echo ""
echo "15. Complex query combining KB knowledge and tools:"
echo "curl -X POST http://localhost:8000/query -d '{\"project_id\": \"95\", \"question\": \"Tell me about ASPCA and what time it is now\"}'"
curl -s -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "95", "question": "Tell me about ASPCA and what time it is now"}' | python3 -m json.tool

echo ""
echo ""
echo "✅ DARKBO Unified Demo Completed Successfully!"
echo "============================================="
echo ""
echo "🎯 All Features Demonstrated:"
echo "  ✅ Project listing and management"
echo "  ✅ Knowledge base queries with source citations"
echo "  ✅ FAQ and KB entry retrieval"
echo "  ✅ External tools integration (DateTime, Web Search)"
echo "  ✅ Direct tool execution endpoints"
echo "  ✅ Dynamic FAQ creation via API"
echo "  ✅ Automatic index rebuilding after content changes"
echo "  ✅ Versioned index system with atomic updates"
echo "  ✅ Build status monitoring"
echo "  ✅ Manual index rebuild triggers"
echo "  ✅ Complex queries combining multiple sources"
echo ""
echo "🔧 System Architecture:"
echo "  📁 data/ - Unified home for all project data"
echo "  🏗️  create_sample_data.py - Data generation"
echo "  🔧 prebuild_kb.py - Index building"
echo "  🚀 ai_worker.py - FastAPI server with tools support"
echo ""
echo "🚀 To enable enhanced functionality:"
echo "   pip install sentence-transformers faiss-cpu whoosh python-multipart python-docx PyPDF2"
echo ""
echo "📚 Key Endpoints:"
echo "   GET  /projects - List all projects"
echo "   POST /query - Ask questions with project context"
echo "   GET  /tools - List available external tools"
echo "   POST /tools/{tool_name} - Execute tools directly"
echo "   POST /projects/{id}/faqs - Add new FAQs"
echo "   POST /projects/{id}/rebuild-indexes - Trigger index rebuild"
echo "   GET  /projects/{id}/build-status - Check build status"
echo ""
echo "🎉 DARKBO is ready for your knowledge base needs!"