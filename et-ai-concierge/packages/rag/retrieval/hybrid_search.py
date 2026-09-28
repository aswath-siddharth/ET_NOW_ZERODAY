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

embedding_model = None

def _get_embedding_model():
    global embedding_model
    if embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            embedding_model = None
    return embedding_model

import sys, os, json, socket
from urllib.parse import urlparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
from config import settings

QDRANT_COLLECTION = "et_news_articles"
ES_INDEX = "et_prime_articles"

# ─── Reachability Cache (prevents socket hang when Docker is offline) ─────────
_qdrant_available: Optional[bool] = None
_es_available: Optional[bool] = None

def _is_service_reachable(url_str: str, default_port: int, timeout_sec: float = 0.2) -> bool:
    """Quick socket check to verify if a local service is listening before issuing HTTP calls."""
    try:
        parsed = urlparse(url_str)
        host = parsed.hostname or "localhost"
        port = parsed.port or default_port
        with socket.create_connection((host, port), timeout=timeout_sec):
            return True
    except Exception:
        return False


# ─── Local Seed Data Fallback ────────────────────────────────────────────────
_seed_articles_cache: Optional[List[Dict[str, Any]]] = None

def _load_seed_articles() -> List[Dict[str, Any]]:
    global _seed_articles_cache
    if _seed_articles_cache is None:
        seed_path = os.path.join(os.path.dirname(__file__), "..", "..", "agents", "data", "seed_content.json")
        try:
            if os.path.exists(seed_path):
                with open(seed_path, "r", encoding="utf-8") as f:
                    _seed_articles_cache = json.load(f)
            else:
                _seed_articles_cache = []
        except Exception as e:
            print(f"[WARN] Failed to load seed_content.json: {e}")
            _seed_articles_cache = []
    return _seed_articles_cache


def search_local_seed_articles(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Instant in-memory keyword/tag search over seed articles when DB is offline."""
    articles = _load_seed_articles()
    if not articles:
        return []

    tokens = [t.lower() for t in query.split() if len(t) > 2]
    scored_articles = []

    for art in articles:
        title = art.get("title", "").lower()
        tags = [str(t).lower() for t in art.get("tags", [])]
        category = art.get("category", "").lower()
        content = art.get("content", "").lower()

        score = 0.0
        for token in tokens:
            if token in title:
                score += 3.0
            if any(token in t for t in tags):
                score += 2.0
            if token in category:
                score += 1.5
            if token in content[:300]:
                score += 1.0

        if score > 0:
            scored_articles.append((score, art))

    scored_articles.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, art in scored_articles[:limit]:
        results.append({
            "id": art.get("id"),
            "score": round(score, 2),
            "text": art.get("content", "")[:600],
            "title": art.get("title", ""),
            "sector": art.get("category", ""),
            "url": art.get("source_url", ""),
            "tags": art.get("tags", []),
            "source": "local_seed",
        })

    # If no specific match, return the first few general articles
    if not results and articles:
        for art in articles[:limit]:
            results.append({
                "id": art.get("id"),
                "score": 0.5,
                "text": art.get("content", "")[:600],
                "title": art.get("title", ""),
                "sector": art.get("category", ""),
                "url": art.get("source_url", ""),
                "tags": art.get("tags", []),
                "source": "local_seed",
            })

    return results


# ─── Vector Search (Qdrant) ───────────────────────────────────────────────────

def vector_search(
    query: str,
    limit: int = 10,
    sector_filter: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Semantic vector search over Qdrant with offline bypass."""
    global _qdrant_available
    if _qdrant_available is False:
        return []

    if _qdrant_available is None:
        _qdrant_available = _is_service_reachable(getattr(settings, "QDRANT_URL", "http://localhost:6333"), 6333)
        if not _qdrant_available:
            print("[INFO] Qdrant is offline — bypassing vector socket calls")
            return []

    emb = _get_embedding_model()
    if QdrantClient is None or emb is None:
        return []

    try:
        client = QdrantClient(url=settings.QDRANT_URL, timeout=1.0)
        query_vector = emb.encode(query, normalize_embeddings=True).tolist()

        # Build filter
        qdrant_filter = None
        if sector_filter:
            qdrant_filter = Filter(must=[
                FieldCondition(key="sector", match=MatchAny(any=sector_filter))
            ])

        query_response = client.query_points(
            collection_name=QDRANT_COLLECTION,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
        )
        
        results = query_response.points if hasattr(query_response, 'points') else []
        
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
        _qdrant_available = False
        print(f"[WARN] Qdrant search failed: {e} — cached offline")
        return []


# ─── Lexical Search (Elasticsearch BM25) ─────────────────────────────────────

def lexical_search(
    query: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """BM25 keyword search over Elasticsearch with offline bypass."""
    global _es_available
    if _es_available is False:
        return []

    if _es_available is None:
        _es_available = _is_service_reachable(getattr(settings, "ELASTICSEARCH_URL", "http://localhost:9200"), 9200)
        if not _es_available:
            print("[INFO] Elasticsearch is offline — bypassing lexical socket calls")
            return []

    if Elasticsearch is None:
        return []

    try:
        es = Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=1.0)
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
        _es_available = False
        print(f"[WARN] Elasticsearch search failed: {e} — cached offline")
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
    Falls back instantly to local seed articles when offline.
    """
    vector_results = vector_search(query, limit=limit, sector_filter=sector_filter)
    lexical_results = lexical_search(query, limit=limit)

    if not vector_results and not lexical_results:
        # Fast local fallback
        return search_local_seed_articles(query, limit=limit)

    fused = reciprocal_rank_fusion([vector_results, lexical_results])
    return fused[:limit]
