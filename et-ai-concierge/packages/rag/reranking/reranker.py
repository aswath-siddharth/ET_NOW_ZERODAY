"""
ET AI Concierge — Local Cross-Encoder Reranker
Uses BAAI/bge-reranker-base for zero-cost reranking.
"""
from typing import List, Dict, Any

try:
    from sentence_transformers import CrossEncoder
    reranker_model = CrossEncoder("BAAI/bge-reranker-base")
except ImportError:
    reranker_model = None


def rerank(
    query: str,
    documents: List[Dict[str, Any]],
    top_n: int = 3,
    text_key: str = "text",
) -> List[Dict[str, Any]]:
    """
    Rerank documents using a local cross-encoder.
    Falls back to original order if model is not available.
    """
    if reranker_model is None or not documents:
        return documents[:top_n]

    # Prepare pairs for the cross-encoder
    pairs = [(query, doc.get(text_key, "")) for doc in documents]

    # Get scores
    scores = reranker_model.predict(pairs)

    # Attach scores and sort
    for i, doc in enumerate(documents):
        doc["rerank_score"] = float(scores[i])

    documents.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

    return documents[:top_n]
