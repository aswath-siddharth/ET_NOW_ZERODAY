import json
from enum import Enum
from typing import Dict, Any

class PersonaType(str, Enum):
    CONSERVATIVE_SAVER = "PERSONA_CONSERVATIVE_SAVER"
    ACTIVE_TRADER = "PERSONA_ACTIVE_TRADER"
    YOUNG_PROFESSIONAL = "PERSONA_YOUNG_PROFESSIONAL"
    CORPORATE_EXECUTIVE = "PERSONA_CORPORATE_EXECUTIVE"
    HOME_BUYER = "PERSONA_HOME_BUYER"

PERSONA_MAPPING: Dict[PersonaType, Dict[str, Any]] = {
    PersonaType.CONSERVATIVE_SAVER: {
        "primary_tools": ["ET Wealth Edition", "NPS Calculator", "FD Rate Tracker"],
        "et_prime_sections": ["Personal Finance", "Tax Saving"],
        "masterclass": None,
        "marketplace_products": ["Fixed Deposits", "NPS", "Health Insurance"]
    },
    PersonaType.ACTIVE_TRADER: {
        "primary_tools": ["Alpha Trades", "Stock Reports Plus", "Candlestick Screener", "RSI Screener"],
        "et_prime_sections": ["Markets", "Tech", "Corporate Governance"],
        "masterclass": "Technical Analysis Masterclass",
        "marketplace_products": ["Demat Account", "Margin Loans"]
    },
    PersonaType.YOUNG_PROFESSIONAL: {
        "primary_tools": ["ET Wealth SIP Guide", "Young Mind Program", "AI for Business Leaders"],
        "et_prime_sections": ["Startups", "Tech", "Career"],
        "masterclass": "Young Mind Entrepreneurship Program",
        "marketplace_products": ["SIP platforms", "Term Insurance", "Credit Card"]
    },
    PersonaType.CORPORATE_EXECUTIVE: {
        "primary_tools": ["ET Prime", "Wealth Edition", "Today's ePaper"],
        "et_prime_sections": ["Corporate Governance", "Aviation", "Auto", "Pharma"],
        "masterclass": "Strategic Leadership Masterclass",
        "marketplace_products": ["Premium Credit Cards", "Portfolio Management Services"]
    },
    PersonaType.HOME_BUYER: {
        "primary_tools": ["Home Loan EMI Calculator", "Loan Marketplace", "RBI Rate Tracker"],
        "et_prime_sections": ["Real Estate", "Digital Real Estate", "Infrastructure"],
        "masterclass": "Build Passive Income with Mutual Funds",
        "marketplace_products": ["Home Loans (SBI, HDFC, Kotak)", "Home Insurance"]
    }
}

def determine_persona(user_profile: Dict[str, Any]) -> PersonaType:
    # Example parsing logic for mapping profiling questions to persona
    # This will be replaced by the LLM routing logic 
    pass
