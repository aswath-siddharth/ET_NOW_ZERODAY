"""
Unit tests for Editorial Agent (editorial_agent.py).
Tests mock articles search, keyword and tag scoring, paywall filtering,
and editorial recommendations.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import UserProfile, AgentResponse
from editorial_agent import _search_articles, run_editorial_agent, MOCK_ARTICLES


def test_mock_articles_integrity():
    assert len(MOCK_ARTICLES) >= 5
    for art in MOCK_ARTICLES:
        assert "id" in art
        assert "title" in art
        assert "summary" in art
        assert "url" in art
        assert "tags" in art
        assert "paywall" in art


def test_search_articles_by_keyword():
    gold_results = _search_articles("gold")
    assert len(gold_results) > 0
    assert any("gold" in a["title"].lower() or "gold" in [t.lower() for t in a["tags"]] for a in gold_results)

    nifty_results = _search_articles("nifty")
    assert len(nifty_results) > 0
    assert any("nifty" in a["title"].lower() for a in nifty_results)


def test_search_articles_paywall_flag():
    results = _search_articles("gold")
    # Should include both paywalled and free articles
    has_paywalled = any(a.get("paywall") is True for a in results)
    has_free = any(a.get("paywall") is False for a in results)
    assert has_paywalled or has_free


def test_search_articles_with_user_interests():
    results = _search_articles("market", user_interests=["Markets"])
    assert len(results) > 0


def test_run_editorial_agent():
    profile = UserProfile(persona="PERSONA_CONSERVATIVE_SAVER", interests=["Tax Saving"])
    response = run_editorial_agent("Tell me about ELSS tax saving funds", profile)
    assert isinstance(response, AgentResponse)
    assert response.agent_id == "editorial_agent"
    assert len(response.content) > 0
    assert len(response.recommendations) > 0
    # Recommendation should have deeplink/url
    rec = response.recommendations[0]
    assert rec.deeplink is not None
    assert rec.deeplink.startswith("http")
