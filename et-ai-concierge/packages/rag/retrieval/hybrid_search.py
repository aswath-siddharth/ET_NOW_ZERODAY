"""
ET AI Concierge — Hybrid Retrieval
Vector (Qdrant) + BM25 (Elasticsearch) + Reciprocal Rank Fusion
"""
from typing import List, Dict, Any, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchAny
except ImportError:
    QdrantClient = None

try:
    from elasticsearch import Elasticsearch
except ImportError:
    Elasticsearch = None

try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
except ImportError:
    embedding_model = None

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
from config import settings


QDRANT_COLLECTION = "et_prime_articles"
ES_INDEX = "et_prime_articles"


# ─── Vector Search (Qdrant) ───────────────────────────────────────────────────

def vector_search(
    query: str,
    limit: int = 10,
    sector_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Semantic vector search over Qdrant."""
    if QdrantClient is None or embedding_model is None:
        return []

    client = QdrantClient(url=settings.QDRANT_URL)
    query_vector = embedding_model.encode(query, normalize_embeddings=True).tolist()

    # Build filter
    qdrant_filter = None
    if sector_filter:
        qdrant_filter = Filter(must=[
            FieldCondition(key="sector", match=MatchAny(any=sector_filter))
        ])

    try:
        results = client.search(
            collection_name=QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
        )
        return [
            {
                "id": str(r.id),
                "score": r.score,
                "text": r.payload.get("text", ""),
                "title": r.payload.get("title", ""),
                "sector": r.payload.get("sector", ""),
                "url": r.payload.get("url", ""),
                "tags": r.payload.get("tags", []),
                "source": "vector",
            }
            for r in results
        ]
    except Exception as e:
        print(f"⚠️ Qdrant search failed: {e}")
        return []


# ─── Lexical Search (Elasticsearch BM25) ─────────────────────────────────────

def lexical_search(
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """BM25 keyword search over Elasticsearch."""
    if Elasticsearch is None:
        return []

    es = Elasticsearch(settings.ELASTICSEARCH_URL)

    try:
        results = es.search(
            index=ES_INDEX,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "body", "summary", "tags"],
                    }
                },
                "size": limit,
            }
        )
        return [
            {
                "id": hit["_id"],
                "score": hit["_score"],
                "text": hit["_source"].get("body", hit["_source"].get("summary", "")),
                "title": hit["_source"].get("title", ""),
                "sector": hit["_source"].get("sector", ""),
                "url": hit["_source"].get("url", ""),
                "tags": hit["_source"].get("tags", []),
                "source": "lexical",
            }
            for hit in results["hits"]["hits"]
        ]
    except Exception as e:
        print(f"⚠️ Elasticsearch search failed: {e}")
        return []


# ─── Reciprocal Rank Fusion ──────────────────────────────────────────────────

def reciprocal_rank_fusion(
    result_lists: List[List[Dict[str, Any]]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Merge multiple ranked result lists using Reciprocal Rank Fusion.
    RRF(d) = Σ 1 / (k + rank(d))
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for results in result_lists:
        for rank, doc in enumerate(results, 1):
            doc_id = doc.get("id", doc.get("title", str(rank)))
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            doc_map[doc_id] = doc

    # Sort by fusion score
    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused = []
    for doc_id in sorted_ids:
        doc = doc_map[doc_id]
        doc["rrf_score"] = scores[doc_id]
        fused.append(doc)

    return fused


# ─── Hybrid Search ────────────────────────────────────────────────────────────

def hybrid_search(
    query: str,
    limit: int = 10,
    sector_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Combined vector + lexical search with RRF fusion.
    This is the main search function used by the Editorial Agent.
    """
    vector_results = vector_search(query, limit=limit, sector_filter=sector_filter)
    lexical_results = lexical_search(query, limit=limit)

    fused = reciprocal_rank_fusion([vector_results, lexical_results])
    return fused[:limit]
