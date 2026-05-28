# backend/tests/unit/monitoring/test_alerting.py

from unittest.mock import Mock
from datetime import datetime, timezone
from src.monitoring.alerting import (
    run_monitoring_check,
    _create_github_issue,
    _build_issue_body,
)


class TestBuildIssueBody:
    """Test suite for _build_issue_body."""

    def test_issue_body_contains_alert_type(self):
        """Test that issue body contains alert type."""
        metrics = {
            "nb_interactions": 100,
            "latence": {"moyenne_ms": 600, "max_ms": 1000},
        }
        body = _build_issue_body("Latence excessive", metrics, 600, 500)

        assert "Latence excessive" in body
        assert "600" in body
        assert "500" in body

    def test_issue_body_contains_metrics(self):
        """Test that issue body contains metrics in JSON."""
        metrics = {"test": "data"}
        body = _build_issue_body("Test Alert", metrics, 1.5, 1.0)

        assert "test" in body
        assert "data" in body

    def test_issue_body_structure(self):
        """Test that issue body has proper structure."""
        metrics = {}
        body = _build_issue_body("Test", metrics, 100, 50)

        assert "🚨" in body
        assert "Valeur actuelle" in body
        assert "Seuil configuré" in body


class TestCreateGithubIssue:
    """Test suite for _create_github_issue."""

    def test_github_issue_created_successfully(
        self, mock_github_env, mock_github_requests
    ):
        """Test successful GitHub issue creation."""
        result = _create_github_issue("Test Title", "Test body")

        assert result["created"] is True
        assert result["issue_number"] == 42
        assert "github.com" in result["url"]

    def test_github_issue_missing_token(self, monkeypatch):
        """Test GitHub issue creation without token."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.setenv("GITHUB_REPO", "test/repo")

        result = _create_github_issue("Title", "Body")

        assert result["created"] is False
        assert "non configurés" in result["reason"].lower()

    def test_github_issue_missing_repo(self, monkeypatch):
        """Test GitHub issue creation without repo."""
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.delenv("GITHUB_REPO", raising=False)

        result = _create_github_issue("Title", "Body")

        assert result["created"] is False
        assert "non configurés" in result["reason"].lower()

    def test_github_api_failure(self, mock_github_env, monkeypatch):
        """Test GitHub API failure handling."""

        def mock_post(*args, **kwargs):
            raise Exception("API Error")

        monkeypatch.setattr("src.monitoring.alerting.http_requests.post", mock_post)

        result = _create_github_issue("Title", "Body")

        assert result["created"] is False
        assert "API Error" in result["reason"]

    def test_github_issue_payload_structure(
        self, mock_github_env, mock_github_requests
    ):
        """Test that GitHub API is called with correct payload."""
        title = "Test Alert Title"
        body = "Test alert body content"

        _create_github_issue(title, body)

        # Verify the mock was called
        assert mock_github_requests.called
        call_args = mock_github_requests.call_args

        # Check payload
        payload = call_args[1]["json"]
        assert payload["title"] == title
        assert payload["body"] == body
        assert "monitoring" in payload["labels"]


class TestRunMonitoringCheck:
    """Test suite for run_monitoring_check."""

    def test_no_interactions_available(self, tmp_interactions_log):
        """Test monitoring check with no interactions."""
        result = run_monitoring_check()

        assert result["status"] == "ok"
        assert len(result["alertes"]) == 0
        assert result["nb_interactions_analysees"] == 0

    def test_latency_threshold_exceeded(self, monkeypatch, tmp_interactions_log):
        """Test alert when latency exceeds threshold."""
        # Create interactions with high latency
        interactions = [
            {
                "request_id": f"req-{i}",
                "latency_ms": 600,  # > 500ms threshold
                "status": "success",
                "tools_called": ["tool"],
                "answer_length": 100,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)
        ]

        # Write to log
        import json

        with open(tmp_interactions_log, "w") as f:
            for i in interactions:
                f.write(json.dumps(i) + "\n")

        # Mock GitHub to avoid API calls
        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")
        mock_post = Mock()
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "number": 1,
            "html_url": "http://test",
        }
        monkeypatch.setattr("src.monitoring.alerting.http_requests.post", mock_post)

        result = run_monitoring_check(last_n=10)

        assert result["status"] == "alert"
        assert any(a["type"] == "latence" for a in result["alertes"])

    def test_error_rate_threshold_exceeded(self, monkeypatch, tmp_interactions_log):
        """Test alert when error rate exceeds threshold."""
        interactions = [
            {
                "request_id": f"req-{i}",
                "latency_ms": 300,
                "status": "error",  # 100% error rate
                "tools_called": [],
                "answer_length": 50,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)
        ]

        import json

        with open(tmp_interactions_log, "w") as f:
            for i in interactions:
                f.write(json.dumps(i) + "\n")

        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")
        mock_post = Mock()
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "number": 1,
            "html_url": "http://test",
        }
        monkeypatch.setattr("src.monitoring.alerting.http_requests.post", mock_post)

        result = run_monitoring_check(last_n=10)

        assert result["status"] == "alert"
        assert any(a["type"] == "taux_erreur" for a in result["alertes"])

    def test_tools_threshold_exceeded(self, monkeypatch, tmp_interactions_log):
        """Test alert when tool usage rate is low."""
        interactions = [
            {
                "request_id": f"req-{i}",
                "latency_ms": 300,
                "status": "success",
                "tools_called": [],  # No tools called
                "answer_length": 100,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)
        ]

        import json

        with open(tmp_interactions_log, "w") as f:
            for i in interactions:
                f.write(json.dumps(i) + "\n")

        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")
        mock_post = Mock()
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "number": 1,
            "html_url": "http://test",
        }
        monkeypatch.setattr("src.monitoring.alerting.http_requests.post", mock_post)

        result = run_monitoring_check(last_n=10)

        assert result["status"] == "alert"
        assert any(a["type"] == "sans_outil" for a in result["alertes"])

    def test_healthy_metrics_no_alerts(self, monkeypatch, tmp_interactions_log):
        """Test no alerts when all metrics are healthy."""
        interactions = [
            {
                "request_id": f"req-{i}",
                "latency_ms": 200,  # < 500ms
                "status": "success",
                "tools_called": ["tool"],  # Tools called
                "answer_length": 200,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)
        ]

        import json

        with open(tmp_interactions_log, "w") as f:
            for i in interactions:
                f.write(json.dumps(i) + "\n")

        result = run_monitoring_check(last_n=10)

        assert result["status"] == "ok"
        assert len(result["alertes"]) == 0

    def test_multiple_alerts_triggered(self, monkeypatch, tmp_interactions_log):
        """Test multiple alerts triggered simultaneously."""
        interactions = [
            {
                "request_id": f"req-{i}",
                "latency_ms": 600,  # > threshold
                "status": "error",  # high error rate
                "tools_called": [],  # no tools
                "answer_length": 50,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            for i in range(5)
        ]

        import json

        with open(tmp_interactions_log, "w") as f:
            for i in interactions:
                f.write(json.dumps(i) + "\n")

        monkeypatch.setenv("GITHUB_TOKEN", "token")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")
        mock_post = Mock()
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {
            "number": 1,
            "html_url": "http://test",
        }
        monkeypatch.setattr("src.monitoring.alerting.http_requests.post", mock_post)

        result = run_monitoring_check(last_n=10)

        assert result["status"] == "alert"
        assert len(result["alertes"]) >= 2  # At least latency + error rate

    def test_response_contains_metrics(self, tmp_interactions_log):
        """Test that response includes full metrics."""
        interactions = [
            {
                "request_id": "req-1",
                "latency_ms": 300,
                "status": "success",
                "tools_called": ["tool"],
                "answer_length": 100,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]

        import json

        with open(tmp_interactions_log, "w") as f:
            for i in interactions:
                f.write(json.dumps(i) + "\n")

        result = run_monitoring_check()

        assert "metriques" in result
        assert "latence" in result["metriques"]
        assert "erreurs" in result["metriques"]
        assert "outils" in result["metriques"]
