from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_style_me_empty_prompt():
    response = client.post("/api/v1/style-me", json={"prompt": ""})
    assert response.status_code == 400
