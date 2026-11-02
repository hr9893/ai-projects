import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def get_auth_headers(username: str, password: str = "password123"):
    response = client.post("/api/auth/token", data={"username": username, "password": password})
    assert response.status_code == 200, f"Login failed for {username}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_successful_login():
    response = client.post("/api/auth/token", data={"username": "doc_john", "password": "password123"})
    assert response.status_code == 200

def test_doctor_vector_access():
    headers = get_auth_headers("doc_john")
    assert client.get("/api/retrieval/vector/clinical", headers=headers).status_code == 200
    assert client.get("/api/retrieval/vector/billing", headers=headers).status_code == 403

def test_doctor_sql_access():
    headers = get_auth_headers("doc_john")
    assert client.get("/api/retrieval/sql/claims", headers=headers).status_code == 200
    assert client.get("/api/retrieval/sql/maintenance_tickets", headers=headers).status_code == 403