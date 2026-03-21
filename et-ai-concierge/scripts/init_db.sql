-- ET AI Concierge — Database Schema
-- Run: psql -U user -d et_concierge -f init_db.sql

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
