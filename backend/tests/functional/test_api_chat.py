# backend/tests/functional/test_api_chat.py

import json
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from src.api.routes import agent_state


class TestChatEndpoint:
    """Test suite for POST /chat endpoint."""

    def test_chat_successful_response(self, api_client, tmp_interactions_log):
        """Test successful chat request and response structure."""
        response = api_client.post(
            "/chat",
            json={"question": "What is the order status?"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        required_fields = ["request_id", "question", "answer", "tools_called", "latency_ms"]
        for field in required_fields:
            assert field in data

    def test_chat_with_tools_called(self, api_client, tmp_interactions_log):
        """Test chat response includes tools that were called."""
        # Create a mock agent that calls tools
        async def mock_ainvoke(input_dict):
            return {
                "messages": [
                    HumanMessage(content="What is the status?"),
                    ToolMessage(content="Tool output", name="get_order_status", tool_call_id="test-id-1"),
                    AIMessage(content="The order is in production.")
                ]
            }

        agent_state["agent"].ainvoke = mock_ainvoke

        response = api_client.post(
            "/chat",
            json={"question": "What is the status?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "get_order_status" in data["tools_called"]

    def test_chat_without_tools_called(self, api_client, tmp_interactions_log):
        """Test chat response when no tools are called."""
        response = api_client.post(
            "/chat",
            json={"question": "Who are you?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["tools_called"], list)

    def test_chat_latency_measured(self, api_client, tmp_interactions_log):
        """Test that latency is measured and returned."""
        response = api_client.post(
            "/chat",
            json={"question": "Test question"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "latency_ms" in data
        assert isinstance(data["latency_ms"], int)
        assert data["latency_ms"] >= 0

    def test_chat_agent_not_initialized(self, api_client, tmp_interactions_log):
        """Test error when agent is not initialized."""
        # Clear agent state
        agent_state.clear()

        response = api_client.post(
            "/chat",
            json={"question": "Test"}
        )

        assert response.status_code == 503
        assert "non disponible" in response.json()["detail"].lower()

    def test_chat_agent_error_handling(self, api_client, tmp_interactions_log):
        """Test error handling when agent raises exception."""
        async def mock_failing_ainvoke(input_dict):
            raise ValueError("Agent error")

        agent_state["agent"].ainvoke = mock_failing_ainvoke

        response = api_client.post(
            "/chat",
            json={"question": "Test"}
        )

        assert response.status_code == 500
        assert "Erreur agent" in response.json()["detail"]

    def test_chat_question_echoed_in_response(self, api_client, tmp_interactions_log):
        """Test that question is echoed in response."""
        question = "Where is product COIL-304?"
        response = api_client.post(
            "/chat",
            json={"question": question}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == question

    def test_chat_answer_not_empty(self, api_client, tmp_interactions_log):
        """Test that answer is not empty."""
        response = api_client.post(
            "/chat",
            json={"question": "Test question"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["answer"]
        assert data["answer"] != "Pas de réponse"

    def test_chat_request_id_unique(self, api_client, tmp_interactions_log):
        """Test that each request gets a unique ID."""
        response1 = api_client.post(
            "/chat",
            json={"question": "Question 1"}
        )
        response2 = api_client.post(
            "/chat",
            json={"question": "Question 2"}
        )

        id1 = response1.json()["request_id"]
        id2 = response2.json()["request_id"]

        assert id1 != id2

    def test_chat_logs_to_file(self, api_client, tmp_interactions_log):
        """Test that interaction is logged to file."""
        response = api_client.post(
            "/chat",
            json={"question": "Log test"}
        )

        assert response.status_code == 200

        # Verify log file was written
        with open(tmp_interactions_log, "r") as f:
            lines = f.readlines()

        assert len(lines) > 0

        # Parse last log entry
        last_log = json.loads(lines[-1])
        assert last_log["question"] == "Log test"
        assert last_log["status"] == "success"

    def test_chat_multiple_tools_in_response(self, api_client, tmp_interactions_log):
        """Test response with multiple tools called."""
        async def mock_multi_tool_ainvoke(input_dict):
            return {
                "messages": [
                    HumanMessage(content="Full info?"),
                    ToolMessage(content="Output 1", name="get_client_info", tool_call_id="test-id-1"),
                    ToolMessage(content="Output 2", name="get_order_status", tool_call_id="test-id-2"),
                    AIMessage(content="Full details...")
                ]
            }

        agent_state["agent"].ainvoke = mock_multi_tool_ainvoke

        response = api_client.post(
            "/chat",
            json={"question": "Full client info?"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tools_called"]) == 2
        assert "get_client_info" in data["tools_called"]
        assert "get_order_status" in data["tools_called"]

    def test_chat_answer_length_in_log(self, api_client, tmp_interactions_log):
        """Test that answer length is correctly logged."""
        response = api_client.post(
            "/chat",
            json={"question": "Test"}
        )

        assert response.status_code == 200

        with open(tmp_interactions_log, "r") as f:
            last_log = json.loads(f.readlines()[-1])

        assert "answer_length" in last_log
        assert last_log["answer_length"] > 0

    def test_chat_invalid_request_format(self, api_client):
        """Test invalid request format."""
        response = api_client.post(
            "/chat",
            json={"not_question": "Invalid"}
        )

        assert response.status_code in [422, 400]  # Validation error

    def test_chat_response_content_type(self, api_client, tmp_interactions_log):
        """Test that response has correct content type."""
        response = api_client.post(
            "/chat",
            json={"question": "Test"}
        )

        assert "application/json" in response.headers.get("content-type", "")
