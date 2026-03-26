"""
ET AI Concierge — RAG Ingestion Pipeline
Parses ET Prime articles, embeds with BGE, and upserts to Qdrant + Elasticsearch.
Includes support for live ET news scraping and deduplication.
"""
import json
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
QDRANT_ET_COLLECTION = "et_news_articles"  # For live scraped articles
ES_INDEX = "et_prime_articles"
ES_ET_INDEX = "et_news_articles"
EMBEDDING_DIM = 1024  # BGE-large-en-v1.5 output dimension

# In-memory deduplication cache (content_hash -> timestamp)
_dedup_cache: Dict[str, datetime] = {}
_dedup_cache_retention_days = 90


# ─── Collection Initialization ─────────────────────────────────────────────────

def init_et_news_collection():
    """Initialize the et_news_articles collection in Qdrant if it doesn't exist."""
    if QdrantClient is None:
        logger.warning("⚠️ qdrant-client not installed. Skipping collection initialization.")
        return
    
    try:
        client = QdrantClient(url=settings.QDRANT_URL)
        
        # Check if collection exists
        try:
            client.get_collection(QDRANT_ET_COLLECTION)
            logger.info(f"✅ Qdrant collection already exists: {QDRANT_ET_COLLECTION}")
            return
        except Exception:
            pass
        
        # Create collection
        client.create_collection(
            collection_name=QDRANT_ET_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"✅ Created Qdrant collection: {QDRANT_ET_COLLECTION}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Qdrant collection: {e}")


def init_et_news_index():
    """Initialize the et_news_articles index in Elasticsearch if it doesn't exist."""
    if Elasticsearch is None:
        logger.warning("⚠️ elasticsearch not installed. Skipping index initialization.")
        return
    
    try:
        es = Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=5)
        
        # Check if index exists
        try:
            exists = es.indices.exists(index=ES_ET_INDEX)
            if exists:
                logger.info(f"✅ Elasticsearch index already exists: {ES_ET_INDEX}")
                return
        except Exception as check_err:
            logger.debug(f"⚠️ Could not check if ES index exists: {check_err}. Will try to create.")
        
        # Try to create index
        try:
            es.indices.create(index=ES_ET_INDEX, body={
                "mappings": {
                    "properties": {
                        "title": {"type": "text", "boost": 2.0},
                        "body": {"type": "text"},
                        "category": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "url": {"type": "keyword"},
                        "source": {"type": "keyword"},
                        "publish_date": {"type": "date"},
                        "scraped_at": {"type": "date"},
                        "content_hash": {"type": "keyword"},
                    }
                }
            })
            logger.info(f"✅ Created Elasticsearch index: {ES_ET_INDEX}")
        except Exception as create_err:
            logger.warning(f"⚠️ Could not create ES index: {create_err}. Elasticsearch will be skipped for ingestion.")
        
    except Exception as e:
        logger.warning(f"⚠️ Elasticsearch unavailable: {e}. Continuing without ES.")


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


# ─── ET News Ingestion Functions ──────────────────────────────────────────────

def check_duplicate(content_hash: str) -> bool:
    """
    Check if article (by content_hash) already exists in dedup cache or Qdrant.
    Returns True if duplicate, False if new.
    """
    # Check in-memory cache first
    if content_hash in _dedup_cache:
        stored_time = _dedup_cache[content_hash]
        age_days = (datetime.utcnow() - stored_time).days
        if age_days < _dedup_cache_retention_days:
            logger.debug(f"✅ Cache hit: Article is duplicate (age: {age_days}d)")
            return True
        else:
            # Expired, remove from cache
            del _dedup_cache[content_hash]

    # Check in Qdrant using metadata filter
    if QdrantClient is None:
        logger.warning("⚠️ Qdrant not available, skipping DB check")
        return False

    try:
        client = QdrantClient(url=settings.QDRANT_URL)
        
        # Search for existing article with same content_hash
        results = client.scroll(
            collection_name=QDRANT_ET_COLLECTION,
            limit=1,
            with_payload=True,
        )

        for point in results[0]:
            if point.payload.get("content_hash") == content_hash:
                logger.debug(f"✅ DB hit: Article is duplicate in Qdrant")
                _dedup_cache[content_hash] = datetime.utcnow()
                return True

    except Exception as e:
        logger.warning(f"⚠️ Could not check Qdrant for duplicates: {e}")
        # Don't fail on Qdrant check, proceed with ingestion

    # Not a duplicate
    logger.debug(f"✅ New article: {content_hash[:8]}...")
    _dedup_cache[content_hash] = datetime.utcnow()
    return False


