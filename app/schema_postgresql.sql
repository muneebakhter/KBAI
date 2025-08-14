-- PostgreSQL schema for KBAI API
-- This schema supports the same tables as SQLite but with PostgreSQL-specific optimizations

-- Enable pgvector extension for vector storage (if using vector features)
-- CREATE EXTENSION IF NOT EXISTS vector;

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

-- Optional: Vector storage table for embeddings and attachments
-- Uncomment if using pgvector for vector storage
/*
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

-- Table for storing file attachments metadata
CREATE TABLE IF NOT EXISTS attachments(
  id SERIAL PRIMARY KEY,
  project_id TEXT NOT NULL,
  content_type TEXT NOT NULL, -- 'faq', 'kb', 'document'
  content_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  mime_type TEXT,
  file_size BIGINT,
  file_path TEXT, -- Path in storage system
  storage_backend TEXT DEFAULT 'local', -- 'local', 's3', 'gcs', etc.
  metadata JSONB,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_attachments_project ON attachments(project_id);
CREATE INDEX IF NOT EXISTS idx_attachments_content ON attachments(content_type, content_id);
*/

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add trigger for sessions table if it has updated_at column
-- (Currently not used but available for future enhancements)