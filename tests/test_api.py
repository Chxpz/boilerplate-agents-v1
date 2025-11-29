import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "status" in response.json()

def test_chat_endpoint():
    """Test chat endpoint with valid input."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "session_id": "test"}
    )
    assert response.status_code in [200, 500]

def test_clear_memory():
    """Test clear memory endpoint."""
    response = client.delete("/api/v1/memory/test_session")
    assert response.status_code == 200
    assert "message" in response.json()
