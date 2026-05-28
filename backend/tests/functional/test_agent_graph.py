# backend/tests/functional/test_agent_graph.py

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock


class TestCreateAgent:
    """Test suite for create_agent function."""

    @pytest.mark.asyncio
    async def test_agent_creation_success(self, monkeypatch):
        """Test that agent is created successfully."""
        # Mock the external dependencies
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        monkeypatch.setenv("MCP_URL", "http://127.0.0.1:8001")

        with patch("src.agent.graph.ChatMistralAI") as mock_llm, \
             patch("src.agent.graph.MultiServerMCPClient") as mock_mcp_client, \
             patch("src.agent.graph.create_react_agent") as mock_create_agent:

            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance

            # Mock MCP client and its methods
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.get_tools = AsyncMock(return_value=[])
            mock_mcp_client.return_value = mock_mcp_instance

            mock_agent = AsyncMock()
            mock_create_agent.return_value = mock_agent

            from src.agent.graph import create_agent
            agent = await create_agent()

            # Verify agent was returned
            assert agent is not None

    @pytest.mark.asyncio
    async def test_agent_uses_mistral_model(self, monkeypatch):
        """Test that agent uses ChatMistralAI."""
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        monkeypatch.setenv("MCP_URL", "http://127.0.0.1:8001")

        with patch("src.agent.graph.ChatMistralAI") as mock_llm, \
             patch("src.agent.graph.MultiServerMCPClient") as mock_mcp, \
             patch("src.agent.graph.create_react_agent"):

            mock_llm_instance = MagicMock()
            mock_llm.return_value = mock_llm_instance

            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.get_tools = AsyncMock(return_value=[])
            mock_mcp.return_value = mock_mcp_instance

            from src.agent.graph import create_agent
            await create_agent()

            # Verify ChatMistralAI was instantiated
            mock_llm.assert_called_once()
            call_kwargs = mock_llm.call_args[1]
            assert call_kwargs["model"] == "mistral-small-latest"
            assert call_kwargs["temperature"] == 0

    @pytest.mark.asyncio
    async def test_agent_mcp_connection(self, monkeypatch):
        """Test that agent connects to MCP server."""
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        monkeypatch.setenv("MCP_URL", "http://custom.mcp:9000")

        with patch("src.agent.graph.ChatMistralAI") as mock_llm, \
             patch("src.agent.graph.MultiServerMCPClient") as mock_mcp, \
             patch("src.agent.graph.create_react_agent"):

            mock_llm.return_value = MagicMock()

            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.get_tools = AsyncMock(return_value=[])
            mock_mcp.return_value = mock_mcp_instance

            from src.agent.graph import create_agent
            await create_agent()

            # Verify MCP client was created with correct config
            mock_mcp.assert_called_once()
            config = mock_mcp.call_args[0][0]
            assert "steelbot" in config
            assert "http://custom.mcp:9000" in config["steelbot"]["url"]

    @pytest.mark.asyncio
    async def test_agent_gets_tools_from_mcp(self, monkeypatch):
        """Test that agent retrieves tools from MCP."""
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        monkeypatch.setenv("MCP_URL", "http://127.0.0.1:8001")

        with patch("src.agent.graph.ChatMistralAI") as mock_llm, \
             patch("src.agent.graph.MultiServerMCPClient") as mock_mcp, \
             patch("src.agent.graph.create_react_agent") as mock_create_agent:

            mock_llm.return_value = MagicMock()

            mock_tools = ["get_client_info", "get_order_status"]
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.get_tools = AsyncMock(return_value=mock_tools)
            mock_mcp.return_value = mock_mcp_instance

            from src.agent.graph import create_agent
            await create_agent()

            # Verify get_tools was called
            mock_mcp_instance.get_tools.assert_called_once()

            # Verify create_react_agent received tools
            mock_create_agent.assert_called_once()
            call_kwargs = mock_create_agent.call_args[1]
            assert "tools" in call_kwargs
            assert call_kwargs["tools"] == mock_tools

    @pytest.mark.asyncio
    async def test_agent_missing_api_key(self, monkeypatch):
        """Test agent creation fails when API key is missing."""
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        monkeypatch.setenv("MCP_URL", "http://127.0.0.1:8001")

        from src.agent.graph import create_agent

        # Should raise or fail gracefully (may include network errors if MCP is unreachable)
        with pytest.raises(Exception):
            await create_agent()

    @pytest.mark.asyncio
    async def test_agent_uses_system_prompt(self, monkeypatch):
        """Test that agent uses system prompt."""
        monkeypatch.setenv("MISTRAL_API_KEY", "test-key")
        monkeypatch.setenv("MCP_URL", "http://127.0.0.1:8001")

        with patch("src.agent.graph.ChatMistralAI") as mock_llm, \
             patch("src.agent.graph.MultiServerMCPClient") as mock_mcp, \
             patch("src.agent.graph.create_react_agent") as mock_create_agent, \
             patch("src.agent.graph.SYSTEM_PROMPT", "Test prompt"):

            mock_llm.return_value = MagicMock()
            mock_mcp_instance = AsyncMock()
            mock_mcp_instance.get_tools = AsyncMock(return_value=[])
            mock_mcp.return_value = mock_mcp_instance

            from src.agent.graph import create_agent
            await create_agent()

            # Verify create_react_agent received system prompt
            mock_create_agent.assert_called_once()
            call_kwargs = mock_create_agent.call_args[1]
            assert call_kwargs["prompt"] == "Test prompt"
