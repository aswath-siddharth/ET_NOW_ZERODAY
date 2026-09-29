"""
Unit tests for Behavioral Monitor Agent (behavioral_monitor.py).
Tests session tracking, paywall limits, learning-to-tool bridges,
career transitions, and tax search triggers.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from behavioral_monitor import (
    track_paywall_hit, track_page_view, track_time_on_page,
    track_query, run_behavioral_monitor, get_or_create_session,
)


def test_paywall_trigger_after_3_hits():
    user_id = "user_paywall_test_1"
    session = get_or_create_session(user_id)
    session.paywall_hits = 0

    track_paywall_hit(user_id)
    track_paywall_hit(user_id)
    assert run_behavioral_monitor(user_id, "") is None

    # Third hit triggers ET Prime offer
    track_paywall_hit(user_id)
    response = run_behavioral_monitor(user_id, "")
    assert response is not None
    assert "ET Prime" in response.content
    assert len(response.recommendations) > 0


def test_masterclass_no_tool_trigger():
    user_id = "user_masterclass_test_2"
    session = get_or_create_session(user_id)
    session.time_on_page = {}
    session.has_used = {}

    track_time_on_page(user_id, "technical-analysis-masterclass", 150)
    response = run_behavioral_monitor(user_id, "")
    assert response is not None
    assert "Candlestick Screener" in response.content


def test_career_transition_trigger():
    user_id = "user_career_test_3"
    session = get_or_create_session(user_id)
    session.recent_queries = []

    track_query(user_id, "educational loan")
    track_query(user_id, "investment")

    response = run_behavioral_monitor(user_id, "")
    assert response is not None
    assert "Psychology of Money" in response.content


def test_tax_search_intent_trigger():
    user_id = "user_tax_test_4"
    session = get_or_create_session(user_id)
    session.recent_queries = []

    track_query(user_id, "how to save tax under 80c")
    response = run_behavioral_monitor(user_id, "")
    assert response is not None
    assert "80C" in response.content or "NPS calculator" in response.content
