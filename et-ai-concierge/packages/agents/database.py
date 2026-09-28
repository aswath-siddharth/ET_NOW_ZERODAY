"""
ET AI Concierge — Database Layer
PostgreSQL models and session management.
"""
import uuid
import datetime
from typing import Optional, Dict, Any, List
import json
import os
import sqlite3

try:
    import psycopg2
    import psycopg2.extras
    psycopg2.extras.register_uuid()
except ImportError:
    psycopg2 = None

from config import settings


# ─── SQL Schema ───────────────────────────────────────────────────────────────

INIT_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    email           VARCHAR(255) UNIQUE,
    name            VARCHAR(255),
    image           TEXT,
    auth_provider   VARCHAR(50) DEFAULT 'credentials',
    password_hash   TEXT,
    persona         VARCHAR(50),
    risk_score      INTEGER,
    interests       JSONB DEFAULT '[]'::jsonb,
    goals           JSONB DEFAULT '[]'::jsonb,
    income_type     VARCHAR(30),
    age_group       VARCHAR(10),
    has_emergency_fund BOOLEAN,
    home_ownership  VARCHAR(20),
    investment_horizon VARCHAR(20),
    is_active_trader BOOLEAN DEFAULT FALSE,
    primary_goal    VARCHAR(50),
    onboarding_complete BOOLEAN DEFAULT FALSE,
    has_et_prime    BOOLEAN DEFAULT FALSE,
    profile_completeness FLOAT DEFAULT 0.0
);

-- Migration: add auth columns if they don't exist (safe to re-run)
DO $$ BEGIN
    ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR(255);
    ALTER TABLE users ADD COLUMN IF NOT EXISTS image TEXT;
    ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'credentials';
    ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
EXCEPTION WHEN OTHERS THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS ai_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id         UUID NOT NULL,
    session_id      UUID NOT NULL,
    agent_id        VARCHAR(50) NOT NULL,
    intent          VARCHAR(100),
    recommendation  JSONB,
    sources         JSONB,
    reasoning_trace TEXT,
    model_version   VARCHAR(50),
    confidence      FLOAT,
    hitl_triggered  BOOLEAN DEFAULT FALSE,
    disclaimer_shown BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON ai_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON ai_audit_log(agent_id);

CREATE TABLE IF NOT EXISTS chat_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         VARCHAR(255) NOT NULL,
    session_id      VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL,
    content         TEXT NOT NULL,
    agent_id        VARCHAR(50),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_user_session ON chat_history(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_history(created_at);

-- pgvector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_base (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id      VARCHAR(50) NOT NULL,
    title           TEXT NOT NULL,
    category        VARCHAR(100),
    chunk_text      TEXT NOT NULL,
    chunk_index     INTEGER NOT NULL,
    embedding       vector(384),
    source_url      TEXT,
    tags            JSONB DEFAULT '[]'::jsonb,
    paywall         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
"""


# ─── Database Connection Helper ───────────────────────────────────────────────

_pg_available = False

def get_connection():
    """Get a psycopg2 connection to the local Postgres."""
    if psycopg2 is None:
        raise ConnectionError("psycopg2 is not installed")
    return psycopg2.connect(settings.DATABASE_URL, connect_timeout=1)


# ─── SQLite Fallback Store (When Postgres is unavailable) ─────────────────────

SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "local_dev.db")

def _init_sqlite():
    """Initialize local SQLite database for offline dev without Docker."""
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            email TEXT UNIQUE,
            name TEXT,
            image TEXT,
            auth_provider TEXT DEFAULT 'credentials',
            password_hash TEXT,
            persona TEXT,
            risk_score INTEGER,
            interests TEXT DEFAULT '[]',
            goals TEXT DEFAULT '[]',
            income_type TEXT,
            age_group TEXT,
            has_emergency_fund INTEGER,
            home_ownership TEXT,
            investment_horizon TEXT,
            is_active_trader INTEGER DEFAULT 0,
            primary_goal TEXT,
            onboarding_complete INTEGER DEFAULT 0,
            has_et_prime INTEGER DEFAULT 0,
            profile_completeness REAL DEFAULT 0.0
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            agent_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_audit_log (
            id TEXT PRIMARY KEY,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            intent TEXT,
            recommendation TEXT,
            sources TEXT,
            reasoning_trace TEXT,
            model_version TEXT,
            confidence REAL,
            hitl_triggered INTEGER DEFAULT 0,
            disclaimer_shown INTEGER DEFAULT 0
        )
        """)


def _sqlite_create_user(user_id: Optional[str] = None) -> str:
    _init_sqlite()
    uid = str(uuid.UUID(user_id)) if user_id else str(uuid.uuid4())
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (uid,))
    except Exception:
        pass
    return uid


