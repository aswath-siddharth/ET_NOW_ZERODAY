"""
ET AI Concierge — RAG Engine
Retrieval-Augmented Generation: hybrid search across PostgreSQL + Qdrant with reranking
"""
import json
import sys
import os
from typing import Dict, Any, List, Optional

try:
    import psycopg2
    import psycopg2.extras
    psycopg2.extras.register_uuid()
except ImportError:
    psycopg2 = None

try:
    from qdrant_client import QdrantClient
except ImportError:
    QdrantClient = None

try:
    # Import reranker from packages/rag/reranking/
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag", "reranking"))
    from reranker import rerank
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    print("⚠️ Reranker not available - using similarity-based ranking only")

from config import settings


# ─── Embedding ────────────────────────────────────────────────────────────────

_model = None
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def _get_model():
    """Lazy-load the sentence-transformers model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(EMBEDDING_MODEL)
            print(f"✅ RAG embedding model loaded: {EMBEDDING_MODEL}")
        except ImportError:
            print("⚠️ sentence-transformers not installed — RAG disabled")
    return _model


def embed_query(text: str) -> Optional[List[float]]:
    """Embed a single query text."""
    model = _get_model()
    if model is None:
        return None
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


# ─── Reranking ─────────────────────────────────────────────────────────────────

def _rerank_results(query: str, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """
    Optional reranking step: use cross-encoder to improve relevance.
    If reranker unavailable, returns results as-is (sorted by similarity).
    This improves ranking quality without extra infrastructure.
    """
    if not RERANKER_AVAILABLE or not results:
        return results[:top_k]
    
    try:
        # Rerank by relevance using cross-encoder
        reranked = rerank(
            query=query,
            documents=results,
            top_n=top_k,
            text_key="chunk_text"  # Use chunk_text as the document content field
        )
        print(f"✅ Reranked {len(results)} results → top {len(reranked)} by relevance")
        return reranked
    except Exception as e:
        print(f"⚠️ Reranking failed: {e}, returning original ranking")
        return results[:top_k]


# ─── Retrieval ────────────────────────────────────────────────────────────────

def retrieve_from_qdrant(query_embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Search Qdrant vector database for et_news_articles collection.
    Returns list of documents with metadata and similarity scores.
    """
    if QdrantClient is None:
        return []
    
    try:
        client = QdrantClient(
            url=settings.get("QDRANT_URL", "http://localhost:6333"),
            api_key=settings.get("QDRANT_API_KEY"),
            timeout=10
        )
        
        # Search the et_news_articles collection
        search_result = client.search(
            collection_name="et_news_articles",
            query_vector=query_embedding,
            limit=top_k,
            score_threshold=0.5  # Only return results with similarity > 0.5
        )
        
        documents = []
        for point in search_result:
            doc = {
                "id": point.id,
                "chunk_text": point.payload.get("text", ""),
                "metadata": point.payload,
                "similarity": point.score,
                "source": "qdrant",
                "title": point.payload.get("title", ""),
                "source_url": point.payload.get("source_url", ""),
                "tags": point.payload.get("tags", [])
            }
            documents.append(doc)
        
        return documents
    except Exception as e:
        print(f"⚠️ Qdrant search failed: {e}")
        return []


def retrieve(query: str, top_k: int = 3, category: str = None) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval: search both PostgreSQL (pgvector) and Qdrant.
    Embed the query and perform cosine similarity search in both databases.
    Returns top-k most relevant chunks merged and ranked by similarity.
    """
    query_embedding = embed_query(query)
    if query_embedding is None:
        return []

    pg_results = []
    if psycopg2:
        try:
            conn = psycopg2.connect(settings.DATABASE_URL)
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if category:
                    cur.execute("""
                        SELECT
                            id, article_id, title, category, chunk_text,
                            chunk_index, source_url, tags, paywall,
                            1 - (embedding <=> %s::vector) AS similarity
                        FROM knowledge_base
                        WHERE category = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (str(query_embedding), category, str(query_embedding), top_k))
                else:
                    cur.execute("""
                        SELECT
                            id, article_id, title, category, chunk_text,
                            chunk_index, source_url, tags, paywall,
                            1 - (embedding <=> %s::vector) AS similarity
                        FROM knowledge_base
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s
                    """, (str(query_embedding), str(query_embedding), top_k))

                pg_results = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            print(f"⚠️ PostgreSQL RAG retrieval error: {e}")

    # Query Qdrant vector database
    qdrant_results = retrieve_from_qdrant(query_embedding, top_k=top_k)

    # Merge results: de-duplicate by content and rank by similarity
    merged = {}
    for doc in pg_results:
        key = doc.get("chunk_text", "")[:100]  # Use first 100 chars as dedup key
        if key not in merged:
            merged[key] = doc

    for doc in qdrant_results:
        key = doc.get("chunk_text", "")[:100]
        if key not in merged:
            merged[key] = doc

    # Sort by similarity as baseline
    similarity_ranked = sorted(merged.values(), key=lambda x: x.get("similarity", 0), reverse=True)
    
    # Optional reranking: improve relevance using cross-encoder
    final_results = _rerank_results(query, similarity_ranked, top_k)
    
    return final_results


# ─── Persona-Aware Generation ─────────────────────────────────────────────────

