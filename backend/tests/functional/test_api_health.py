# backend/tests/functional/test_api_health.py

import pytest
import os
from src.api.routes import agent_state


class TestHealthEndpoint:
    """Test suite for GET /health endpoint."""

    def test_health_check_agent_ready(self, api_client):
        """Test health check when agent is ready."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["agent"] == "ready"

    def test_health_check_agent_not_initialized(self, api_client):
        """Test health check when agent is not initialized."""
        agent_state.clear()

        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["agent"] == "not initialized"

    def test_health_check_contains_mcp_url(self, api_client):
        """Test that health check includes MCP server URL."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "mcp_server" in data
        assert "/sse" in data["mcp_server"]

    def test_health_check_default_mcp_url(self, api_client, monkeypatch):
        """Test default MCP URL when env var not set."""
        monkeypatch.delenv("MCP_URL", raising=False)

        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Default should be http://127.0.0.1:8000/sse
        assert "127.0.0.1" in data["mcp_server"] or "localhost" in data["mcp_server"]
        assert "8000" in data["mcp_server"]

    def test_health_check_custom_mcp_url(self, api_client, monkeypatch):
        """Test health check with custom MCP URL."""
        custom_url = "http://mcp.example.com:9000"
        monkeypatch.setenv("MCP_URL", custom_url)

        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert custom_url in data["mcp_server"]

    def test_health_check_response_schema(self, api_client):
        """Test health check response has all required fields."""
        response = api_client.get("/health")

        assert response.status_code == 200
        data = response.json()

        required_fields = ["status", "agent", "mcp_server"]
        for field in required_fields:
            assert field in data

    def test_health_check_content_type(self, api_client):
        """Test health check response content type."""
        response = api_client.get("/health")

        assert "application/json" in response.headers.get("content-type", "")

    def test_health_check_multiple_calls(self, api_client):
        """Test health check can be called multiple times."""
        response1 = api_client.get("/health")
        response2 = api_client.get("/health")
        response3 = api_client.get("/health")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

        data1 = response1.json()
        data2 = response2.json()
        data3 = response3.json()

        # All should return same status
        assert data1["status"] == data2["status"] == data3["status"]
