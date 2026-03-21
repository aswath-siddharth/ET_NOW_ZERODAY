"""
ET AI Concierge — Database Layer
PostgreSQL models and session management.
"""
import uuid
import datetime
from typing import Optional, Dict, Any, List
import json

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
"""


# ─── Database Connection Helper ───────────────────────────────────────────────

def get_connection():
    """Get a psycopg2 connection to the local Postgres."""
    return psycopg2.connect(settings.DATABASE_URL)


def init_db():
    """Create tables if they don't exist."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(INIT_SQL)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database tables initialized successfully")
    except Exception as e:
        print(f"⚠️ Database init skipped (not available): {e}")


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
        pass
    return str(uid)


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
        print(f"⚠️ Could not update user profile: {e}")


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
        return None


# ─── Audit Logging ────────────────────────────────────────────────────────────

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
    except Exception as e:
        print(f"⚠️ Audit log failed: {e}")


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
        print(f"⚠️ Could not save chat message: {e}")


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
        print(f"⚠️ Could not retrieve chat history: {e}")
        return []