def ingest_et_articles(articles: List[Dict[str, Any]]):
    """
    Ingest scraped ET articles with deduplication.
    Stores in separate ET news collection for live content.
    """
    if not articles:
        logger.warning("⚠️ No articles to ingest")
        return

    logger.info(f"📰 Ingesting {len(articles)} ET news articles...")

    # Add standard fields if missing
    for article in articles:
        if "id" not in article:
            article["id"] = str(uuid.uuid4())

    # Upsert to Qdrant (ET News collection)
    _upsert_et_articles_to_qdrant(articles)

    # Index to Elasticsearch (ET News index)
    _index_et_articles_to_elasticsearch(articles)

    logger.info(f"✅ Ingested {len(articles)} ET articles")


def _upsert_et_articles_to_qdrant(articles: List[Dict[str, Any]]):
    """Upsert ET articles to dedicated Qdrant collection."""
    if QdrantClient is None:
        logger.warning("⚠️ qdrant-client not installed. Skipping Qdrant upsert.")
        return

    client = QdrantClient(url=settings.QDRANT_URL)

    # Create collection if not exists
    try:
        client.get_collection(QDRANT_ET_COLLECTION)
    except Exception:
        client.create_collection(
            collection_name=QDRANT_ET_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"✅ Created Qdrant collection: {QDRANT_ET_COLLECTION}")

    # Process and upsert
    points = []
    all_texts = []
    all_metadata = []

    for article in articles:
        chunks = chunk_text(article.get("body", ""))
        for i, chunk in enumerate(chunks):
            all_texts.append(chunk)
            all_metadata.append({
                "article_id": article["id"],
                "title": article["title"],
                "source": article.get("source", "ET"),
                "category": article.get("category", "general"),
                "chunk_index": i,
                "url": article.get("url", ""),
                "tags": article.get("tags", []),
                "publish_date": article.get("publish_date", ""),
                "content_hash": article.get("content_hash", ""),
                "scraped_at": article.get("scraped_at", ""),
            })

    if not all_texts:
        logger.warning("⚠️ No text chunks to embed")
        return

    logger.info(f"🔢 Embedding {len(all_texts)} text chunks...")
    embeddings = embed_texts(all_texts)

    for j, (text, meta, emb) in enumerate(zip(all_texts, all_metadata, embeddings)):
        points.append(PointStruct(
            id=generate_doc_id(text),
            vector=emb,
            payload={**meta, "text": text},
        ))

    client.upsert(collection_name=QDRANT_ET_COLLECTION, points=points)
    logger.info(f"✅ Upserted {len(points)} chunks to Qdrant {QDRANT_ET_COLLECTION}")


def _index_et_articles_to_elasticsearch(articles: List[Dict[str, Any]]):
    """Index ET articles to Elasticsearch for BM25 search (non-critical)."""
    if Elasticsearch is None:
        logger.warning("⚠️ elasticsearch not installed. Skipping ES indexing.")
        return

    try:
        # Create client with API compatibility mode
        es = Elasticsearch(
            settings.ELASTICSEARCH_URL, 
            request_timeout=5,
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )

        # Try to create index if not exists
        try:
            if not es.indices.exists(index=ES_ET_INDEX):
                try:
                    es.indices.create(index=ES_ET_INDEX, body={
                        "mappings": {
                            "properties": {
                                "title": {"type": "text", "boost": 2.0},
                                "body": {"type": "text"},
                                "category": {"type": "keyword"},
                                "tags": {"type": "keyword"},
                                "url": {"type": "keyword"},
                                "source": {"type": "keyword"},
                                "publish_date": {"type": "date"},
                                "scraped_at": {"type": "date"},
                                "content_hash": {"type": "keyword"},
                            }
                        }
                    })
                    logger.info(f"✅ Created Elasticsearch index: {ES_ET_INDEX}")
                except Exception as idx_err:
                    logger.debug(f"⚠️ Could not create ES index: {idx_err}. Skipping ES indexing.")
                    return  # Skip ES indexing if index creation fails
        except Exception as exists_err:
            logger.debug(f"⚠️ Could not check ES index: {exists_err}. Skipping ES indexing.")
            return

        # Index articles (best effort)
        indexed_count = 0
        for article in articles:
            try:
                es.index(index=ES_ET_INDEX, id=article["id"], body={
                    "title": article["title"],
                    "body": article.get("body", ""),
                    "category": article.get("category", "general"),
                    "tags": article.get("tags", []),
                    "url": article.get("url", ""),
                    "source": article.get("source", "ET"),
                    "publish_date": article.get("publish_date", ""),
                    "scraped_at": article.get("scraped_at", ""),
                    "content_hash": article.get("content_hash", ""),
                })
                indexed_count += 1
            except Exception as article_err:
                logger.debug(f"⚠️ Could not index article {article['id']}: {article_err}")
                continue

        logger.info(f"✅ Indexed {indexed_count}/{len(articles)} articles to Elasticsearch {ES_ET_INDEX}")

    except Exception as e:
        logger.debug(f"⚠️ Elasticsearch unavailable: {e}. Continuing without ES.")

