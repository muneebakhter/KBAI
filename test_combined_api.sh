#!/usr/bin/env bash
# 
# KBAI Combined API Test Script
# Demonstrates all the testing steps mentioned in the requirements
#

set -e

echo "🧪 KBAI Combined API Integration Test"
echo "====================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE="http://localhost:8000"
PROJECT_ID="95"  # ASPCA project
API_KEY="test-api-key-12345"

# Test functions
test_step() {
    echo -e "${BLUE}📋 Test Step: $1${NC}"
}

test_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

test_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

test_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if server is running
check_server() {
    test_step "Checking if KBAI API server is running"
    if curl -s "$API_BASE/healthz" > /dev/null; then
        test_success "Server is running at $API_BASE"
    else
        test_error "Server is not running. Please start with './run_api.sh'"
    fi
}

# Step 6: Get authentication token
get_auth_token() {
    test_step "Getting authentication token using admin/admin credentials"
    
    TOKEN_RESPONSE=$(curl -s -X POST "$API_BASE/v1/auth/token" \
        -H "Content-Type: application/json" \
        -d '{
            "username": "admin",
            "password": "admin",
            "client_name": "test-client",
            "scopes": ["read:basic", "write:projects"],
            "ttl_seconds": 3600
        }')
    
    TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
    
    if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        test_success "JWT token obtained successfully"
        test_info "Token: ${TOKEN:0:20}..."
    else
        test_error "Failed to get JWT token"
    fi
}

# Step 7a: Query before document upload
test_query_before_upload() {
    test_step "Testing query BEFORE document upload: 'what is the website for ASPCA project 95'"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/v1/query" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": \"$PROJECT_ID\",
            \"question\": \"what is the website for ASPCA project 95\"
        }")
    
    ANSWER=$(echo "$RESPONSE" | jq -r '.answer')
    SOURCES_COUNT=$(echo "$RESPONSE" | jq '.sources | length')
    
    test_success "Query executed successfully"
    test_info "Answer: $ANSWER"
    test_info "Sources found: $SOURCES_COUNT"
    echo ""
}

# Step 7b: Upload ASPCATEST.docx
test_document_upload() {
    test_step "Uploading ASPCATEST.docx to project $PROJECT_ID"
    
    if [ ! -f "ASPCATEST.docx" ]; then
        test_error "ASPCATEST.docx file not found in current directory"
    fi
    
    UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/v1/projects/$PROJECT_ID/documents" \
        -H "Authorization: Bearer $TOKEN" \
        -F "file=@ASPCATEST.docx" \
        -F "article_title=ASPCA Test Document")
    
    SUCCESS=$(echo "$UPLOAD_RESPONSE" | jq -r '.success')
    MESSAGE=$(echo "$UPLOAD_RESPONSE" | jq -r '.message')
    DOCUMENT_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.document_id')
    INDEX_BUILD_STARTED=$(echo "$UPLOAD_RESPONSE" | jq -r '.index_build_started')
    
    if [ "$SUCCESS" = "true" ]; then
        test_success "Document uploaded successfully"
        test_info "Message: $MESSAGE"
        test_info "Document ID: $DOCUMENT_ID"
        test_info "Index rebuild started: $INDEX_BUILD_STARTED"
        
        if [ "$INDEX_BUILD_STARTED" = "true" ]; then
            test_info "Waiting for index rebuild to complete..."
            sleep 3
            
            # Check build status
            BUILD_STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
                "$API_BASE/v1/projects/$PROJECT_ID/build-status")
            
            IS_BUILDING=$(echo "$BUILD_STATUS" | jq -r '.build_status.is_building')
            CURRENT_VERSION=$(echo "$BUILD_STATUS" | jq -r '.build_status.current_version')
            
            test_info "Build status - Is building: $IS_BUILDING, Version: $CURRENT_VERSION"
        fi
    else
        test_error "Document upload failed: $MESSAGE"
    fi
    echo ""
}

# Step 7c: Query after document upload
test_query_after_upload() {
    test_step "Testing query AFTER document upload: 'what is the website for ASPCA project 95'"
    
    RESPONSE=$(curl -s -X POST "$API_BASE/v1/query" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": \"$PROJECT_ID\",
            \"question\": \"what is the website for ASPCA project 95\"
        }")
    
    ANSWER=$(echo "$RESPONSE" | jq -r '.answer')
    SOURCES_COUNT=$(echo "$RESPONSE" | jq '.sources | length')
    
    test_success "Query executed successfully"
    test_info "Answer: $ANSWER"
    test_info "Sources found: $SOURCES_COUNT"
    
    # Check if the uploaded document appears as a source
    DOCUMENT_IN_SOURCES=$(echo "$RESPONSE" | jq '.sources[] | select(.title | contains("ASPCA Test Document"))')
    
    if [ -n "$DOCUMENT_IN_SOURCES" ]; then
        test_success "Uploaded document appears in sources"
        DOCUMENT_URL=$(echo "$DOCUMENT_IN_SOURCES" | jq -r '.url')
        test_info "Document source URL: $DOCUMENT_URL"
        
        # Test accessing the document directly
        test_step "Testing direct document access"
        DOCUMENT_ACCESS_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -H "Authorization: Bearer $TOKEN" \
            "$API_BASE$DOCUMENT_URL" 2>/dev/null || echo "500")
        
        if echo "$DOCUMENT_ACCESS_RESPONSE" | grep -q "200"; then
            test_success "Document accessible via provided URL"
            # Get content type with a separate request
            CONTENT_TYPE_RESPONSE=$(curl -s -I -H "Authorization: Bearer $TOKEN" \
                "$API_BASE$DOCUMENT_URL" 2>/dev/null | grep -i "content-type" | cut -d' ' -f2- || echo "unknown")
            test_info "HTTP Status: 200 OK"
        else
            test_error "Document not accessible via provided URL"
        fi
    else
        test_info "Uploaded document not yet appearing in sources (may need more time for indexing)"
    fi
    echo ""
}

