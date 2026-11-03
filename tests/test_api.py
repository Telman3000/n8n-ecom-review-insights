"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from service.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "llm_available" in data
    assert "mode" in data
    assert data["mode"] in ["llm", "fallback"]


def test_analyze_endpoint_single_review(client):
    """Test analysis endpoint with a single review."""
    payload = {
        "reviews": [
            {
                "id": "test1",
                "text": "Отличный товар! Качество супер, доставка быстрая.",
                "rating": 5,
            }
        ]
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "summary" in data
    assert len(data["results"]) == 1

    result = data["results"][0]
    assert result["id"] == "test1"
    assert result["sentiment"] in ["positive", "neutral", "negative"]
    assert isinstance(result["topics"], list)
    assert isinstance(result["complaints"], list)
    assert result["priority"] in ["low", "medium", "high", "critical"]


def test_analyze_endpoint_multiple_reviews(client):
    """Test analysis endpoint with multiple reviews."""
    payload = {
        "reviews": [
            {"id": "1", "text": "Отличный товар!", "rating": 5},
            {"id": "2", "text": "Ужасное качество!", "rating": 1},
            {"id": "3", "text": "Нормально, ничего особенного.", "rating": 3},
        ]
    }

    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) == 3

    summary = data["summary"]
    assert summary["total_reviews"] == 3
    assert "sentiment_distribution" in summary
    assert "priority_distribution" in summary
    assert "top_topics" in summary
    assert "top_complaints" in summary


def test_analyze_endpoint_validation_empty_reviews(client):
    """Test validation for empty reviews list."""
    payload = {"reviews": []}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422  # Validation error


def test_analyze_endpoint_validation_missing_id(client):
    """Test validation for review without id."""
    payload = {"reviews": [{"text": "Отличный товар!"}]}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_endpoint_validation_missing_text(client):
    """Test validation for review without text."""
    payload = {"reviews": [{"id": "1", "rating": 5}]}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_endpoint_validation_invalid_rating(client):
    """Test validation for invalid rating."""
    payload = {"reviews": [{"id": "1", "text": "Test", "rating": 6}]}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422


def test_analyze_endpoint_without_rating(client):
    """Test analysis works without rating."""
    payload = {"reviews": [{"id": "1", "text": "Отличный товар!"}]}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert len(data["results"]) == 1


def test_openapi_schema(client):
    """Test that OpenAPI schema is accessible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    assert "info" in schema
    assert "paths" in schema
    assert "/analyze" in schema["paths"]
    assert "/health" in schema["paths"]
