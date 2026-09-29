"""
Unit tests for Compliance Wrapper (compliance_wrapper.py).
Tests SEBI investment disclaimers, audit logging, and HITL escalation triggers.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import UserProfile, AgentResponse
from compliance_wrapper import compliance_wrapper, SEBI_DISCLAIMER


def test_sebi_disclaimer_added_on_investment_advice():
    user = UserProfile()
    response = AgentResponse(
        agent_id="market_intelligence_agent",
        content="Buy TCS stock for strong quarterly dividend.",
        contains_investment_advice=True,
        confidence_score=0.85,
    )
    wrapped = compliance_wrapper.wrap(response, user, session_id="sess-1")
    assert SEBI_DISCLAIMER in wrapped.disclaimers
    assert "SEBI" in wrapped.content


def test_sebi_disclaimer_omitted_for_general_info():
    user = UserProfile()
    response = AgentResponse(
        agent_id="editorial_agent",
        content="Here is today's headline about GDP growth.",
        contains_investment_advice=False,
        confidence_score=0.90,
    )
    wrapped = compliance_wrapper.wrap(response, user, session_id="sess-2")
    assert SEBI_DISCLAIMER not in wrapped.disclaimers


def test_hitl_escalation_on_high_stakes():
    user = UserProfile()
    response = AgentResponse(
        agent_id="marketplace_agent",
        content="Proceeding with loan underwriting.",
        type="LOAN_APPLICATION",
        confidence_score=0.90,
    )
    wrapped = compliance_wrapper.wrap(response, user, session_id="sess-3")
    assert wrapped.type == "HITL_ESCALATION"
    assert "specialist review" in wrapped.content.lower()


def test_hitl_escalation_on_low_confidence():
    user = UserProfile()
    response = AgentResponse(
        agent_id="editorial_agent",
        content="Uncertain answer.",
        confidence_score=0.55,  # Below 0.70 threshold
    )
    wrapped = compliance_wrapper.wrap(response, user, session_id="sess-4")
    assert wrapped.type == "HITL_ESCALATION"
    assert "specialist review" in wrapped.content.lower()


def test_standard_response_no_escalation():
    user = UserProfile()
    response = AgentResponse(
        agent_id="editorial_agent",
        content="Standard news query answer.",
        type="general",
        confidence_score=0.88,
    )
    wrapped = compliance_wrapper.wrap(response, user, session_id="sess-5")
    assert wrapped.type == "general"
    assert "specialist review" not in wrapped.content.lower()
