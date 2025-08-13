# KBAI API Testing Walkthrough

This walkthrough demonstrates how to test the KBAI (Knowledge Base AI) API from setup to full functionality. It's based on the comprehensive test script `test_combined_api.sh` but provides step-by-step manual instructions.

## Prerequisites

- Python 3.7+ with venv support
- curl (for API testing)
- jq (for JSON processing, optional but recommended)

## Step 1: Repository Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/muneebakhter/KBAI.git
   cd KBAI
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Step 2: Initialize Database and Data

4. **Initialize the database:**
   ```bash
   ./init_db.sh
   ```
   This creates the SQLite database for sessions and request tracing.

5. **Create sample data:**
   ```bash
   python3 create_sample_data.py
   ```
   This creates two sample projects (ACLU and ASPCA) with FAQ and KB entries.

6. **Build knowledge base indexes:**
   ```bash
   cd data
   python3 ../prebuild_kb.py
   cd ..
   ```
   This builds the search indexes for the knowledge base content.

## Step 3: Start the API Server

7. **Start the API server:**
   ```bash
   ./run_api.sh
   ```
   
   The server will start and display:
   - Server URL (http://0.0.0.0:8000)
   - Auto-generated API token
   - Documentation URLs

   **Note:** Save the auto-generated API token shown in the output - you'll need it for authentication.

## Step 4: Verify Server Health

8. **Check server health:**
   ```bash
   curl http://localhost:8000/healthz
   ```
   Should return: `ok`

9. **Check readiness:**
   ```bash
   curl http://localhost:8000/readyz
   ```
   Should return: `ready`

## Step 5: Authentication Testing

10. **Get JWT token (optional):**
    ```bash
    curl -X POST "http://localhost:8000/v1/auth/token" \
      -H "Content-Type: application/json" \
      -d '{
        "username": "admin",
        "password": "admin",
        "client_name": "test-client",
        "scopes": ["read:basic", "write:projects"],
        "ttl_seconds": 3600
      }'
    ```

11. **Test API key authentication:**
    ```bash
    # Replace YOUR_API_KEY with the auto-generated token from step 7
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/test/ping"
    ```

## Step 6: Test Core Functionality

12. **List projects:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects"
    ```
    Should return two projects: ACLU (175) and ASPCA (95).

13. **Add a new project:**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "id": "123",
        "name": "Test Organization",
        "active": true
      }'
    ```

42. **Verify project was created:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects"
    ```
    Should now include the new Test Organization (123).

36. **Add FAQ to new project:**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/123/faqs/add" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "question": "What is Test Organization?",
        "answer": "This is a test organization created via the API."
      }'
    ```

37. **Add KB article to new project:**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/123/kb/add" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Organization Overview",
        "content": "Test Organization provides comprehensive testing services for API validation and demonstration purposes."
      }'
    ```

38. **List project FAQs:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/123/faqs"
    ```

39. **List project KB articles:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/123/kb"
    ```

40. **Remove (deactivate) project:**
    ```bash
    curl -X DELETE "http://localhost:8000/v1/projects/123" \
      -H "X-API-Key: YOUR_API_KEY"
    ```

41. **Query before document upload:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "what is the website for ASPCA project 95"
      }'
    ```

## Step 7: Document Upload Testing

42. **Upload a document (if you have ASPCATEST.docx):**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/95/documents" \
      -H "X-API-Key: YOUR_API_KEY" \
      -F "file=@ASPCATEST.docx" \
      -F "article_title=ASPCA Test Document"
    ```

36. **Check build status:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/build-status"
    ```

37. **Query after document upload:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "what is the website for ASPCA project 95"
      }'
    ```

38. **Test document-based query (if ASPCATEST.docx was uploaded):**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "is there some way to donate for pets of israel-gaza war"
      }'
    ```

## Step 8: FAQ and Knowledge Base Management

39. **Add a new FAQ:**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/95/faqs/add" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "question": "How can I volunteer with ASPCA?",
        "answer": "You can volunteer by visiting our volunteer page or contacting your local ASPCA center."
      }'
    ```

40. **Add a new KB article:**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/95/kb/add" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Emergency Pet Care Guide",
        "content": "In case of pet emergency, contact your local veterinarian immediately. For after-hours emergencies, locate the nearest 24-hour animal hospital."
      }'
    ```

41. **List FAQs to get IDs:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/faqs"
    ```

42. **List KB articles to get IDs:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/kb"
    ```

