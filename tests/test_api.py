"""
Tests for the LlamaSearch AI API.
"""

from fastapi.testclient import TestClient
from llamasearchai.api.app import app, get_api_key
from llamasearchai.config.settings import settings


# Override API key dependency for testing
def get_test_api_key():
    return "test-api-key"


app.dependency_overrides[get_api_key] = get_test_api_key
client = TestClient(app)


def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "uptime" in data


def test_validate_api_key():
    """Test API key validation."""
    # Valid API key
    response = client.get(
        "/api/v1/validate",
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True

    # Invalid API key
    response = client.get(
        "/api/v1/validate",
        headers={settings.API_KEY_HEADER: "invalid-key"},
    )
    assert response.status_code == 401


def test_search_endpoint():
    """Test the search endpoint."""
    search_request = {
        "query": {
            "text": "python fastapi tutorial",
            "intent": "informational",
            "language": "en",
        },
        "num_results": 5,
        "providers": ["google", "bing"],
    }

    response = client.post(
        "/api/v1/search/",
        json=search_request,
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= search_request["num_results"]
    assert "metadata" in data
    assert "query" in data
    assert data["query"]["text"] == search_request["query"]["text"]


def test_analyze_query():
    """Test the query analysis endpoint."""
    query = "python fastapi tutorial"

    response = client.get(
        f"/api/v1/search/analyze?query={query}",
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == query
    assert "intent" in data
    assert "locality" in data
    assert "language" in data


def test_embed_endpoint():
    """Test the embedding endpoint."""
    embed_request = {
        "text": ["Python is a programming language", "FastAPI is a web framework"],
        "model": "text-embedding-ada-002",
        "normalize": True,
    }

    response = client.post(
        "/api/v1/vector/embed",
        json=embed_request,
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "embeddings" in data
    assert len(data["embeddings"]) == len(embed_request["text"])
    assert "metadata" in data
    assert data["metadata"]["model"] == embed_request["model"]

    # Check each embedding
    for i, embedding in enumerate(data["embeddings"]):
        assert "vector" in embedding
        assert "dimensions" in embedding
        assert embedding["text"] == embed_request["text"][i]
        assert embedding["model"] == embed_request["model"]
        assert len(embedding["vector"]) == embedding["dimensions"]


def test_vector_search():
    """Test the vector search endpoint."""
    search_request = {
        "query": "Python programming",
        "collection": "test_collection",
        "num_results": 5,
    }

    response = client.post(
        "/api/v1/vector/search",
        json=search_request,
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) <= search_request["num_results"]
    assert "metadata" in data
    assert data["metadata"]["collection"] == search_request["collection"]


def test_user_profile():
    """Test user profile endpoints."""
    user_id = "test_user"

    # Get profile
    response = client.get(
        f"/api/v1/personalization/profile/{user_id}",
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    profile = response.json()
    assert profile["user_id"] == user_id
    assert "preferences" in profile
    assert "topics_of_interest" in profile

    # Update profile
    profile["topics_of_interest"].append("testing")

    response = client.put(
        f"/api/v1/personalization/profile/{user_id}",
        json=profile,
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    updated_profile = response.json()
    assert "testing" in updated_profile["topics_of_interest"]


def test_personalization():
    """Test personalization endpoint."""
    personalization_request = {
        "user_id": "test_user",
        "content": [
            {
                "id": "result1",
                "title": "Python Tutorial",
                "url": "https://example.com/python",
                "score": 0.95,
            },
            {
                "id": "result2",
                "title": "FastAPI Documentation",
                "url": "https://example.com/fastapi",
                "score": 0.90,
            },
        ],
        "context": {"query": "python tutorial"},
    }

    response = client.post(
        "/api/v1/personalization/rerank",
        json=personalization_request,
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "content" in data
    assert len(data["results"]) == len(personalization_request["content"])
    assert len(data["content"]) == len(personalization_request["content"])
    assert "metadata" in data


def test_user_feedback():
    """Test user feedback endpoint."""
    feedback_request = {
        "user_id": "test_user",
        "item_id": "result1",
        "rating": 4.5,
        "feedback_text": "Very helpful tutorial",
        "source": "search",
        "context": {"query": "python tutorial"},
    }

    response = client.post(
        "/api/v1/personalization/feedback",
        json=feedback_request,
        headers={settings.API_KEY_HEADER: "test-api-key"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "feedback_id" in data
    assert "metadata" in data
