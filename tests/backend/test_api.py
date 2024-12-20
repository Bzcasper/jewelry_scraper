import pytest
from fastapi.testclient import TestClient
from api.app import app
import json

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def sample_search_payload():
    return {
        "query": "gold ring",
        "platform": "ebay",
        "max_items": 50,
        "filters": {
            "price_min": 100,
            "price_max": 1000,
            "category": "rings"
        }
    }

class TestAPI:
    def test_scrape_endpoint(self, client, sample_search_payload):
        response = client.post("/scrape", json=sample_search_payload)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_scrape_status(self, client):
        # First create a job
        response = client.post("/scrape", json={"query": "test"})
        job_id = response.json()["job_id"]
        
        # Check status
        response = client.get(f"/scrape/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data

    def test_get_products(self, client):
        response = client.get("/products")
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        assert "total" in data

    def test_get_products_with_filters(self, client):
        filters = {
            "platform": "ebay",
            "category": "rings",
            "price_min": 100,
            "price_max": 1000
        }
        response = client.get("/products", params=filters)
        assert response.status_code == 200
        data = response.json()
        assert "products" in data

    def test_system_status(self, client):
        response = client.get("/system/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_jobs" in data
        assert "database_size" in data