"""
ET AI Concierge — Centralized Configuration
Loads all settings from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── LLM (Groq) ──────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # ── Auth ────────────────────────────────────
    AUTH_SECRET: str = os.getenv("AUTH_SECRET", "")

    # ── Redis (Local) ────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # ── PostgreSQL (Local) ───────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/et_concierge")

    # ── Qdrant (Local Docker) ────────────────────
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")

    # ── Elasticsearch (Local Docker) ─────────────
    ELASTICSEARCH_URL: str = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # ── Neo4j (Local Docker) ─────────────────────
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "local_password")

    # ── External APIs (Free Tiers) ───────────────
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")
    OPENWEATHERMAP_API_KEY: str = os.getenv("OPENWEATHERMAP_API_KEY", "")
    DAILY_API_KEY: str = os.getenv("DAILY_API_KEY", "")

    # ── Observability ────────────────────────────
    LANGSMITH_API_KEY: str = os.getenv("LANGSMITH_API_KEY", "")
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    # ── Compliance ───────────────────────────────
    ZENDESK_API_KEY: str = os.getenv("ZENDESK_API_KEY", "")
    ZENDESK_SUBDOMAIN: str = os.getenv("ZENDESK_SUBDOMAIN", "")

    # ── Voice ────────────────────────────────────
    EDGE_TTS_VOICE: str = "en-IN-NeerjaNeural"

    # ── Embedding Model ──────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"


settings = Settings()
