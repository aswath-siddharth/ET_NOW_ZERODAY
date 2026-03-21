import os
from dotenv import load_dotenv

load_dotenv()

from profiling_agent import run_xray_step, extract_xray_profile, map_xray_to_persona

# Mocking the 5-question conversation history based on user's exact responses
conversation_history = [
    {"role": "assistant", "content": "What is your primary source of income?"},
    {"role": "user", "content": "business owner"},
    {"role": "assistant", "content": "Which decade of life are you in?"},
    {"role": "user", "content": "50+"},
    {"role": "assistant", "content": "What is your risk tolerance?"},
    {"role": "user", "content": "7"},
    {"role": "assistant", "content": "What sectors interest you most?"},
    {"role": "user", "content": "Tech"},
    {"role": "assistant", "content": "What is your primary financial goal?"},
    {"role": "user", "content": "protecting assets"}
]

print("Running X-Ray LLM Generation...")
response = run_xray_step(conversation_history, 5)
print("\n--- LLM RAW RESPONSE ---")
print(response)

print("\n--- EXTRACTED PROFILE ---")
extracted = extract_xray_profile(response)
print(extracted)

from config import settings
print("Groq Key length:", len(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else "None")
print("Ollama model:", settings.OLLAMA_MODEL)
print("\n--- FINAL PERSONA MAPPING ---")
if extracted:
    persona = map_xray_to_persona(extracted)
    print("Mapped to:", persona)
else:
    print("Failed to extract JSON.")

