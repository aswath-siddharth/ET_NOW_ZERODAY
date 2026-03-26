"""
ET AI Concierge — RAG Engine
Retrieval-Augmented Generation: embed query → pgvector search → persona-aware LLM generation.
"""
import json
from typing import Dict, Any, List, Optional

try:
    import psycopg2
    import psycopg2.extras
    psycopg2.extras.register_uuid()
except ImportError:
    psycopg2 = None

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


# ─── Retrieval ────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = 3, category: str = None) -> List[Dict[str, Any]]:
    """
    Embed the query and perform cosine similarity search in pgvector.
    Returns top-k most relevant chunks with metadata.
    """
    query_embedding = embed_query(query)
    if query_embedding is None:
        return []

    if not psycopg2:
        return []

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

            results = cur.fetchall()
        conn.close()

        return [dict(r) for r in results]

    except Exception as e:
        print(f"⚠️ RAG retrieval error: {e}")
        return []


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
