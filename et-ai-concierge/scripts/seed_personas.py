"""
ET AI Concierge — Seed Script: Seed Test User Profiles
Run: python scripts/seed_personas.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "packages", "agents"))

from database import init_db, create_user, update_user_profile


TEST_USERS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "persona": "PERSONA_CONSERVATIVE_SAVER",
        "risk_score": 3,
        "interests": ["Personal Finance", "Tax Saving"],
        "goals": ["saving"],
        "income_type": "salaried",
        "age_group": "50+",
        "has_emergency_fund": True,
        "home_ownership": "owning",
        "investment_horizon": "1-3 years",
        "is_active_trader": False,
        "primary_goal": "protecting",
        "onboarding_complete": True,
        "profile_completeness": 1.0,
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "persona": "PERSONA_ACTIVE_TRADER",
        "risk_score": 9,
        "interests": ["Markets", "Tech"],
        "goals": ["growing"],
        "income_type": "salaried",
        "age_group": "30s",
        "has_emergency_fund": True,
        "home_ownership": "renting",
        "investment_horizon": "1-3 years",
        "is_active_trader": True,
        "primary_goal": "growing",
        "onboarding_complete": True,
        "profile_completeness": 1.0,
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "persona": "PERSONA_YOUNG_PROFESSIONAL",
        "risk_score": 6,
        "interests": ["Startups", "Tech", "Career"],
        "goals": ["growing", "saving"],
        "income_type": "salaried",
        "age_group": "20s",
        "has_emergency_fund": False,
        "home_ownership": "renting",
        "investment_horizon": "10+ years",
        "is_active_trader": False,
        "primary_goal": "growing",
        "onboarding_complete": True,
        "profile_completeness": 1.0,
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "persona": "PERSONA_CORPORATE_EXECUTIVE",
        "risk_score": 6,
        "interests": ["Corporate Governance", "Aviation", "Pharma"],
        "goals": ["growing", "protecting"],
        "income_type": "salaried",
        "age_group": "40s",
        "has_emergency_fund": True,
        "home_ownership": "owning",
        "investment_horizon": "5-10 years",
        "is_active_trader": False,
        "primary_goal": "growing",
        "onboarding_complete": True,
        "profile_completeness": 1.0,
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "persona": "PERSONA_HOME_BUYER",
        "risk_score": 4,
        "interests": ["Real Estate", "Infrastructure"],
        "goals": ["buying"],
        "income_type": "salaried",
        "age_group": "30s",
        "has_emergency_fund": True,
        "home_ownership": "renting",
        "investment_horizon": "3-5 years",
        "is_active_trader": False,
        "primary_goal": "buying",
        "onboarding_complete": True,
        "profile_completeness": 1.0,
    },
]


if __name__ == "__main__":
    print("🚀 Initializing database and seeding test users...")
    init_db()

    for user in TEST_USERS:
        uid = user.pop("id")
        create_user(uid)
        update_user_profile(uid, user)
        print(f"  ✅ Created user {uid} — {user['persona']}")

    print(f"\n✅ Done! {len(TEST_USERS)} test users created.")
