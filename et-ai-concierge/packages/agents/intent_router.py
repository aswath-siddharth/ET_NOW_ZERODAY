"""
ET AI Concierge — Intent Router (Agent 1 for Phase 3)
Detects cross-sell and upsell opportunities using fast keyword detection and in-memory embedding similarity.
No external LLM fallback: runs 100% locally in milliseconds.
"""
from typing import Dict, Any, List, Optional
import numpy as np
from state import UserProfile
from config import settings

# ─── Fast Semantic Anchors ───────────────────────────────────────────────────

TAX_ANCHORS = [
    "How can I save tax under section 80C?",
    "Best tax saving investments and ELSS mutual funds",
    "How to reduce income tax deductions and tax planning",
    "Tax saving fixed deposits and NPS tax benefits",
    "Which mutual funds help me save taxes on my salary?",
]

INSURANCE_ANCHORS = [
    "I want to buy life insurance or term plan",
    "Health insurance policy mediclaim coverage for family",
    "Best insurance protection and critical illness cover",
    "Should I get term insurance or health insurance?",
    "Family health protection and life insurance policy",
]

_tax_embeddings: Optional[np.ndarray] = None
_insurance_embeddings: Optional[np.ndarray] = None


def _get_anchor_embeddings():
    """Lazily compute and cache anchor embeddings once in memory."""
    global _tax_embeddings, _insurance_embeddings
    if _tax_embeddings is None or _insurance_embeddings is None:
        try:
            from rag_engine import embed_query
            tax_vectors = [embed_query(a) for a in TAX_ANCHORS]
            ins_vectors = [embed_query(a) for a in INSURANCE_ANCHORS]
            _tax_embeddings = np.array([v for v in tax_vectors if v is not None])
            _insurance_embeddings = np.array([v for v in ins_vectors if v is not None])
        except Exception as e:
            print(f"[WARN] Failed to compute anchor embeddings: {e}")
            _tax_embeddings = np.array([])
            _insurance_embeddings = np.array([])
    return _tax_embeddings, _insurance_embeddings


def detect_upsell_intent(query: str, profile: UserProfile) -> Dict[str, Any]:
    """
    Evaluates the user's query and profile to detect monetization intent.
    Uses ultra-fast keyword matching (Tier 1) followed by in-memory embedding similarity (Tier 2).
    Runs in < 10ms with zero external LLM calls.
    Returns: {"trigger_active": bool, "trigger_type": str or None}
    """
    fallback_response = {"trigger_active": False, "trigger_type": None}
    query_lower = query.lower()

    # ──── TIER 1: FAST KEYWORD MATCHING (< 0.1ms) ─────────────────────────────
    tax_keywords = [
        "80c", "section 80c", "elss", "tax sav", "tax invest", "tax deduct",
        "tax-sav", "tax-invest", "tax benefit", "fy deduct", "save tax", "save taxes"
    ]
    if any(kw in query_lower for kw in tax_keywords) and not profile.has_tax_investments:
        print(f"[OK] Keyword match: tax_marketplace detected")
        return {"trigger_active": True, "trigger_type": "tax_marketplace"}

    insurance_keywords = [
        "life insur", "health insur", "term plan", "insur cover", "insur plan",
        "protect", "health cover", "mediclaim", "term insur"
    ]
    if any(kw in query_lower for kw in insurance_keywords) and not profile.has_insurance:
        print(f"[OK] Keyword match: insurance_marketplace detected")
        return {"trigger_active": True, "trigger_type": "insurance_marketplace"}

    # ──── TIER 2: IN-MEMORY EMBEDDING SIMILARITY (~5ms) ───────────────────────
    try:
        from rag_engine import embed_query
        query_vec = embed_query(query)
        if query_vec is not None:
            qv = np.array(query_vec)
            tax_vecs, ins_vecs = _get_anchor_embeddings()

            tax_sim = float(np.max(np.dot(tax_vecs, qv))) if len(tax_vecs) > 0 else 0.0
            ins_sim = float(np.max(np.dot(ins_vecs, qv))) if len(ins_vecs) > 0 else 0.0

            SEMANTIC_THRESHOLD = 0.50

            if tax_sim >= SEMANTIC_THRESHOLD and tax_sim > ins_sim and not profile.has_tax_investments:
                print(f"[OK] Semantic match (sim={tax_sim:.2f}): tax_marketplace detected")
                return {"trigger_active": True, "trigger_type": "tax_marketplace"}

            if ins_sim >= SEMANTIC_THRESHOLD and ins_sim > tax_sim and not profile.has_insurance:
                print(f"[OK] Semantic match (sim={ins_sim:.2f}): insurance_marketplace detected")
                return {"trigger_active": True, "trigger_type": "insurance_marketplace"}

    except Exception as e:
        print(f"[WARN] In-memory semantic intent check failed: {e}")

    return fallback_response
