"""
ET AI Concierge — RAG Ingestion Pipeline
Parses ET Prime articles, embeds with BGE, and upserts to Qdrant + Elasticsearch.
"""
import json
import uuid
import hashlib
from typing import List, Dict, Any

# ─── Optional imports (gracefully degrade if not installed) ───────────────────
try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
except ImportError:
    embedding_model = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance, PointStruct
except ImportError:
    QdrantClient = None

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
from config import settings


# ─── Constants ────────────────────────────────────────────────────────────────

QDRANT_COLLECTION = "et_prime_articles"
ES_INDEX = "et_prime_articles"
EMBEDDING_DIM = 1024  # BGE-large-en-v1.5 output dimension


# ─── Document Chunking ───────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def generate_doc_id(text: str) -> str:
    """Generate a deterministic UUID from text content."""
    return str(uuid.UUID(hashlib.md5(text.encode()).hexdigest()))


# ─── Embedding ────────────────────────────────────────────────────────────────

def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed texts using the local BGE model."""
    if embedding_model is None:
        print("⚠️ sentence-transformers not installed. Returning zero vectors.")
        return [[0.0] * EMBEDDING_DIM for _ in texts]
    
    embeddings = embedding_model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


# ─── Qdrant Upsert ───────────────────────────────────────────────────────────

def upsert_to_qdrant(articles: List[Dict[str, Any]]):
    """Upsert article chunks to Qdrant vector store."""
    if QdrantClient is None:
        print("⚠️ qdrant-client not installed. Skipping Qdrant upsert.")
        return

    client = QdrantClient(url=settings.QDRANT_URL)

    # Create collection if not exists
    try:
        client.get_collection(QDRANT_COLLECTION)
    except Exception:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        print(f"✅ Created Qdrant collection: {QDRANT_COLLECTION}")

    # Process and upsert
    points = []
    all_texts = []
    all_metadata = []

    for article in articles:
        chunks = chunk_text(article.get("body", article.get("summary", "")))
        for i, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_metadata.append({
                "article_id": article["id"],
                "title": article["title"],
                "sector": article.get("sector", ""),
                "chunk_index": i,
                "url": article.get("url", ""),
                "tags": article.get("tags", []),
                "paywall": article.get("paywall", False),
            })

    if not all_texts:
        return

    embeddings = embed_texts(all_texts)

    for j, (text, meta, emb) in enumerate(zip(all_texts, all_metadata, embeddings)):
        points.append(PointStruct(
            id=generate_doc_id(text),
            vector=emb,
            payload={**meta, "text": text},
        ))

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    print(f"✅ Upserted {len(points)} chunks to Qdrant")


# ─── Elasticsearch Index ─────────────────────────────────────────────────────

def index_to_elasticsearch(articles: List[Dict[str, Any]]):
    """Index articles to Elasticsearch for BM25 search."""
    if Elasticsearch is None:
        print("⚠️ elasticsearch not installed. Skipping ES indexing.")
        return

    es = Elasticsearch(settings.ELASTICSEARCH_URL)

    # Create index if not exists
    if not es.indices.exists(index=ES_INDEX):
        es.indices.create(index=ES_INDEX, body={
            "mappings": {
                "properties": {
                    "title": {"type": "text", "boost": 2.0},
                    "body": {"type": "text"},
                    "summary": {"type": "text"},
                    "sector": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "url": {"type": "keyword"},
                    "paywall": {"type": "boolean"},
                }
            }
        })
        print(f"✅ Created Elasticsearch index: {ES_INDEX}")

    # Index articles
    for article in articles:
        es.index(index=ES_INDEX, id=article["id"], body={
            "title": article["title"],
            "body": article.get("body", article.get("summary", "")),
            "summary": article.get("summary", ""),
            "sector": article.get("sector", ""),
            "tags": article.get("tags", []),
            "url": article.get("url", ""),
            "paywall": article.get("paywall", False),
        })

    print(f"✅ Indexed {len(articles)} articles to Elasticsearch")


# ─── Main Ingestion Function ─────────────────────────────────────────────────

def ingest_articles(articles: List[Dict[str, Any]]):
    """Full ingestion pipeline: embed → Qdrant + Elasticsearch."""
    print(f"📄 Ingesting {len(articles)} articles...")
    upsert_to_qdrant(articles)
    index_to_elasticsearch(articles)
    print("✅ Ingestion complete!")
