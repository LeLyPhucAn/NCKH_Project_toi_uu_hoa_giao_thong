import sys
import os
from fastapi.testclient import TestClient
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src"))

from server import app

client = TestClient(app)


def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Operational"
    assert "Modular Monolith" in data["architecture"]


def test_api_get_hubs():
    response = client.get("/api/hubs")
    assert response.status_code == 200
    hubs = response.json()
    assert isinstance(hubs, list)


def test_api_get_kpis():
    response = client.get("/api/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
