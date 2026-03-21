"""
ET AI Concierge — Data Ingestion Pipeline
Loads seed content, chunks text, generates embeddings, and inserts into PostgreSQL (pgvector).

Usage: python ingest.py
"""
import json
import os
import sys
import uuid

try:
    import psycopg2
    import psycopg2.extras
    psycopg2.extras.register_uuid()
except ImportError:
    print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "seed_content.json")
CHUNK_SIZE = 500        # characters per chunk
CHUNK_OVERLAP = 100     # overlap between chunks
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/et_concierge")


# ─── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence boundary
        if end < len(text):
            # Look for sentence-ending punctuation near the end
            for boundary in [". ", ".\n", "? ", "!\n", "\n\n"]:
                last_boundary = text.rfind(boundary, start + chunk_size // 2, end + 50)
                if last_boundary != -1:
                    end = last_boundary + len(boundary)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap
        if start >= len(text):
            break

    return chunks


# ─── Embedding ────────────────────────────────────────────────────────────────

_model = None

def get_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            print(f"📦 Loading embedding model: {EMBEDDING_MODEL}...")
            _model = SentenceTransformer(EMBEDDING_MODEL)
            print("✅ Model loaded!")
        except ImportError:
            print("❌ sentence-transformers not installed. Run: pip install sentence-transformers")
            sys.exit(1)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    return embeddings.tolist()


# ─── Database ─────────────────────────────────────────────────────────────────

def get_connection():
    """Create a PostgreSQL connection."""
    return psycopg2.connect(DATABASE_URL)


def ensure_schema(conn):
    """Create the pgvector extension and knowledge_base table if not exists."""
    with conn.cursor() as cur:
        # Enable pgvector
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Create knowledge_base table
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                article_id      VARCHAR(50) NOT NULL,
                title           TEXT NOT NULL,
                category        VARCHAR(100),
                chunk_text      TEXT NOT NULL,
                chunk_index     INTEGER NOT NULL,
                embedding       vector({EMBEDDING_DIM}),
                source_url      TEXT,
                tags            JSONB DEFAULT '[]'::jsonb,
                paywall         BOOLEAN DEFAULT FALSE,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
            );
        """)

        # Create index for vector similarity search
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_kb_embedding
            ON knowledge_base
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 10);
        """)

        # Create index for category filtering
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
        """)

        conn.commit()
        print("✅ Schema ready (pgvector extension + knowledge_base table)")


def clear_knowledge_base(conn):
    """Clear existing data for re-ingestion."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM knowledge_base;")
        conn.commit()
        print("🗑️  Cleared existing knowledge_base data")


def insert_chunks(conn, chunks_data: list[dict]):
    """Batch insert chunks with embeddings."""
    with conn.cursor() as cur:
        for chunk in chunks_data:
            cur.execute("""
                INSERT INTO knowledge_base
                    (id, article_id, title, category, chunk_text, chunk_index, embedding, source_url, tags, paywall)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s::vector, %s, %s::jsonb, %s)
            """, (
                str(uuid.uuid4()),
                chunk["article_id"],
                chunk["title"],
                chunk["category"],
                chunk["chunk_text"],
                chunk["chunk_index"],
                str(chunk["embedding"]),
                chunk["source_url"],
                json.dumps(chunk["tags"]),
                chunk["paywall"],
            ))
        conn.commit()


# ─── Main Pipeline ────────────────────────────────────────────────────────────

def run_ingestion():
    """Main ingestion pipeline: load → chunk → embed → insert."""
    print("=" * 60)
    print("🚀 ET AI Concierge — Knowledge Base Ingestion")
    print("=" * 60)

    # 1. Load seed content
    if not os.path.exists(DATA_FILE):
        print(f"❌ Seed data not found at: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)
    print(f"\n📄 Loaded {len(articles)} articles from seed_content.json")

    # 2. Chunk all articles
    all_chunks = []
    for article in articles:
        text_chunks = chunk_text(article["content"])
        for i, chunk_text_str in enumerate(text_chunks):
            all_chunks.append({
                "article_id": article["id"],
                "title": article["title"],
                "category": article["category"],
                "chunk_text": chunk_text_str,
                "chunk_index": i,
                "source_url": article.get("source_url", ""),
                "tags": article.get("tags", []),
                "paywall": article.get("paywall", False),
            })
    print(f"✂️  Created {len(all_chunks)} chunks (avg {sum(len(c['chunk_text']) for c in all_chunks) // len(all_chunks)} chars/chunk)")

    # 3. Generate embeddings
    print(f"\n🧠 Generating embeddings with {EMBEDDING_MODEL}...")
    texts = [c["chunk_text"] for c in all_chunks]
    embeddings = embed_texts(texts)
    for i, emb in enumerate(embeddings):
        all_chunks[i]["embedding"] = emb
    print(f"✅ Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    # 4. Insert into PostgreSQL
    print(f"\n💾 Inserting into PostgreSQL...")
    conn = get_connection()
    try:
        ensure_schema(conn)
        clear_knowledge_base(conn)
        insert_chunks(conn, all_chunks)
        print(f"✅ Inserted {len(all_chunks)} chunks into knowledge_base table")

        # Verify
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM knowledge_base;")
            count = cur.fetchone()[0]
            print(f"\n📊 Verification: {count} rows in knowledge_base")
    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("🎉 Ingestion complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()
