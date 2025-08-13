from __future__ import annotations
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Tuple
import json
import threading

class DB:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.RLock()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str, params: Tuple = ()) -> None:
        with self._lock:
            with self.connect() as c:
                c.execute(sql, params)
                c.commit()

    def executemany(self, sql: str, rows: Iterable[Tuple]) -> None:
        with self._lock:
            with self.connect() as c:
                c.executemany(sql, rows)
                c.commit()

    def query(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        with self._lock:
            with self.connect() as c:
                cur = c.execute(sql, params)
                return cur.fetchall()

    # Sessions
    def create_session(self, id: str, jti: str, client_name: str, scopes_csv: str, issued_at: str, expires_at: str, ip_lock: Optional[str]) -> None:
        self.execute(
            "INSERT INTO sessions(id, token_jti, client_name, scopes, issued_at, expires_at, ip_lock, disabled) VALUES (?,?,?,?,?,?,?,0)",
            (id, jti, client_name, scopes_csv, issued_at, expires_at, ip_lock)
        )

    def get_session_by_id(self, id: str) -> Optional[sqlite3.Row]:
        rows = self.query("SELECT * FROM sessions WHERE id=? LIMIT 1", (id,))
        return rows[0] if rows else None

    def get_session_by_jti(self, jti: str) -> Optional[sqlite3.Row]:
        rows = self.query("SELECT * FROM sessions WHERE token_jti=? LIMIT 1", (jti,))
        return rows[0] if rows else None

    def disable_session(self, id: str) -> None:
        self.execute("UPDATE sessions SET disabled=1 WHERE id=?", (id,))

    # Traces
    def insert_trace(self, trace: Dict[str, Any]) -> None:
        self.execute(
            """INSERT INTO traces(id, ts, method, path, status, latency_ms, ip, ua, headers_slim, query, body_sha256, token_sub, error)
                 VALUES (:id, :ts, :method, :path, :status, :latency_ms, :ip, :ua, :headers_slim, :query, :body_sha256, :token_sub, :error)""" ,
            trace
        )

    def get_trace_by_id(self, trace_id: str) -> Optional[sqlite3.Row]:
        """Get a single trace by ID."""
        rows = self.query("SELECT * FROM traces WHERE id=? LIMIT 1", (trace_id,))
        return rows[0] if rows else None

    def list_traces(self, since: Optional[str], limit: int, status: Optional[int], path: Optional[str], ip: Optional[str], has_error: Optional[bool] = None, since_seconds: Optional[int] = None) -> List[sqlite3.Row]:
        sql = "SELECT * FROM traces WHERE 1=1"
        params: List[Any] = []
        
        if since:
            sql += " AND ts >= ?"
            params.append(since)
        
        if since_seconds is not None:
            from datetime import datetime, timedelta
            since_time = (datetime.utcnow() - timedelta(seconds=since_seconds)).isoformat(timespec='seconds') + "Z"
            sql += " AND ts >= ?"
            params.append(since_time)
            
        if status is not None:
            sql += " AND status = ?"
            params.append(status)
            
        if path:
            sql += " AND path LIKE ?"
            params.append('%' + path + '%')  # substring search
            
        if ip:
            sql += " AND ip = ?"
            params.append(ip)
            
        if has_error is not None:
            if has_error:
                sql += " AND error IS NOT NULL"
            else:
                sql += " AND error IS NULL"
                
        sql += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        return self.query(sql, tuple(params))

    def metrics_summary(self, window_seconds: int) -> Dict[str, Any]:
        from datetime import datetime, timedelta
        since = (datetime.utcnow() - timedelta(seconds=window_seconds)).isoformat(timespec='seconds') + "Z"
        rows = self.query("SELECT status, path, latency_ms FROM traces WHERE ts >= ?", (since,))
        total = len(rows)
        by_status = {"2xx":0,"4xx":0,"5xx":0}
        top_paths: Dict[str,int] = {}
        latencies = []
        unauthorized = 0
        for r in rows:
            s = int(r["status"])
            if 200 <= s < 300: by_status["2xx"] += 1
            elif 400 <= s < 500: by_status["4xx"] += 1
            elif 500 <= s < 600: by_status["5xx"] += 1
            if s == 401: unauthorized += 1
            p = r["path"]
            top_paths[p] = top_paths.get(p, 0) + 1
            latencies.append(float(r["latency_ms"]))
        # compute p95
        p95 = None
        if latencies:
            latencies.sort()
            idx = int(0.95 * (len(latencies)-1))
            p95 = latencies[idx]
        top = sorted(top_paths.items(), key=lambda kv: kv[1], reverse=True)[:10]
        return {
            "window": f"{window_seconds//60}m" if window_seconds%3600!=0 else f"{window_seconds//3600}h",
            "total": total,
            "by_status": by_status,
            "top_paths": top,
            "unauthorized": unauthorized,
            "p95_latency_ms": p95
        }

    def add_trace_metadata(self, trace_id: Optional[str], metadata: Dict[str, Any]) -> None:
        """Add metadata to a trace for enhanced logging."""
        if not trace_id:
            return
        
        try:
            # Convert metadata to JSON string
            metadata_json = json.dumps(metadata)
            
            # Update the trace with metadata (if the trace exists)
            # This assumes there's a metadata column, if not, this will fail silently
            self.execute(
                "UPDATE traces SET metadata = ? WHERE id = ?",
                (metadata_json, trace_id)
            )
        except Exception:
            # Fail silently if metadata column doesn't exist
            pass