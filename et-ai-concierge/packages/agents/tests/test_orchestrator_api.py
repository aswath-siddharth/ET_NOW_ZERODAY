"""
Integration tests for FastAPI Orchestrator Endpoints (orchestrator.py).
Tests authentication gates, health checks, onboarding flows, chat endpoints,
streaming SSE, session resume, and admin endpoints.
"""
import pytest
import uuid
from starlette.testclient import TestClient
from jose import jwt
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import settings
from orchestrator import app, _get_profile
from state import UserProfile, PersonaType


@pytest.fixture(autouse=True)
def setup_test_env():
    settings.AUTH_SECRET = "orchestrator_test_secret_key_12345"
    yield


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(user_id="test_user_orch", email="orch@et.com"):
    token = jwt.encode(
        {"sub": user_id, "email": email, "name": "Orchestrator Tester"},
        settings.AUTH_SECRET,
        algorithm="HS256"
    )
    return {"Authorization": f"Bearer {token}"}


# ─── Public Endpoints ─────────────────────────────────────────────────────────

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "services" in data
    assert "timestamp" in data


def test_groq_status_endpoint(client):
    res = client.get("/api/groq-status")
    assert res.status_code == 200
    data = res.json()
    assert "available" in data
    assert "status" in data


def test_auth_register_and_verify_flow(client):
    unique_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    pwd = "securepassword123"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": pwd,
        "name": "Integration User"
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["email"] == unique_email
    assert reg_data["is_new"] is True

    # Duplicate register returns existing
    dup_res = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": pwd,
        "name": "Integration User Duplicate"
    })
    assert dup_res.status_code == 200
    assert dup_res.json()["is_new"] is False

    # Verify credentials with correct password
    verify_res = client.post("/api/auth/verify", json={
        "email": unique_email,
        "password": pwd
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["email"] == unique_email

    # Verify credentials with wrong password -> 401
    wrong_res = client.post("/api/auth/verify", json={
        "email": unique_email,
        "password": "wrong_password"
    })
    assert wrong_res.status_code == 401


# ─── Auth Gates (Unauthenticated 401) ─────────────────────────────────────────

@pytest.mark.parametrize("endpoint,method,body", [
    ("/api/profile", "GET", None),
    ("/api/dashboard/feed", "GET", None),
    ("/api/onboarding/start", "GET", None),
    ("/api/onboarding/answer", "POST", {"user_id": "u", "answer": "a", "step": 1}),
    ("/api/chat", "POST", {"message": "hello"}),
    ("/api/chat/stream", "POST", {"message": "hello"}),
    ("/api/chat/xray", "POST", {"message": "start"}),
    ("/api/chat/history", "GET", None),
    ("/api/session/resume", "GET", None),
    ("/api/track/paywall", "POST", None),
    ("/api/admin/scrape-now", "POST", None),
    ("/api/admin/scrape-status", "GET", None),
])
def test_endpoints_reject_unauthenticated(client, endpoint, method, body):
    if method == "GET":
        res = client.get(endpoint)
    else:
        res = client.post(endpoint, json=body or {})
    assert res.status_code == 401


# ─── Authenticated Workflows ──────────────────────────────────────────────────

def test_get_profile_authenticated(client):
    headers = auth_header("prof_user_1")
    res = client.get("/api/profile", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "id" in data
    assert "onboarding_complete" in data


def test_get_dashboard_feed_authenticated(client):
    headers = auth_header("dash_user_1")
    res = client.get("/api/dashboard/feed", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "persona" in data
    assert "market_overview" in data
    assert "recommended_insights" in data
    assert "primary_tools" in data


def test_onboarding_start_new_user(client):
    headers = auth_header(f"new_onboarding_{uuid.uuid4().hex[:6]}")
    res = client.get("/api/onboarding/start", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 0
    assert data["is_complete"] is False
    assert len(data["question"]) > 0


def test_onboarding_start_already_completed(client):
    uid = f"completed_user_{uuid.uuid4().hex[:6]}"
    headers = auth_header(uid)
    # Pre-set profile to complete
    profile = _get_profile(uid)
    profile.onboarding_complete = True
    profile.persona = PersonaType.YOUNG_PROFESSIONAL

    res = client.get("/api/onboarding/start", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_complete"] is True
    assert "complete" in data["question"].lower()


def test_onboarding_answer_progression(client):
    uid = f"answer_user_{uuid.uuid4().hex[:6]}"
    headers = auth_header(uid)

    # Start onboarding first
    client.get("/api/onboarding/start", headers=headers)

    # Answer step 0
    res = client.post("/api/onboarding/answer", headers=headers, json={
        "user_id": uid,
        "answer": "salaried",
        "step": 0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["step"] == 1
    assert data["is_complete"] is False


def test_chat_endpoint_routing_and_response(client):
    headers = auth_header(f"chat_user_{uuid.uuid4().hex[:6]}")
    res = client.post("/api/chat", headers=headers, json={
        "message": "What is the Nifty 50 price?",
        "modality": "web"
    })
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert len(data["message"]) > 0
    assert "session_id" in data
    assert "agent_used" in data


def test_chat_stream_endpoint(client):
    headers = auth_header(f"stream_user_{uuid.uuid4().hex[:6]}")
    res = client.post("/api/chat/stream", headers=headers, json={
        "message": "Tell me about ELSS funds",
        "modality": "web"
    })
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")
    assert "data:" in res.text


def test_chat_xray_empty_message_init(client):
    headers = auth_header(f"xray_user_{uuid.uuid4().hex[:6]}")
    res = client.post("/api/chat/xray", headers=headers, json={
        "message": ""
    })
    assert res.status_code == 200
    data = res.json()
    assert data["is_complete"] is False
    assert data["question_number"] == 0
    assert len(data["message"]) > 0


def test_chat_history_retrieval(client):
    uid = f"hist_user_{uuid.uuid4().hex[:6]}"
    headers = auth_header(uid)

    # Send a chat message first
    client.post("/api/chat", headers=headers, json={"message": "First message"})

    # Fetch history
    res = client.get("/api/chat/history?limit=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "messages" in data
    assert data["count"] >= 1


def test_session_resume_new(client):
    uid = f"resume_user_{uuid.uuid4().hex[:6]}"
    headers = auth_header(uid)

    res = client.get("/api/session/resume?modality=web", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data.get("is_new_session") is True or "transition_message" in data


def test_track_paywall_endpoint(client):
    headers = auth_header(f"paywall_user_{uuid.uuid4().hex[:6]}")
    res = client.post("/api/track/paywall", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "triggered" in data