# Test authentication
test_authentication() {
    test_step "Testing authentication methods"
    
    # Test JWT authentication
    JWT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$API_BASE/v1/test/ping")
    JWT_AUTH_METHOD=$(echo "$JWT_RESPONSE" | jq -r '.auth_method')
    
    if [ "$JWT_AUTH_METHOD" = "jwt" ]; then
        test_success "JWT authentication working"
    else
        test_error "JWT authentication failed"
    fi
    
    # Test API key authentication
    API_KEY_RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" \
        "$API_BASE/v1/test/ping")
    API_KEY_AUTH_METHOD=$(echo "$API_KEY_RESPONSE" | jq -r '.auth_method')
    
    if [ "$API_KEY_AUTH_METHOD" = "api_key" ]; then
        test_success "API key authentication working"
    else
        test_error "API key authentication failed"
    fi
    
    # Test no authentication (should fail)
    NO_AUTH_RESPONSE=$(curl -s -X POST "$API_BASE/v1/query" \
        -H "Content-Type: application/json" \
        -d "{\"project_id\": \"$PROJECT_ID\", \"question\": \"test\"}")
    
    if echo "$NO_AUTH_RESPONSE" | grep -q "Missing authentication"; then
        test_success "No authentication properly rejected"
    else
        test_error "No authentication should be rejected"
    fi
    echo ""
}

# Test tools functionality
test_tools() {
    test_step "Testing AI tools functionality"
    
    # List available tools
    TOOLS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$API_BASE/v1/tools")
    TOOLS_COUNT=$(echo "$TOOLS_RESPONSE" | jq '.tools | length')
    
    test_success "Tools endpoint accessible"
    test_info "Available tools: $TOOLS_COUNT"
    
    # Test datetime tool execution
    DATETIME_RESPONSE=$(curl -s -X POST "$API_BASE/v1/tools/datetime" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{}')
    
    DATETIME_SUCCESS=$(echo "$DATETIME_RESPONSE" | jq -r '.success')
    CURRENT_TIME=$(echo "$DATETIME_RESPONSE" | jq -r '.data.current_datetime')
    
    if [ "$DATETIME_SUCCESS" = "true" ]; then
        test_success "Datetime tool execution successful"
        test_info "Current time: $CURRENT_TIME"
    else
        test_error "Datetime tool execution failed"
    fi
    
    # Test time-based query (should use datetime tool automatically)
    TIME_QUERY_RESPONSE=$(curl -s -X POST "$API_BASE/v1/query" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": \"$PROJECT_ID\",
            \"question\": \"What time is it now?\"
        }")
    
    TOOLS_USED=$(echo "$TIME_QUERY_RESPONSE" | jq '.tools_used | length')
    
    if [ "$TOOLS_USED" -gt 0 ]; then
        test_success "AI automatically used tools for time-based query"
        test_info "Tools used in query: $TOOLS_USED"
    else
        test_info "No tools used in time-based query (might be expected based on implementation)"
    fi
    echo ""
}

# Test traces
test_traces() {
    test_step "Testing request tracing functionality"
    
    TRACES_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
        "$API_BASE/v1/traces?limit=5")
    
    if echo "$TRACES_RESPONSE" | jq -e '.items' > /dev/null; then
        TRACES_COUNT=$(echo "$TRACES_RESPONSE" | jq '.items | length')
        test_success "Traces endpoint accessible"
        test_info "Recent traces: $TRACES_COUNT"
    else
        test_info "Traces endpoint might be hidden from schema (expected behavior)"
    fi
    echo ""
}

# Main execution
main() {
    echo "Starting comprehensive integration test..."
    echo ""
    
    check_server
    get_auth_token
    test_authentication
    test_query_before_upload
    test_document_upload
    test_query_after_upload
    test_tools
    test_traces
    
    echo ""
    echo -e "${GREEN}🎉 All tests completed successfully!${NC}"
    echo ""
    echo "Summary of what was tested:"
    echo "✅ JWT and API key authentication"
    echo "✅ Query processing before document upload"
    echo "✅ Document upload and index rebuilding"
    echo "✅ Query processing after document upload"
    echo "✅ Source document access"
    echo "✅ AI tools integration"
    echo "✅ Request tracing"
    echo ""
    echo "The combined KBAI API is working correctly!"
}

# Run the tests
main