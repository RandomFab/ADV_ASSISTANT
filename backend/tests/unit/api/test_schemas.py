# backend/tests/unit/api/test_schemas.py

import pytest
from pydantic import ValidationError
from src.api.schemas import ChatRequest, ChatResponse


class TestChatRequest:
    """Test suite for ChatRequest schema."""

    def test_valid_chat_request(self):
        """Test creating a valid ChatRequest."""
        request = ChatRequest(question="What is the order status?")

        assert request.question == "What is the order status?"

    def test_missing_question_field(self):
        """Test ChatRequest with missing question field."""
        with pytest.raises(ValidationError):
            ChatRequest()

    def test_empty_question_string(self):
        """Test ChatRequest with empty question."""
        # Pydantic allows empty strings by default
        request = ChatRequest(question="")
        assert request.question == ""

    def test_question_with_special_characters(self):
        """Test ChatRequest with special characters."""
        question = "Quel est le statut de la commande? 🏭 [CMD-2024-001]"
        request = ChatRequest(question=question)

        assert request.question == question

    def test_question_with_newlines(self):
        """Test ChatRequest with multiline question."""
        question = "First line\nSecond line"
        request = ChatRequest(question=question)

        assert request.question == question

    def test_non_string_question_fails(self):
        """Test ChatRequest rejects non-string question."""
        with pytest.raises(ValidationError):
            ChatRequest(question=123)

    def test_none_question_fails(self):
        """Test ChatRequest rejects None."""
        with pytest.raises(ValidationError):
            ChatRequest(question=None)

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        # Pydantic by default ignores extra fields
        request = ChatRequest(question="Test", extra_field="ignored")
        assert request.question == "Test"


class TestChatResponse:
    """Test suite for ChatResponse schema."""

    def test_valid_chat_response(self):
        """Test creating a valid ChatResponse."""
        response = ChatResponse(
            request_id="req-123",
            question="What is the status?",
            answer="The order is delivered.",
            tools_called=["get_order_status"],
            latency_ms=500
        )

        assert response.request_id == "req-123"
        assert response.question == "What is the status?"
        assert response.answer == "The order is delivered."
        assert response.tools_called == ["get_order_status"]
        assert response.latency_ms == 500

    def test_empty_tools_called_list(self):
        """Test ChatResponse with empty tools list."""
        response = ChatResponse(
            request_id="req-456",
            question="Who are you?",
            answer="I am SteelBot.",
            tools_called=[],
            latency_ms=300
        )

        assert response.tools_called == []

    def test_multiple_tools_called(self):
        """Test ChatResponse with multiple tools."""
        tools = ["get_client_info", "get_order_status", "search_reclamations"]
        response = ChatResponse(
            request_id="req-789",
            question="Full client info?",
            answer="Client details and orders...",
            tools_called=tools,
            latency_ms=1200
        )

        assert response.tools_called == tools

    def test_missing_required_field(self):
        """Test ChatResponse with missing required field."""
        with pytest.raises(ValidationError):
            ChatResponse(
                request_id="req-123",
                question="Test",
                answer="Test answer"
                # Missing tools_called and latency_ms
            )

    def test_invalid_latency_type(self):
        """Test ChatResponse with invalid latency type."""
        with pytest.raises(ValidationError):
            ChatResponse(
                request_id="req-123",
                question="Test",
                answer="Test",
                tools_called=[],
                latency_ms="500ms"  # Should be int
            )

    def test_negative_latency(self):
        """Test ChatResponse with negative latency."""
        # Pydantic allows negative numbers by default
        response = ChatResponse(
            request_id="req-123",
            question="Test",
            answer="Test",
            tools_called=[],
            latency_ms=-100
        )
        assert response.latency_ms == -100

    def test_zero_latency(self):
        """Test ChatResponse with zero latency."""
        response = ChatResponse(
            request_id="req-123",
            question="Test",
            answer="Test",
            tools_called=[],
            latency_ms=0
        )
        assert response.latency_ms == 0

    def test_long_answer_text(self):
        """Test ChatResponse with very long answer."""
        long_answer = "x" * 10000
        response = ChatResponse(
            request_id="req-123",
            question="Test",
            answer=long_answer,
            tools_called=[],
            latency_ms=1000
        )

        assert len(response.answer) == 10000

    def test_special_characters_in_fields(self):
        """Test ChatResponse with special characters."""
        response = ChatResponse(
            request_id="req-éàü-123",
            question="État de la commande? 🏭",
            answer="Réponse: Livrée ✅",
            tools_called=["outil-test"],
            latency_ms=500
        )

        assert "éàü" in response.request_id
        assert "🏭" in response.question
        assert "✅" in response.answer

    def test_response_serialization(self):
        """Test ChatResponse can be serialized to JSON."""
        response = ChatResponse(
            request_id="req-123",
            question="Test?",
            answer="Answer.",
            tools_called=["tool1"],
            latency_ms=400
        )

        # Serialize to dict
        data = response.model_dump()

        assert data["request_id"] == "req-123"
        assert data["latency_ms"] == 400
        assert isinstance(data["tools_called"], list)

    def test_response_list_type(self):
        """Test that tools_called is properly typed as list[str]."""
        response = ChatResponse(
            request_id="req-123",
            question="Test",
            answer="Test",
            tools_called=["tool_a", "tool_b"],
            latency_ms=500
        )

        # Verify it's a list of strings
        assert isinstance(response.tools_called, list)
        for tool in response.tools_called:
            assert isinstance(tool, str)