36. **Delete a FAQ (use ID from step 20):**
    ```bash
    curl -X DELETE "http://localhost:8000/v1/projects/95/faqs/FAQ_ID_HERE" \
      -H "X-API-Key: YOUR_API_KEY"
    ```

37. **Delete a KB article (use ID from step 21):**
    ```bash
    curl -X DELETE "http://localhost:8000/v1/projects/95/kb/KB_ID_HERE" \
      -H "X-API-Key: YOUR_API_KEY"
    ```

38. **Verify deletion affected search results:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "How can I volunteer with ASPCA?"
      }'
    ```

## Step 8.5: Document Retrieval in Original Format

After uploading documents in Steps 7-8, you can retrieve them in their original format using the following process:

43. **List all KB articles to find uploaded documents:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/kb"
    ```
    
    This returns a JSON array of all KB entries. Look for entries with `"source": "upload"` - these are from document uploads. Note the `id` field for documents you want to retrieve.

44. **Retrieve a specific document by its KB ID (replace KB_ID_HERE with actual ID):**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/kb/KB_ID_HERE"
    ```
    
    **Behavior:**
    - If the original document file exists in attachments, it returns the **original file** with proper content-type headers
    - If no attachment file exists, it returns the **JSON representation** of the KB entry with extracted text content
    
45. **Download document to file (when original file is available):**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/kb/KB_ID_HERE" \
      -o "downloaded_document.docx"
    ```
    
    The downloaded file will retain its original format (PDF, DOCX, etc.).

46. **Filter KB entries to find only uploaded documents:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/kb" | \
      jq '.[] | select(.source == "upload")'
    ```
    
    This uses `jq` to filter and show only document-based entries, making it easier to find uploaded files.

**Note:** Large documents are automatically chunked into multiple KB entries. Each chunk has the same `article` title but different `id` values. The original file attachment is linked to these chunks, so retrieving any chunk's ID will return the complete original document.

## Step 9: Test Document Deletion and Re-indexing

39. **Upload a document for deletion testing:**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/95/documents" \
      -H "X-API-Key: YOUR_API_KEY" \
      -F "file=@ASPCATEST.docx" \
      -F "article_title=Test Document for Deletion"
    ```

40. **Query to verify document is indexed:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "israel-gaza war pets donation"
      }'
    ```

41. **Get KB articles to find document-based entries:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/kb"
    ```

42. **Delete KB entries from uploaded document:**
    ```bash
    # Use the KB IDs from step 27 that were created from the document
    curl -X DELETE "http://localhost:8000/v1/projects/95/kb/DOCUMENT_KB_ID_HERE" \
      -H "X-API-Key: YOUR_API_KEY"
    ```

36. **Verify document content no longer findable:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "israel-gaza war pets donation"
      }'
    ```

37. **Check index rebuild status:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/build-status"
    ```

## Step 10: Test AI Tools

38. **List available tools:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/tools"
    ```

39. **Test datetime tool:**
    ```bash
    curl -X POST "http://localhost:8000/v1/tools/datetime" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{}'
    ```

40. **Test time-based query:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "What time is it now?"
      }'
    ```

## Step 11: Test Request Tracing

41. **View recent traces:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/traces?limit=5"
    ```

## Step 12: Explore the API

42. **View API documentation:**
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - Admin Dashboard: http://localhost:8000/admin

## Troubleshooting

### Common Issues

1. **"Database not found" error:**
   - Run `./init_db.sh` from the project root

2. **"Schema file not found" error:**
   - Ensure you're running scripts from the correct directory
   - The shell scripts now use absolute paths and should work from any directory

3. **Empty projects list:**
   - Run `python3 create_sample_data.py` to create sample projects
   - Check that `data/proj_mapping.txt` exists and contains project entries

4. **"Dependencies not found" error:**
   - Make sure virtual environment is activated: `source .venv/bin/activate`
   - Install requirements: `pip install -r requirements.txt`

5. **Permission errors on shell scripts:**
   ```bash
   chmod +x *.sh
   ```

### Automated Testing

For automated testing, you can run the comprehensive test script:
```bash
./test_combined_api.sh
```

This script performs all the above steps automatically and reports the results.

## Expected Outcomes

After following this walkthrough, you should have:

- ✅ A running KBAI API server
- ✅ Two sample projects (ACLU and ASPCA) with knowledge base content
- ✅ Working authentication (both API key and JWT)
- ✅ Functional query processing
- ✅ Document upload capability
- ✅ FAQ and KB article creation/deletion with automatic re-indexing
- ✅ Document deletion testing with knowledge base removal
- ✅ AI tools integration
- ✅ Request tracing

The API is now ready for development, testing, or integration with other systems.