def _sqlite_create_or_get_user(
    email: str,
    name: Optional[str] = None,
    password: Optional[str] = None,
    provider: str = "credentials",
    image: Optional[str] = None,
) -> tuple[Optional[Dict[str, Any]], bool]:
    _init_sqlite()
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row:
            return dict(row), False

        hashed_pw = None
        if password and pwd_context_available:
            pwd_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

        uid = str(uuid.uuid4())
        cur.execute(
            """INSERT INTO users (id, email, name, image, auth_provider, password_hash)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (uid, email, name, image, provider, hashed_pw),
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE id = ?", (uid,))
        new_row = cur.fetchone()
        return (dict(new_row) if new_row else None), True


def _sqlite_verify_user_credentials(email: str, password: str) -> Optional[Dict[str, Any]]:
    _init_sqlite()
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if row and row["password_hash"] and pwd_context_available:
            try:
                if bcrypt.checkpw(password.encode('utf-8'), row["password_hash"].encode('utf-8')):
                    return dict(row)
            except ValueError:
                pass
    return None


def _sqlite_update_user_profile(user_id: str, profile_data: Dict[str, Any]):
    _init_sqlite()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.execute(
                """UPDATE users SET 
                    persona = ?, risk_score = ?, interests = ?, goals = ?,
                    income_type = ?, age_group = ?, has_emergency_fund = ?,
                    home_ownership = ?, investment_horizon = ?, is_active_trader = ?,
                    primary_goal = ?, onboarding_complete = ?, profile_completeness = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (
                    profile_data.get("persona"),
                    profile_data.get("risk_score"),
                    json.dumps(profile_data.get("interests", [])),
                    json.dumps(profile_data.get("goals", [])),
                    profile_data.get("income_type"),
                    profile_data.get("age_group"),
                    1 if profile_data.get("has_emergency_fund") else 0,
                    profile_data.get("home_ownership"),
                    profile_data.get("investment_horizon"),
                    1 if profile_data.get("is_active_trader") else 0,
                    profile_data.get("primary_goal"),
                    1 if profile_data.get("onboarding_complete") else 0,
                    profile_data.get("profile_completeness", 0.0),
                    str(user_id),
                ),
            )
    except Exception as e:
        print(f"[WARN] SQLite update profile error: {e}")


def _sqlite_get_user(user_id: str) -> Optional[Dict[str, Any]]:
    _init_sqlite()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
            row = cur.fetchone()
            if not row:
                return None
            d = dict(row)
            for f in ["interests", "goals"]:
                if isinstance(d.get(f), str):
                    try:
                        d[f] = json.loads(d[f])
                    except Exception:
                        d[f] = []
            return d
    except Exception:
        return None


def _sqlite_save_chat_message(user_id: str, session_id: str, role: str, content: str, agent_id: Optional[str] = None):
    _init_sqlite()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.execute(
                "INSERT INTO chat_history (id, user_id, session_id, role, content, agent_id) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), str(user_id), str(session_id), role, content, agent_id),
            )
    except Exception as e:
        print(f"[WARN] SQLite save chat message error: {e}")


