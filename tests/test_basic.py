from fastapi.testclient import TestClient
from yfinance_api.api_server import app

client = TestClient(app)

def test_health_root_returns_200():
    resp = client.get("/")
    assert resp.status_code == 200
