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

13. **Query before document upload:**
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

14. **Upload a document (if you have ASPCATEST.docx):**
    ```bash
    curl -X POST "http://localhost:8000/v1/projects/95/documents" \
      -H "X-API-Key: YOUR_API_KEY" \
      -F "file=@ASPCATEST.docx" \
      -F "article_title=ASPCA Test Document"
    ```

15. **Check build status:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/projects/95/build-status"
    ```

16. **Query after document upload:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "what is the website for ASPCA project 95"
      }'
    ```

## Step 8: Test AI Tools

17. **List available tools:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/tools"
    ```

18. **Test datetime tool:**
    ```bash
    curl -X POST "http://localhost:8000/v1/tools/datetime" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{}'
    ```

19. **Test time-based query:**
    ```bash
    curl -X POST "http://localhost:8000/v1/query" \
      -H "X-API-Key: YOUR_API_KEY" \
      -H "Content-Type: application/json" \
      -d '{
        "project_id": "95",
        "question": "What time is it now?"
      }'
    ```

## Step 9: Test Request Tracing

20. **View recent traces:**
    ```bash
    curl -H "X-API-Key: YOUR_API_KEY" \
      "http://localhost:8000/v1/traces?limit=5"
    ```

## Step 10: Explore the API

21. **View API documentation:**
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
- ✅ AI tools integration
- ✅ Request tracing

The API is now ready for development, testing, or integration with other systems.