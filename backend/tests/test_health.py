def test_root_health_check(client):
    """Test root /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "DemandIQ Backend"
    assert "version" in data
    assert "timestamp" in data


def test_api_v1_health_check(client):
    """Test /api/v1/health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "DemandIQ Backend"


def test_root_welcome(client):
    """Test GET / endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "DemandIQ" in data["message"]
