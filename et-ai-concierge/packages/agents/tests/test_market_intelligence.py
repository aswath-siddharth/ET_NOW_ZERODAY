"""
Unit tests for Market Intelligence Agent (market_intelligence_agent.py).
Tests portfolio drift calculations, threshold boundaries, stock quoting,
gold price fetching, and market response generation.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import UserProfile, AgentResponse
from market_intelligence_agent import (
    calculate_portfolio_drift, get_real_time_quote,
    get_indian_gold_price, run_market_intelligence_agent,
)


def test_calculate_portfolio_drift_no_rebalance_needed():
    current = {"equity": 0.61, "debt": 0.30, "gold": 0.09}
    target = {"equity": 0.60, "debt": 0.30, "gold": 0.10}

    # Max drift is 0.01 (1%), which is <= 0.05
    drift = calculate_portfolio_drift(current, target, threshold=0.05)
    assert drift["requires_rebalance"] is False
    assert drift["max_drift_pct"] == 1.0


def test_calculate_portfolio_drift_rebalance_required():
    current = {"equity": 0.75, "debt": 0.20, "gold": 0.05}
    target = {"equity": 0.50, "debt": 0.40, "gold": 0.10}

    # Equity drift is 0.25 (25%), which exceeds 0.05
    drift = calculate_portfolio_drift(current, target, threshold=0.05)
    assert drift["requires_rebalance"] is True
    assert drift["max_drift_asset"] == "equity"
    assert drift["max_drift_pct"] == 25.0
    assert "rebalancing" in drift["message"].lower()
    assert "deeplink" in drift


def test_calculate_portfolio_drift_disjoint_assets():
    current = {"crypto": 0.10, "equity": 0.90}
    target = {"equity": 0.80, "debt": 0.20}

    drift = calculate_portfolio_drift(current, target, threshold=0.05)
    assert "crypto" in drift["drifts"]
    assert "debt" in drift["drifts"]
    assert drift["requires_rebalance"] is True


def test_get_indian_gold_price():
    gold = get_indian_gold_price()
    assert isinstance(gold, dict)
    assert "symbol" in gold


def test_get_real_time_quote_invalid_symbol():
    res = get_real_time_quote("TOTALLY_INVALID_SYMBOL_XYZ_999")
    assert isinstance(res, dict)
    assert "error" in res or "status" in res


def test_run_market_intelligence_agent_basic():
    profile = UserProfile(persona="PERSONA_ACTIVE_TRADER", risk_score=8)
    response = run_market_intelligence_agent("What is the Nifty 50 doing today?", profile)
    assert isinstance(response, AgentResponse)
    assert response.agent_id == "market_intelligence_agent"
    assert len(response.content) > 0
