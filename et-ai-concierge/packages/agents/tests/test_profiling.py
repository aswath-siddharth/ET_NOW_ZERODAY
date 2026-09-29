"""
Unit tests for Profiling Agent and Persona logic (profiling_agent.py).
Tests 5 financial personas, question flows, profile completeness,
boundary values, and persona tools mapping.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from state import PersonaType
from profiling_agent import (
    determine_persona, calculate_profile_completeness,
    get_onboarding_step, process_onboarding_answer,
    PROFILING_QUESTIONS, PERSONA_MAPPING,
)


def test_persona_mapping_structure():
    """Verify all 5 personas have mapped primary tools, sections, and products."""
    for persona in PersonaType:
        assert persona in PERSONA_MAPPING, f"Missing mapping for {persona}"
        mapping = PERSONA_MAPPING[persona]
        assert "primary_tools" in mapping
        assert len(mapping["primary_tools"]) > 0
        assert "et_prime_sections" in mapping
        assert "marketplace_products" in mapping


def test_determine_persona_home_buyer():
    answers = {"primary_goal": "buying", "home_ownership": "renting", "risk_score": 4}
    assert determine_persona(answers) == PersonaType.HOME_BUYER


def test_determine_persona_active_trader():
    # Active trader via trader flag
    answers = {"is_active_trader": "active trader", "risk_score": 5}
    assert determine_persona(answers) == PersonaType.ACTIVE_TRADER

    # Active trader via high risk score
    answers_risk = {"is_active_trader": "no", "risk_score": 9}
    assert determine_persona(answers_risk) == PersonaType.ACTIVE_TRADER


def test_determine_persona_young_professional():
    answers = {"age_group": "20s", "risk_score": 6, "primary_goal": "growing"}
    assert determine_persona(answers) == PersonaType.YOUNG_PROFESSIONAL

    answers_30s = {"age_group": "30s", "risk_score": 5, "primary_goal": "growing"}
    assert determine_persona(answers_30s) == PersonaType.YOUNG_PROFESSIONAL


def test_determine_persona_corporate_executive():
    answers = {"age_group": "40s", "risk_score": 6, "primary_goal": "growing"}
    assert determine_persona(answers) == PersonaType.CORPORATE_EXECUTIVE

    answers_50 = {"age_group": "50+", "risk_score": 7, "primary_goal": "growing"}
    assert determine_persona(answers_50) == PersonaType.CORPORATE_EXECUTIVE


def test_determine_persona_conservative_saver_default():
    answers = {"risk_score": 2, "age_group": "20s", "primary_goal": "saving"}
    assert determine_persona(answers) == PersonaType.CONSERVATIVE_SAVER

    empty_answers = {}
    assert determine_persona(empty_answers) == PersonaType.CONSERVATIVE_SAVER


def test_determine_persona_string_risk_score():
    answers = {"risk_score": "8", "age_group": "30s"}
    assert determine_persona(answers) == PersonaType.ACTIVE_TRADER

    answers_invalid = {"risk_score": "not_a_number", "age_group": "20s"}
    # Should fallback gracefully without throwing ValueError
    persona = determine_persona(answers_invalid)
    assert isinstance(persona, PersonaType)


def test_calculate_profile_completeness():
    assert calculate_profile_completeness({}) == 0.0

    all_answers = {q["key"]: "some_answer" for q in PROFILING_QUESTIONS}
    assert calculate_profile_completeness(all_answers) == 1.0

    half_answers = {PROFILING_QUESTIONS[0]["key"]: "ans", PROFILING_QUESTIONS[1]["key"]: "ans"}
    expected = 2 / len(PROFILING_QUESTIONS)
    assert abs(calculate_profile_completeness(half_answers) - expected) < 1e-4


def test_get_onboarding_step():
    # Step 0 is warm open
    step0 = get_onboarding_step(0)
    assert step0.step == 0
    assert step0.is_complete is False
    assert "Financial Navigator" in step0.question

    # Step 1 is first question
    step1 = get_onboarding_step(1)
    assert step1.step == 1
    assert step1.is_complete is False
    assert len(step1.options) > 0

    # Step 9 is last question
    step9 = get_onboarding_step(9)
    assert step9.step == 9
    assert step9.is_complete is False

    # Step 10 is completion
    step10 = get_onboarding_step(10)
    assert step10.is_complete is True


def test_process_onboarding_answer():
    answers = {}
    # Question 1: income_type
    answers = process_onboarding_answer(1, "salaried", answers)
    assert answers["income_type"] == "salaried"

    # Question 5: risk_score (should parse to int)
    answers = process_onboarding_answer(5, "7", answers)
    assert answers["risk_score"] == 7

    # Question 5 with invalid int fallback
    answers = process_onboarding_answer(5, "invalid", answers)
    assert answers["risk_score"] == 5
