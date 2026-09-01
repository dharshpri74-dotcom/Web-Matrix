"""
FinVerse — Database models for logging, metrics, and analytics.
SQLite for prototype — structured for easy PostgreSQL migration.
"""
import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "finverse.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            persona TEXT NOT NULL,
            overall_signal TEXT,
            overall_confidence REAL,
            agent_latency_momentum_ms REAL,
            agent_latency_sentiment_ms REAL,
            agent_latency_fundamentals_ms REAL,
            total_latency_ms REAL,
            agents_used TEXT,  -- JSON array
            agents_missing TEXT,  -- JSON array
            simulate_outage INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            signal TEXT,
            confidence REAL,
            latency_ms REAL,
            data_sources TEXT,  -- JSON array
            error INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metadata TEXT,  -- JSON
            recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_symbol ON analysis_sessions(symbol);
        CREATE INDEX IF NOT EXISTS idx_sessions_created ON analysis_sessions(created_at);
        CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name, recorded_at);
    """)
    conn.commit()
    conn.close()


def log_session(result: dict) -> int:
    """Log a full analysis session. Returns session ID."""
    conn = get_db()
    agents_used = result.get("synthesis", {}).get("agents_used", [])
    agents_missing = result.get("synthesis", {}).get("agents_missing", [])

    agent_latencies = {}
    for name in ["momentum", "sentiment", "fundamentals"]:
        agent_data = result.get("agent_results", {}).get(name, {})
        agent_latencies[name] = agent_data.get("metadata", {}).get("latency_ms", 0) if agent_data else 0

    cur = conn.execute(
        """INSERT INTO analysis_sessions
           (symbol, persona, overall_signal, overall_confidence,
            agent_latency_momentum_ms, agent_latency_sentiment_ms, agent_latency_fundamentals_ms,
            total_latency_ms, agents_used, agents_missing, simulate_outage)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result.get("symbol", ""),
            result.get("persona_applied", {}).get("id", "unknown"),
            result.get("synthesis", {}).get("overall_signal", "neutral"),
            result.get("synthesis", {}).get("overall_confidence", 0),
            agent_latencies.get("momentum", 0),
            agent_latencies.get("sentiment", 0),
            agent_latencies.get("fundamentals", 0),
            result.get("total_latency_ms", 0),
            json.dumps(agents_used),
            json.dumps(agents_missing),
            1 if result.get("simulate_outage") else 0,
        ),
    )
    session_id = cur.lastrowid

    # Log individual agents
    for name in ["momentum", "sentiment", "fundamentals"]:
        agent_data = result.get("agent_results", {}).get(name, {})
        if agent_data:
            conn.execute(
                """INSERT INTO agent_logs
                   (session_id, agent_name, signal, confidence, latency_ms, data_sources, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    agent_data.get("agent", name),
                    agent_data.get("signal"),
                    agent_data.get("confidence", 0),
                    agent_data.get("metadata", {}).get("latency_ms", 0) if isinstance(agent_data.get("metadata"), dict) else 0,
                    json.dumps(agent_data.get("data_sources", [])),
                    1 if agent_data.get("error") else 0,
                ),
            )

    conn.commit()
    conn.close()
    return session_id


def log_metric(name: str, value: float, metadata: dict = None):
    """Log a named metric data point."""
    conn = get_db()
    conn.execute(
        "INSERT INTO metrics (metric_name, metric_value, metadata) VALUES (?, ?, ?)",
        (name, value, json.dumps(metadata) if metadata else None),
    )
    conn.commit()
    conn.close()


def get_metrics_summary() -> dict:
    """Get summary statistics for the metrics panel."""
    conn = get_db()

    # Agent latency stats
    avg_latencies = {}
    for agent in ["momentum", "sentiment", "fundamentals"]:
        col = f"agent_latency_{agent}_ms"
        row = conn.execute(
            f"SELECT AVG({col}) as avg_lat, COUNT(*) as cnt FROM analysis_sessions WHERE {col} > 0"
        ).fetchone()
        avg_latencies[agent] = {
            "avg_ms": round(row["avg_lat"] or 0, 1),
            "count": row["cnt"] or 0,
        }

    # Signal distribution
    signal_dist = conn.execute(
        "SELECT overall_signal, COUNT(*) as cnt FROM analysis_sessions GROUP BY overall_signal"
    ).fetchall()
    signal_distribution = {r["overall_signal"]: r["cnt"] for r in signal_dist}

    # Confidence stats
    conf_row = conn.execute(
        "SELECT AVG(overall_confidence) as avg_conf, MIN(overall_confidence) as min_conf, MAX(overall_confidence) as max_conf FROM analysis_sessions"
    ).fetchone()

    # Outage impact
    outage_sessions = conn.execute(
        "SELECT AVG(overall_confidence) as avg_conf_outage FROM analysis_sessions WHERE simulate_outage = 1"
    ).fetchone()

    normal_sessions = conn.execute(
        "SELECT AVG(overall_confidence) as avg_conf_normal FROM analysis_sessions WHERE simulate_outage = 0"
    ).fetchone()

    # Total sessions
    total = conn.execute("SELECT COUNT(*) as cnt FROM analysis_sessions").fetchone()

    conn.close()

    return {
        "total_sessions": total["cnt"],
        "agent_latencies": avg_latencies,
        "signal_distribution": signal_distribution,
        "confidence_stats": {
            "avg": round(conf_row["avg_conf"] or 0, 3),
            "min": round(conf_row["min_conf"] or 0, 3),
            "max": round(conf_row["max_conf"] or 0, 3),
        },
        "degradation_impact": {
            "avg_confidence_with_outage": round(outage_sessions["avg_conf_outage"] or 0, 3),
            "avg_confidence_normal": round(normal_sessions["avg_conf_normal"] or 0, 3),
        },
    }


def get_recent_sessions(limit: int = 20) -> list[dict]:
    """Get recent analysis sessions."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
