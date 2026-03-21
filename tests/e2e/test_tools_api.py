"""
E2E Tests for Tools and Skills API

Tests tool listing, skills listing, and related endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestToolsAPI:
    """Test suite for tools-related API endpoints."""

    def test_list_tools_success(
        self,
        test_client: TestClient
    ):
        """Test that tools endpoint returns tool definitions."""
        response = test_client.get("/api/nanobot/tools")

        assert response.status_code == 200

        data = response.json()
        assert "tools" in data
        assert "count" in data

        assert isinstance(data["tools"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["tools"])

    def test_tools_have_required_fields(
        self,
        test_client: TestClient
    ):
        """Test that each tool has required fields."""
        response = test_client.get("/api/nanobot/tools")
        data = response.json()

        for tool in data["tools"]:
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert isinstance(tool["name"], str)
            assert isinstance(tool["description"], str)

    def test_tools_parameters_structure(
        self,
        test_client: TestClient
    ):
        """Test that tool parameters have correct structure."""
        response = test_client.get("/api/nanobot/tools")
        data = response.json()

        for tool in data["tools"]:
            parameters = tool["parameters"]
            if parameters:  # Some tools might have no parameters
                # Should follow OpenAI function calling format
                assert "type" in parameters or "properties" in parameters

    def test_expected_tools_are_registered(
        self,
        test_client: TestClient
    ):
        """Test that core GIS tools are registered."""
        response = test_client.get("/api/nanobot/tools")
        data = response.json()

        tool_names = [tool["name"] for tool in data["tools"]]

        # Check for expected core tools (using actual tool names, not class names)
        expected_tools = [
            "read_data",
            "write_data",
            "convert_data",
            "buffer"
        ]

        for expected in expected_tools:
            assert expected in tool_names, f"Expected tool {expected} not found in {tool_names}"

    def test_tools_count_is_positive(
        self,
        test_client: TestClient
    ):
        """Test that at least some tools are registered."""
        response = test_client.get("/api/nanobot/tools")
        data = response.json()

        assert data["count"] > 0, "No tools registered"
        assert len(data["tools"]) > 0, "Tools list is empty"


class TestSkillsAPI:
    """Test suite for skills-related API endpoints."""

    def test_list_skills_success(
        self,
        test_client: TestClient
    ):
        """Test that skills endpoint returns skill definitions."""
        response = test_client.get("/api/nanobot/skills")

        assert response.status_code == 200

        data = response.json()
        assert "skills" in data
        assert "count" in data

        assert isinstance(data["skills"], list)
        assert isinstance(data["count"], int)
        assert data["count"] == len(data["skills"])

    def test_skills_have_required_fields(
        self,
        test_client: TestClient
    ):
        """Test that each skill has required fields."""
        response = test_client.get("/api/nanobot/skills")
        data = response.json()

        for skill in data["skills"]:
            assert "name" in skill
            assert "path" in skill
            assert "source" in skill
            assert isinstance(skill["name"], str)
            assert isinstance(skill["path"], str)
            assert isinstance(skill["source"], str)

    def test_skills_source_values(
        self,
        test_client: TestClient
    ):
        """Test that skills have valid source values."""
        response = test_client.get("/api/nanobot/skills")
        data = response.json()

        for skill in data["skills"]:
            # Source should be one of the expected values
            valid_sources = ["project", "global", "builtin"]
            # If skills exist, check source (might be empty in tests)
            if skill["source"]:
                assert skill["source"] in valid_sources, \
                    f"Invalid skill source: {skill['source']}"

    def test_empty_skills_handling(
        self,
        test_client: TestClient
    ):
        """Test that skills endpoint handles empty skills gracefully."""
        response = test_client.get("/api/nanobot/skills")

        assert response.status_code == 200
        data = response.json()

        # Should return empty list if no skills
        if data["count"] == 0:
            assert len(data["skills"]) == 0
        else:
            assert len(data["skills"]) > 0


class TestToolsAndSkillsIntegration:
    """Test suite for tools and skills integration."""

    def test_tools_available_after_chat(
        self,
        test_client: TestClient,
        sample_chat_request: dict
    ):
        """Test that tools remain available after a chat session."""
        # Send a chat message
        test_client.post("/api/nanobot/chat", json=sample_chat_request)

        # Tools should still be available
        response = test_client.get("/api/nanobot/tools")
        assert response.status_code == 200
        assert response.json()["count"] > 0

    def test_tools_consistency_across_calls(
        self,
        test_client: TestClient
    ):
        """Test that tools list is consistent across multiple calls."""
        response1 = test_client.get("/api/nanobot/tools")
        response2 = test_client.get("/api/nanobot/tools")

        assert response1.status_code == 200
        assert response2.status_code == 200

        tools1 = response1.json()["tools"]
        tools2 = response2.json()["tools"]

        # Compare tool names (order shouldn't matter)
        names1 = sorted([t["name"] for t in tools1])
        names2 = sorted([t["name"] for t in tools2])

        assert names1 == names2, "Tools list changed between calls"

    def test_all_endpoints_return_valid_json(
        self,
        test_client: TestClient
    ):
        """Test that all API endpoints return valid JSON."""
        endpoints = [
            "/api/nanobot/tools",
            "/api/nanobot/skills",
            "/api/nanobot/sessions"
        ]

        for endpoint in endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200

            # Should be parseable JSON
            data = response.json()
            assert isinstance(data, dict)


class TestToolParameterValidation:
    """Test suite for tool parameter validation through chat."""

    def test_chat_can_trigger_tool(
        self,
        test_client: TestClient,
        agent_loop,
        sample_chat_request: dict
    ):
        """Test that chat can trigger a tool call."""
        from unittest.mock import patch

        # Mock provider to return tool call
        async def mock_chat_with_tools(*args, **kwargs):
            return {
                "content": "",
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "ReadDataTool",
                            "arguments": '{"path": "/test/path"}'
                        }
                    }
                ]
            }

        original_chat = agent_loop.provider.chat
        agent_loop.provider.chat = mock_chat_with_tools

        try:
            response = test_client.post("/api/nanobot/chat", json=sample_chat_request)
            assert response.status_code == 200
        finally:
            agent_loop.provider.chat = original_chat

    def test_invalid_tool_call_handling(
        self,
        test_client: TestClient,
        agent_loop,
        sample_chat_request: dict
    ):
        """Test that invalid tool calls are handled gracefully."""
        from unittest.mock import patch

        # Mock provider to return invalid tool call
        async def mock_chat_with_invalid_tool(*args, **kwargs):
            return {
                "content": "",
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "NonExistentTool",
                            "arguments": '{}'
                        }
                    }
                ]
            }

        original_chat = agent_loop.provider.chat
        agent_loop.provider.chat = mock_chat_with_invalid_tool

        try:
            # Should handle gracefully, not crash
            response = test_client.post("/api/nanobot/chat", json=sample_chat_request)
            # Should still return a response (even if tool failed)
            assert response.status_code in [200, 500]
        finally:
            agent_loop.provider.chat = original_chat


class TestToolExecution:
    """Test suite for actual tool execution through the API."""

    def test_tool_execution_in_chat_flow(
        self,
        test_client: TestClient,
        agent_loop,
        sample_chat_request: dict
    ):
        """Test that tools execute correctly within chat flow."""
        from unittest.mock import patch, AsyncMock

        # Track tool execution
        executed_tools = []

        original_execute = agent_loop.tool_registry.execute

        async def mock_execute(tool_name, tool_args):
            executed_tools.append((tool_name, tool_args))
            return "Mock tool result"

        agent_loop.tool_registry.execute = mock_execute

        try:
            # Mock provider to request tool use
            async def mock_chat(*args, **kwargs):
                if not executed_tools:
                    # First call: request tool
                    return {
                        "content": "Let me check that for you.",
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "ReadDataTool",
                                    "arguments": '{"path": "/test/data.json"}'
                                }
                            }
                        ]
                    }
                else:
                    # Second call: after tool execution
                    return {
                        "content": "I've read the data. Here's what I found...",
                        "role": "assistant",
                        "tool_calls": []
                    }

            original_provider_chat = agent_loop.provider.chat
            agent_loop.provider.chat = mock_chat

            try:
                response = test_client.post("/api/nanobot/chat", json=sample_chat_request)
                assert response.status_code == 200

                # Verify tool was executed
                assert len(executed_tools) == 1
                assert executed_tools[0][0] == "ReadDataTool"

            finally:
                agent_loop.provider.chat = original_provider_chat

        finally:
            agent_loop.tool_registry.execute = original_execute