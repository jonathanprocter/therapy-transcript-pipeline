import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("API_KEY", "testkey")

from app import app, db

with app.app_context():
    db.create_all()


def test_create_client():
    client = app.test_client()
    resp = client.post(
        "/api/clients",
        json={"name": "Test Client"},
        headers={"X-API-KEY": "testkey"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["client_id"]


def test_authentication_required():
    client = app.test_client()
    resp = client.get("/api/processing-logs")
    assert resp.status_code == 401