PERSONA_TONE_MAP = {
    "PERSONA_YOUNG_PROFESSIONAL": (
        "The user is a young professional (20s-30s) building wealth. "
        "Be energetic, use relatable examples, explain financial jargon simply. "
        "Use analogies they'd understand (like comparing SIPs to a Netflix subscription). "
        "Encourage them without being patronizing."
    ),
    "PERSONA_ACTIVE_TRADER": (
        "The user is an active trader who understands markets well. "
        "Be precise, data-heavy, and include specific numbers, levels, and ratios. "
        "Skip basic explanations — they know terminology. "
        "Mention technical indicators, entry/exit levels, and risk-reward ratios."
    ),
    "PERSONA_CONSERVATIVE_SAVER": (
        "The user prioritizes safety and capital preservation. "
        "Emphasize guaranteed returns, government-backed instruments, and low risk. "
        "Be reassuring and avoid aggressive growth language. "
        "Focus on FDs, PPF, SGBs, and insurance."
    ),
    "PERSONA_CORPORATE_EXECUTIVE": (
        "The user is an established professional (40s-50s) managing significant assets. "
        "Be sophisticated, discuss portfolio-level strategy, tax optimization, and estate planning. "
        "Mention premium products like PMS, AIF, and NPS Tier 1."
    ),
    "PERSONA_HOME_BUYER": (
        "The user is focused on buying a home or real estate investment. "
        "Prioritize home loan comparisons, EMI calculations, property market trends. "
        "Discuss PMAY benefits, stamp duty, registration, and tax benefits under Section 24."
    ),
}


def _build_rag_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    persona: str = None,
) -> List[Dict[str, str]]:
    """Build the LLM prompt with retrieved context and persona instructions."""

    # Compile context
    context_parts = []
    sources = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Source {i}: {chunk['title']}]\n{chunk['chunk_text']}"
        )
        if chunk.get("source_url"):
            sources.append(f"- [{chunk['title']}]({chunk['source_url']})")

    context_text = "\n\n".join(context_parts)
    sources_text = "\n".join(sources) if sources else "No sources available."

    # Persona instruction
    persona_instruction = PERSONA_TONE_MAP.get(
        persona, "Adapt your tone to be helpful and conversational."
    )

    system_prompt = f"""You are the ET AI Concierge — a Financial Life Navigator for The Economic Times ecosystem.

## Your Role:
Follow this strictly tiered prompting logic when answering the user's question:

1. **Primary**: Answer the question using ONLY the provided Knowledge Base chunks, tailoring the tone to the user's specific profile. Cite specific data points and numbers from the context.
2. **Fallback**: If the exact answer is NOT in the retrieved chunks, use your general financial knowledge to answer.
3. **Transparency Mandate**: If you use general knowledge because the answer was not in the chunks, you MUST begin your response with this exact disclaimer: "I couldn't find a specific Economic Times article on this exact query, but generally speaking..."

## Persona & Tone:
{persona_instruction}

## Rules:
- Be conversational, not corporate. No bullet-point dumps unless the user asks for a comparison.
- End with a relevant follow-up question or actionable next step.
- Keep your response under 300 words unless the question requires detailed comparison.

## Retrieved Context:
{context_text}

## Sources:
{sources_text}"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]


def generate_answer(
    query: str,
    chunks: List[Dict[str, Any]],
    persona: str = None,
) -> Dict[str, Any]:
    """
    Generate a persona-aware answer using retrieved chunks and LLM.
    Returns dict with 'answer', 'sources', and 'chunks_used'.
    """
    if not chunks:
        return {
            "answer": "I couldn't find relevant information in our knowledge base for your question. Could you try rephrasing or asking about a specific financial topic like SIPs, tax saving, home loans, or market analysis?",
            "sources": [],
            "chunks_used": 0,
        }

    messages = _build_rag_prompt(query, chunks, persona)
    sources = [
        {"title": c["title"], "url": c.get("source_url", ""), "paywall": c.get("paywall", False)}
        for c in chunks
    ]

    # Try OpenRouter LLM (Primary)
    if settings.OPENROUTER_API_KEY:
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://et-ai-concierge.local",
                "X-Title": "ET AI Concierge",
            }
            payload = {
                "model": settings.OPENROUTER_MODEL,
                "messages": messages,
                "temperature": 0.5,
                "max_tokens": 2048,
                "reasoning": {"enabled": True}
            }
            response = requests.post(settings.OPENROUTER_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 405:
                print(f"[WARN] OpenRouter 405 error - trying Groq...")
            else:
                response.raise_for_status()
                return {
                    "answer": response.json()["choices"][0]["message"]["content"],
                    "sources": sources,
                    "chunks_used": len(chunks),
                }
        except Exception as e:
            print(f"[WARN] OpenRouter RAG generation failed: {e}, trying Groq...")

    # Fallback to Groq LLM
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.5,
                max_tokens=800,
            )
            return {
                "answer": response.choices[0].message.content,
                "sources": sources,
                "chunks_used": len(chunks),
            }
        except Exception as e:
            print(f"[WARN] Groq RAG generation failed: {e}")

    # Fallback: return raw chunks as formatted text
    fallback_parts = ["Based on our knowledge base, here's what I found:\n"]
    for i, chunk in enumerate(chunks, 1):
        fallback_parts.append(f"**{chunk['title']}**\n{chunk['chunk_text'][:300]}...\n")
    fallback_parts.append("\n*For a more detailed, personalized answer, please configure either OpenRouter API key or Groq API key.*")

    return {
        "answer": "\n".join(fallback_parts),
        "sources": sources,
        "chunks_used": len(chunks),
    }


# ─── Convenience Function ─────────────────────────────────────────────────────

def ask(query: str, persona: str = None, top_k: int = 3) -> Dict[str, Any]:
    """
    End-to-end RAG: query → retrieve → generate.
    This is the main entry point for the RAG engine.
    """
    chunks = retrieve(query, top_k=top_k)
    return generate_answer(query, chunks, persona)
