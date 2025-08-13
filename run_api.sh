#!/usr/bin/env bash
set -euo pipefail

# KBAI API Run Script
echo "Starting KBAI API server..."

#!/usr/bin/env bash
set -euo pipefail

# KBAI API Run Script
echo "Starting KBAI API server..."

# Get script directory and set paths relative to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# Configuration defaults
DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT="8000"
DEFAULT_RELOAD="false"

# Get configuration from environment or use defaults
HOST=${HOST:-$DEFAULT_HOST}
PORT=${PORT:-$DEFAULT_PORT}
RELOAD=${RELOAD:-$DEFAULT_RELOAD}

# Check if database exists
DB_PATH="$PROJECT_ROOT/app/kbai_api.db"
if [ ! -f "$DB_PATH" ]; then
    echo "⚠️  Database not found at $DB_PATH"
    echo "Please run '$PROJECT_ROOT/init_db.sh' first to initialize the database"
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "⚠️  Dependencies not found. Installing requirements..."
    pip install -r "$PROJECT_ROOT/requirements.txt"
fi

echo ""
echo "🚀 Starting KBAI API server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Reload: $RELOAD"
echo "   Database: $DB_PATH"
echo ""
echo "📚 API Documentation will be available at:"
echo "   Swagger UI: http://$HOST:$PORT/docs"
echo "   ReDoc: http://$HOST:$PORT/redoc"
echo "   Admin Dashboard: http://$HOST:$PORT/admin"
echo ""
echo "⏹️  Press Ctrl+C to stop the server"
echo ""

# Start the server from project root
cd "$PROJECT_ROOT"
if [ "$RELOAD" = "true" ]; then
    uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
else
    uvicorn app.main:app --host "$HOST" --port "$PORT"
fi