# backend/tests/unit/monitoring/test_logger.py

import pytest
from datetime import datetime
from src.monitoring.logger import load_interactions, compute_metrics


class TestLoadInteractions:
    """Test suite for load_interactions function."""

    def test_empty_log_file(self, tmp_interactions_log):
        """Test loading from empty log file."""
        interactions = load_interactions()

        assert isinstance(interactions, list)
        assert len(interactions) == 0

    def test_load_interactions_from_file(self, sample_interactions_log):
        """Test loading interactions from populated log file."""
        interactions = load_interactions()

        assert len(interactions) == 3
        assert interactions[0]["request_id"] == "req-001"
        assert interactions[2]["request_id"] == "req-003"

    def test_filter_last_n_interactions(self, sample_interactions_log):
        """Test filtering to last N interactions."""
        interactions = load_interactions(last_n=2)

        assert len(interactions) == 2
        assert interactions[0]["request_id"] == "req-002"
        assert interactions[1]["request_id"] == "req-003"

    def test_filter_since_hours(self, sample_interactions_log):
        """Test filtering by time (since_hours)."""
        # Get interactions from last 6 minutes (should include recent ones)
        interactions = load_interactions(since_hours=0.1)

        assert len(interactions) >= 1
        # Most recent interaction should be included
        assert any(i["request_id"] == "req-003" for i in interactions)

    def test_corrupted_json_line_ignored(self, tmp_interactions_log):
        """Test that corrupted JSON lines are ignored."""
        with open(tmp_interactions_log, "w", encoding="utf-8") as f:
            f.write('{"valid": "json"}\n')
            f.write("this is not json at all\n")
            f.write('{"another": "valid"}\n')

        interactions = load_interactions()

        assert len(interactions) == 2
        assert interactions[0]["valid"] == "json"
        assert interactions[1]["another"] == "valid"

    def test_empty_lines_ignored(self, tmp_interactions_log):
        """Test that empty lines are skipped."""
        with open(tmp_interactions_log, "w", encoding="utf-8") as f:
            f.write('{"id": 1}\n')
            f.write("\n")
            f.write("\n")
            f.write('{"id": 2}\n')

        interactions = load_interactions()

        assert len(interactions) == 2


class TestComputeMetrics:
    """Test suite for compute_metrics function."""

    def test_empty_interactions_list(self):
        """Test with empty interactions list."""
        metrics = compute_metrics([])

        assert metrics["nb_interactions"] == 0
        assert "message" in metrics

    def test_latency_metrics(self, sample_interactions_log):
        """Test latency calculation."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        assert metrics["latence"]["moyenne_ms"] > 0
        assert metrics["latence"]["max_ms"] > 0
        # Max should be >= average
        assert metrics["latence"]["max_ms"] >= metrics["latence"]["moyenne_ms"]

    def test_error_rate_calculation(self, sample_interactions_log):
        """Test error rate calculation."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        # In sample data: 1 error out of 3 = 33.33%
        assert metrics["erreurs"]["nb"] == 1
        assert metrics["erreurs"]["taux_pct"] == pytest.approx(33.33, abs=0.1)

    def test_tool_calls_frequency(self, sample_interactions_log):
        """Test tool call frequency tracking."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        assert len(metrics["outils"]["frequence"]) > 0
        assert "get_order_status" in metrics["outils"]["frequence"]
        assert "get_stock_level" in metrics["outils"]["frequence"]

    def test_tools_without_tools_called(self, sample_interactions_log):
        """Test interaction without tools_called."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        # req-003 has no tools_called
        assert metrics["outils"]["nb_interactions_sans_outil"] >= 1

    def test_tools_rate_without_tools(self, sample_interactions_log):
        """Test rate of interactions without tools."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        # 1 out of 3 interactions without tools = 33.33%
        assert metrics["outils"]["taux_sans_outil_pct"] == pytest.approx(33.33, abs=0.1)

    def test_response_length_metrics(self, sample_interactions_log):
        """Test response length categorization."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        assert "nb_trop_courtes" in metrics["reponses"]
        assert "nb_trop_longues" in metrics["reponses"]
        # Sample data has short responses (50-150 chars)
        assert metrics["reponses"]["nb_trop_courtes"] >= 1

    def test_total_tool_calls(self, sample_interactions_log):
        """Test total tool calls count."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        # 2 interactions with tools called
        assert metrics["outils"]["nb_appels_total"] == 2

    def test_period_timestamps(self, sample_interactions_log):
        """Test that period first and last timestamps are recorded."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        assert "premiere" in metrics["periode"]
        assert "derniere" in metrics["periode"]
        # Timestamps should be ISO format strings
        assert isinstance(metrics["periode"]["premiere"], str)
        assert isinstance(metrics["periode"]["derniere"], str)

    def test_all_required_fields(self, sample_interactions_log):
        """Test that all required metric fields are present."""
        interactions = load_interactions()
        metrics = compute_metrics(interactions)

        required_sections = [
            "nb_interactions",
            "latence",
            "erreurs",
            "outils",
            "reponses",
        ]
        for section in required_sections:
            assert section in metrics

    def test_metrics_with_successful_interactions_only(self):
        """Test metrics with only successful interactions."""
        interactions = [
            {
                "request_id": "1",
                "latency_ms": 400,
                "status": "success",
                "tools_called": ["tool_a"],
                "answer_length": 200,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "request_id": "2",
                "latency_ms": 500,
                "status": "success",
                "tools_called": ["tool_b"],
                "answer_length": 300,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]

        metrics = compute_metrics(interactions)

        assert metrics["nb_interactions"] == 2
        assert metrics["erreurs"]["taux_pct"] == 0.0
        assert metrics["outils"]["taux_sans_outil_pct"] == 0.0
