PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY,           -- sess_*
  token_jti TEXT UNIQUE NOT NULL,
  client_name TEXT NOT NULL,
  scopes TEXT NOT NULL,          -- comma-separated
  issued_at TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  ip_lock TEXT,                  -- optional CIDR/addr
  disabled INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS traces(
  id TEXT PRIMARY KEY,           -- tr_*
  ts TEXT NOT NULL,
  method TEXT NOT NULL,
  path TEXT NOT NULL,
  status INTEGER NOT NULL,
  latency_ms REAL NOT NULL,
  ip TEXT,
  ua TEXT,
  headers_slim TEXT,             -- JSON
  query TEXT,                    -- JSON
  body_sha256 TEXT,
  token_sub TEXT,                -- sessions.id
  error TEXT
);

CREATE INDEX IF NOT EXISTS idx_traces_ts ON traces(ts);
CREATE INDEX IF NOT EXISTS idx_traces_path ON traces(path);
CREATE INDEX IF NOT EXISTS idx_traces_status ON traces(status);
CREATE INDEX IF NOT EXISTS idx_traces_token_sub ON traces(token_sub);