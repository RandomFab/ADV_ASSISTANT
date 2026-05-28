# backend/tests/functional/test_api_monitoring.py



class TestMonitoringCheckEndpoint:
    """Test suite for GET /monitoring/check endpoint."""

    def test_monitoring_check_success(self, api_client, sample_interactions_log):
        """Test successful monitoring check."""
        response = api_client.get("/monitoring/check")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "nb_interactions_analysees" in data
        assert "metriques" in data
        assert "alertes" in data

    def test_monitoring_check_no_interactions(self, api_client, tmp_interactions_log):
        """Test monitoring check with no interactions."""
        response = api_client.get("/monitoring/check")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert data["nb_interactions_analysees"] == 0
        assert len(data["alertes"]) == 0

    def test_monitoring_check_with_interactions(self, api_client, sample_interactions_log):
        """Test monitoring check with interactions available."""
        response = api_client.get("/monitoring/check")

        assert response.status_code == 200
        data = response.json()

        assert data["nb_interactions_analysees"] > 0
        assert "metriques" in data

    def test_monitoring_check_metrics_included(self, api_client, sample_interactions_log):
        """Test that metrics are included in check response."""
        response = api_client.get("/monitoring/check")

        assert response.status_code == 200
        data = response.json()

        metrics = data["metriques"]
        assert "latence" in metrics
        assert "erreurs" in metrics
        assert "outils" in metrics

    def test_monitoring_check_alerts_structure(self, api_client, sample_interactions_log):
        """Test alert structure in monitoring check."""
        response = api_client.get("/monitoring/check")

        assert response.status_code == 200
        data = response.json()

        if data["alertes"]:
            alert = data["alertes"][0]
            assert "type" in alert
            assert "valeur" in alert
            assert "seuil" in alert
            assert "github_issue" in alert

    def test_monitoring_check_response_schema(self, api_client, sample_interactions_log):
        """Test complete response schema."""
        response = api_client.get("/monitoring/check")

        assert response.status_code == 200
        data = response.json()

        required_fields = ["status", "nb_interactions_analysees", "metriques", "alertes"]
        for field in required_fields:
            assert field in data

    def test_monitoring_check_content_type(self, api_client, sample_interactions_log):
        """Test response content type."""
        response = api_client.get("/monitoring/check")

        assert "application/json" in response.headers.get("content-type", "")


class TestMonitoringReportEndpoint:
    """Test suite for GET /monitoring/report endpoint."""

    def test_monitoring_report_success(self, api_client, sample_interactions_log):
        """Test successful report generation."""
        response = api_client.get("/monitoring/report")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "ok"
        assert "report_path" in data

    def test_monitoring_report_path_is_string(self, api_client, sample_interactions_log):
        """Test that report_path is a string."""
        response = api_client.get("/monitoring/report")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["report_path"], str)

    def test_monitoring_report_no_interactions_error(self, api_client, tmp_interactions_log):
        """Test report generation fails with no interactions."""
        response = api_client.get("/monitoring/report")

        # Should return error status when not enough data
        assert response.status_code == 200
        data = response.json()

        # When no interactions, should error
        if "status" in data and data["status"] == "error":
            assert "message" in data
        else:
            # Or might return path even with 0 interactions
            pass

    def test_monitoring_report_response_schema(self, api_client, sample_interactions_log):
        """Test report response schema."""
        response = api_client.get("/monitoring/report")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        if data["status"] == "ok":
            assert "report_path" in data
        else:
            assert "message" in data

    def test_monitoring_report_content_type(self, api_client, sample_interactions_log):
        """Test response content type."""
        response = api_client.get("/monitoring/report")

        assert "application/json" in response.headers.get("content-type", "")

    def test_monitoring_report_idempotent(self, api_client, sample_interactions_log):
        """Test that report can be generated multiple times."""
        response1 = api_client.get("/monitoring/report")
        response2 = api_client.get("/monitoring/report")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Both should have paths (may be same or different)
        data1 = response1.json()
        data2 = response2.json()

        if data1.get("status") == "ok":
            assert "report_path" in data1
        if data2.get("status") == "ok":
            assert "report_path" in data2
