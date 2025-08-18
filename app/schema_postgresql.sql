-- PostgreSQL schema for KBAI API
-- This schema supports the same tables as SQLite but with PostgreSQL-specific optimizations

-- Enable pgvector extension for vector storage (required for vector features)
CREATE EXTENSION IF NOT EXISTS vector;

-- Optional: Enable pgvectorscale for enhanced performance (if available)
-- CREATE EXTENSION IF NOT EXISTS vectorscale;

-- Sessions table for authentication
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY,           -- sess_*
  token_jti TEXT UNIQUE NOT NULL,
  client_name TEXT NOT NULL,
  scopes TEXT NOT NULL,          -- comma-separated
  issued_at TIMESTAMP NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  ip_lock INET,                  -- PostgreSQL-specific INET type for IP addresses
  disabled BOOLEAN NOT NULL DEFAULT FALSE
);

-- Traces table for request logging
CREATE TABLE IF NOT EXISTS traces(
  id TEXT PRIMARY KEY,           -- tr_*
  ts TIMESTAMP NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status INTEGER NOT NULL,
  latency_ms REAL NOT NULL,
  ip INET,                       -- PostgreSQL-specific INET type
  ua TEXT,
  headers_slim JSONB,            -- PostgreSQL-specific JSONB for better JSON performance
  query JSONB,                   -- PostgreSQL-specific JSONB
  body_sha256 TEXT,
  token_sub TEXT,                -- sessions.id
  error TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_traces_ts ON traces(ts);
CREATE INDEX IF NOT EXISTS idx_traces_path ON traces(path);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_token_sub ON traces(token_sub);
CREATE INDEX IF NOT EXISTS idx_traces_ip ON traces(ip);

-- Additional indexes for JSON queries (PostgreSQL-specific)
CREATE INDEX IF NOT EXISTS idx_traces_headers_slim ON traces USING GIN(headers_slim);
CREATE INDEX IF NOT EXISTS idx_traces_query ON traces USING GIN(query);

-- Vector storage table for embeddings
CREATE TABLE IF NOT EXISTS vector_embeddings(
  id SERIAL PRIMARY KEY,
  project_id TEXT NOT NULL,
  content_type TEXT NOT NULL, -- 'faq', 'kb', 'document'
  content_id TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  embedding vector(1536),     -- OpenAI ada-002 embedding size
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vector_embeddings_project ON vector_embeddings(project_id);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_type ON vector_embeddings(content_type);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_content_id ON vector_embeddings(content_id);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_vector ON vector_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Table for storing file attachments as base64-encoded content in PostgreSQL
CREATE TABLE IF NOT EXISTS attachments(
  id SERIAL PRIMARY KEY,
  file_id TEXT UNIQUE NOT NULL,  -- UUID for external reference
  project_id TEXT NOT NULL,
  content_type TEXT NOT NULL, -- 'faq', 'kb', 'document'
  content_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  mime_type TEXT,
  file_size BIGINT,
  file_content_base64 TEXT,   -- Base64-encoded file content stored in database
  storage_backend TEXT DEFAULT 'postgresql', -- 'postgresql', 'local', 's3', 'gcs', etc.
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attachments_project ON attachments(project_id);
CREATE INDEX IF NOT EXISTS idx_attachments_content ON attachments(content_type, content_id);
CREATE INDEX IF NOT EXISTS idx_attachments_file_id ON attachments(file_id);

-- Trigger to update updated_at timestamp for vector_embeddings
CREATE TRIGGER update_vector_embeddings_updated_at 
    BEFORE UPDATE ON vector_embeddings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update updated_at timestamp for attachments  
CREATE TRIGGER update_attachments_updated_at 
    BEFORE UPDATE ON attachments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Projects table for storing project mappings
CREATE TABLE IF NOT EXISTS projects(
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(active);

-- FAQs table for storing FAQ entries
CREATE TABLE IF NOT EXISTS faqs(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  tags TEXT, -- comma-separated tags
  source TEXT, -- 'manual', 'upload', etc.
  source_file TEXT, -- reference to attachment if uploaded
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_faqs_project ON faqs(project_id);
CREATE INDEX IF NOT EXISTS idx_faqs_question ON faqs USING GIN(to_tsvector('english', question));
CREATE INDEX IF NOT EXISTS idx_faqs_answer ON faqs USING GIN(to_tsvector('english', answer));

-- Knowledge Base articles table
CREATE TABLE IF NOT EXISTS kb_articles(
  id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  tags TEXT, -- comma-separated tags
  source TEXT, -- 'manual', 'upload', etc.
  source_file TEXT, -- reference to attachment if uploaded
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kb_articles_project ON kb_articles(project_id);
CREATE INDEX IF NOT EXISTS idx_kb_articles_title ON kb_articles USING GIN(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_kb_articles_content ON kb_articles USING GIN(to_tsvector('english', content));

-- Add triggers for new tables
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faqs_updated_at 
    BEFORE UPDATE ON faqs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_kb_articles_updated_at 
    BEFORE UPDATE ON kb_articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add trigger for sessions table if it has updated_at column
-- (Currently not used but available for future enhancements)