def _sqlite_get_chat_history(user_id: str, session_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    _init_sqlite()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            if session_id:
                cur.execute(
                    "SELECT * FROM chat_history WHERE user_id = ? AND session_id = ? ORDER BY created_at ASC LIMIT ?",
                    (str(user_id), str(session_id), limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM chat_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (str(user_id), limit),
                )
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []


def init_db():
    """Create tables if they don't exist."""
    global _pg_available
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(INIT_SQL)
        conn.commit()
        cur.close()
        conn.close()
        _pg_available = True
        print("[OK] PostgreSQL database tables initialized successfully")
    except Exception as e:
        _pg_available = False
        print(f"[WARN] PostgreSQL not available ({e}). Using local SQLite fallback.")
        _init_sqlite()


# ─── Password Hashing ─────────────────────────────────────────────────────────

try:
    import bcrypt
    pwd_context_available = True
except ImportError:
    pwd_context_available = False


# ─── User CRUD ────────────────────────────────────────────────────────────────

def create_user(user_id: Optional[str] = None) -> str:
    """Create a new user and return their ID."""
    uid = uuid.UUID(user_id) if user_id else uuid.uuid4()
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (id) VALUES (%s) ON CONFLICT (id) DO NOTHING RETURNING id",
            (uid,)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        return _sqlite_create_user(user_id)
    return str(uid)


def create_or_get_user(
    email: str,
    name: Optional[str] = None,
    password: Optional[str] = None,
    provider: str = "credentials",
    image: Optional[str] = None,
) -> tuple[Optional[Dict[str, Any]], bool]:
    """Create a new user by email or return existing one. Used by auth flow. Returns (user_dict, is_new)."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Check if user exists
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()
        if existing:
            cur.close()
            conn.close()
            return dict(existing), False
        
        # Hash password if provided
        hashed_pw = None
        if password and pwd_context_available:
            pwd_bytes = password.encode('utf-8')
            salt = bcrypt.gensalt()
            hashed_pw = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
        
        uid = uuid.uuid4()
        cur.execute(
            """INSERT INTO users (id, email, name, image, auth_provider, password_hash)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING *""",
            (uid, email, name, image, provider, hashed_pw),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return (dict(row) if row else None), True
    except Exception as e:
        print(f"[INFO] PostgreSQL unavailable ({e}), using SQLite fallback for create_or_get_user")
        return _sqlite_create_or_get_user(email, name, password, provider, image)


def verify_user_credentials(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verify email + password for login. Returns user dict or None."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row and row.get("password_hash") and pwd_context_available:
            try:
                if bcrypt.checkpw(password.encode('utf-8'), row["password_hash"].encode('utf-8')):
                    return dict(row)
            except ValueError:
                pass
        return None
    except Exception as e:
        print(f"[INFO] PostgreSQL unavailable ({e}), using SQLite fallback for verify_user_credentials")
        return _sqlite_verify_user_credentials(email, password)


def update_user_profile(user_id: str, profile_data: Dict[str, Any]):
    """Update a user's profile in Postgres."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """UPDATE users SET 
                persona = %s, risk_score = %s, interests = %s, goals = %s,
                income_type = %s, age_group = %s, has_emergency_fund = %s,
                home_ownership = %s, investment_horizon = %s, is_active_trader = %s,
                primary_goal = %s, onboarding_complete = %s, profile_completeness = %s,
                updated_at = now()
            WHERE id = %s""",
            (
                profile_data.get("persona"),
                profile_data.get("risk_score"),
                json.dumps(profile_data.get("interests", [])),
                json.dumps(profile_data.get("goals", [])),
                profile_data.get("income_type"),
                profile_data.get("age_group"),
                profile_data.get("has_emergency_fund"),
                profile_data.get("home_ownership"),
                profile_data.get("investment_horizon"),
                profile_data.get("is_active_trader"),
                profile_data.get("primary_goal"),
                profile_data.get("onboarding_complete", False),
                profile_data.get("profile_completeness", 0.0),
                uuid.UUID(user_id),
            )
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        _sqlite_update_user_profile(user_id, profile_data)


def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a user profile from Postgres."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE id = %s", (uuid.UUID(user_id),))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return _sqlite_get_user(user_id)


# ─── Audit Logging ────────────────────────────────────────────────────────────

def _sqlite_log_audit(
    user_id: str,
    session_id: str,
    agent_id: str,
    intent: str = "",
    recommendation: Optional[Dict] = None,
    sources: Optional[List[str]] = None,
    reasoning_trace: str = "",
    model_version: str = "llama-3.3-70b-versatile",
    confidence: float = 0.8,
    hitl_triggered: bool = False,
    disclaimer_shown: bool = False,
):
    _init_sqlite()
    try:
        with sqlite3.connect(SQLITE_DB_PATH) as conn:
            conn.execute(
                """INSERT INTO ai_audit_log 
                    (id, user_id, session_id, agent_id, intent, recommendation, sources,
                     reasoning_trace, model_version, confidence, hitl_triggered, disclaimer_shown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    str(user_id),
                    str(session_id),
                    agent_id,
                    intent,
                    json.dumps(recommendation or {}),
                    json.dumps(sources or []),
                    reasoning_trace,
                    model_version,
                    confidence,
                    1 if hitl_triggered else 0,
                    1 if disclaimer_shown else 0,
                )
            )
    except Exception:
        pass


def log_audit(
    user_id: str,
    session_id: str,
    agent_id: str,
    intent: str = "",
    recommendation: Optional[Dict] = None,
    sources: Optional[List[str]] = None,
    reasoning_trace: str = "",
    model_version: str = "llama-3.3-70b-versatile",
    confidence: float = 0.8,
    hitl_triggered: bool = False,
    disclaimer_shown: bool = False,
):
    """Log an AI recommendation to the audit table."""
    if _pg_available:
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO ai_audit_log 
                    (user_id, session_id, agent_id, intent, recommendation, sources,
                     reasoning_trace, model_version, confidence, hitl_triggered, disclaimer_shown)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    uuid.UUID(user_id),
                    uuid.UUID(session_id),
                    agent_id,
                    intent,
                    json.dumps(recommendation or {}),
                    json.dumps(sources or []),
                    reasoning_trace,
                    model_version,
                    confidence,
                    hitl_triggered,
                    disclaimer_shown,
                )
            )
            conn.commit()
            cur.close()
            conn.close()
            return
        except Exception:
            pass
    _sqlite_log_audit(
        user_id, session_id, agent_id, intent, recommendation, sources,
        reasoning_trace, model_version, confidence, hitl_triggered, disclaimer_shown
    )


# ─── Chat History ─────────────────────────────────────────────────────────────

def save_chat_message(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    agent_id: Optional[str] = None,
):
    """Persist a chat message to the chat_history table."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO chat_history (user_id, session_id, role, content, agent_id)
            VALUES (%s, %s, %s, %s, %s)""",
            (user_id, session_id, role, content, agent_id),
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        _sqlite_save_chat_message(user_id, session_id, role, content, agent_id)


def get_chat_history(
    user_id: str,
    session_id: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Retrieve chat messages for a user, optionally filtered by session."""
    try:
        conn = get_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        if session_id:
            cur.execute(
                "SELECT * FROM chat_history WHERE user_id = %s AND session_id = %s ORDER BY created_at ASC LIMIT %s",
                (user_id, session_id, limit),
            )
        else:
            cur.execute(
                "SELECT * FROM chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
                (user_id, limit),
            )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        return _sqlite_get_chat_history(user_id, session_id, limit)
