# backend/tests/functional/test_middleware.py

import json
import logging


class TestLoggingMiddleware:
    """Test suite for LoggingMiddleware."""

    def test_middleware_logs_request(self, api_client, caplog):
        """Test that middleware logs each request."""
        with caplog.at_level(logging.INFO):
            response = api_client.get("/health")

        assert response.status_code == 200

        # Check that at least one log entry was created
        assert len(caplog.records) > 0

    def test_middleware_logs_json_structure(self, api_client, caplog):  # noqa: ARG002
        """Test that middleware logs valid JSON."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")

        # Find JSON log entries
        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        assert len(json_logs) > 0

    def test_middleware_includes_method(self, api_client, caplog):
        """Test that middleware logs HTTP method."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        if json_logs:
            assert any("method" in log for log in json_logs)
            assert any(log.get("method") == "GET" for log in json_logs)

    def test_middleware_includes_path(self, api_client, caplog):
        """Test that middleware logs request path."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        if json_logs:
            assert any("path" in log for log in json_logs)
            assert any("/health" in log.get("path", "") for log in json_logs)

    def test_middleware_includes_status_code(self, api_client, caplog):
        """Test that middleware logs status code."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        if json_logs:
            assert any("status_code" in log for log in json_logs)
            assert any(log.get("status_code") == 200 for log in json_logs)

    def test_middleware_includes_latency(self, api_client, caplog):
        """Test that middleware measures and logs latency."""
        with caplog.at_level(logging.INFO):
            response = api_client.get("/health")

        assert response.status_code == 200

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        if json_logs:
            latency_logs = [log for log in json_logs if "latency_ms" in log]
            assert len(latency_logs) > 0
            assert all(log["latency_ms"] >= 0 for log in latency_logs)

    def test_middleware_latency_reasonable(self, api_client, caplog):
        """Test that measured latency is reasonable."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        latency_logs = [log for log in json_logs if "latency_ms" in log]
        if latency_logs:
            # Health check should be fast (< 1000ms)
            assert all(log["latency_ms"] < 1000 for log in latency_logs)

    def test_middleware_logs_different_methods(self, api_client, caplog):
        """Test middleware logs different HTTP methods."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")
            api_client.post("/chat", json={"question": "test"})

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        methods = [log.get("method") for log in json_logs if "method" in log]
        assert "GET" in methods
        assert "POST" in methods

    def test_middleware_logs_different_paths(self, api_client, caplog):
        """Test middleware logs different request paths."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")
            api_client.post("/chat", json={"question": "test"})

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        paths = [log.get("path") for log in json_logs if "path" in log]
        assert any("/health" in p for p in paths)
        assert any("/chat" in p for p in paths)

    def test_middleware_logs_all_requests(self, api_client, caplog):
        """Test that every request is logged."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")
            api_client.get("/health")
            api_client.get("/health")

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Should have multiple log entries (at least 3)
        assert len(json_logs) >= 3

    def test_middleware_includes_request_id(self, api_client, caplog):
        """Test that middleware includes request_id."""
        with caplog.at_level(logging.INFO):
            api_client.get("/health")

        json_logs = []
        for record in caplog.records:
            try:
                log_data = json.loads(record.message)
                json_logs.append(log_data)
            except (json.JSONDecodeError, TypeError):
                pass

        if json_logs:
            request_ids = [
                log.get("request_id") for log in json_logs if "request_id" in log
            ]
            assert len(request_ids) > 0
            # Request IDs should be UUIDs
            for req_id in request_ids:
                assert len(req_id) == 36  # UUID format
