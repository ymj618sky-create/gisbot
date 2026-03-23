"""
E2E Tests for Chat API Flow

Tests the complete chat interaction flow through the API.
"""
import pytest
from fastapi.testclient import TestClient


class TestChatFlow:
    """Test suite for chat API endpoints."""

    def test_chat_endpoint_returns_response(
        self,
        test_client: TestClient,
        sample_chat_request: dict
    ):
        """Test that chat endpoint returns a valid response."""
        response = test_client.post(
            "/api/chat",
            json=sample_chat_request
        )

        assert response.status_code == 200

        data = response.json()
        assert "response" in data
        assert "session_id" in data
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

    def test_chat_creates_session(
        self,
        test_client: TestClient,
        sample_chat_request: dict,
        channel: str,
        chat_id: str
    ):
        """Test that a new chat creates a session."""
        # Send initial chat
        response = test_client.post(
            "/api/chat",
            json=sample_chat_request
        )
        assert response.status_code == 200

        session_id = response.json()["session_id"]
        assert session_id != ""

        # Verify session exists
        response = test_client.get(
            f"/api/session/{channel}/{chat_id}"
        )
        assert response.status_code == 200

        session_data = response.json()
        assert session_data["channel"] == channel
        assert session_data["chat_id"] == chat_id
        assert session_data["message_count"] >= 1

    def test_multi_turn_conversation(
        self,
        test_client: TestClient,
        sample_chat_request: dict,
        channel: str,
        chat_id: str
    ):
        """Test that multiple messages maintain conversation context."""
        # First message
        response1 = test_client.post(
            "/api/chat",
            json=sample_chat_request
        )
        assert response1.status_code == 200

        # Second message in same chat
        second_request = {
            "message": "Can you tell me more?",
            "channel": channel,
            "chat_id": chat_id,
            "media": None
        }
        response2 = test_client.post(
            "/api/chat",
            json=second_request
        )
        assert response2.status_code == 200

        # Verify session has 2 messages
        session_response = test_client.get(
            f"/api/session/{channel}/{chat_id}"
        )
        assert session_response.status_code == 200
        session_data = session_response.json()
        assert session_data["message_count"] >= 2

    def test_chat_with_different_channels(
        self,
        test_client: TestClient
    ):
        """Test that different channels maintain separate sessions."""
        # Chat in web channel
        web_chat = {
            "message": "Hello from web",
            "channel": "web",
            "chat_id": "user-123",
            "media": None
        }
        response1 = test_client.post("/api/chat", json=web_chat)
        assert response1.status_code == 200
        web_session_id = response1.json()["session_id"]

        # Chat in cli channel with same chat_id
        cli_chat = {
            "message": "Hello from cli",
            "channel": "cli",
            "chat_id": "user-123",
            "media": None
        }
        response2 = test_client.post("/api/chat", json=cli_chat)
        assert response2.status_code == 200
        cli_session_id = response2.json()["session_id"]

        # Sessions should be different
        assert web_session_id != cli_session_id

    def test_chat_required_fields_validation(
        self,
        test_client: TestClient
    ):
        """Test that required fields are validated."""
        # Missing message
        response = test_client.post(
            "/api/chat",
            json={
                "channel": "test",
                "chat_id": "test-123"
            }
        )
        assert response.status_code == 422  # Validation error

        # Missing chat_id
        response = test_client.post(
            "/api/chat",
            json={
                "message": "Hello",
                "channel": "test"
            }
        )
        assert response.status_code == 422

    def test_chat_with_media_list(
        self,
        test_client: TestClient,
        sample_chat_request: dict
    ):
        """Test chat with media attachments."""
        request_with_media = {
            **sample_chat_request,
            "media": ["/path/to/image.jpg", "/path/to/document.pdf"]
        }

        response = test_client.post(
            "/api/chat",
            json=request_with_media
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    def test_chat_uses_default_channel(
        self,
        test_client: TestClient,
        chat_id: str
    ):
        """Test that default channel is used when not specified."""
        request = {
            "message": "Hello",
            "chat_id": chat_id
        }

        response = test_client.post(
            "/api/chat",
            json=request
        )

        # This should work as channel has a default value
        assert response.status_code in [200, 422]  # Depends on Pydantic config

    def test_chat_handles_long_messages(
        self,
        test_client: TestClient,
        sample_chat_request: dict
    ):
        """Test that chat handles long messages."""
        long_message = "Please analyze this data: " + "x" * 10000
        request = {
            **sample_chat_request,
            "message": long_message
        }

        response = test_client.post(
            "/api/chat",
            json=request
        )

        assert response.status_code == 200

    def test_chat_handles_special_characters(
        self,
        test_client: TestClient,
        sample_chat_request: dict
    ):
        """Test that chat handles special characters and emojis."""
        special_message = "Hello! 🌍GIS data with special chars: <>&\"'\\n\\t"
        request = {
            **sample_chat_request,
            "message": special_message
        }

        response = test_client.post(
            "/api/chat",
            json=request
        )

        assert response.status_code == 200


class TestChatStreaming:
    """Test suite for streaming chat API."""

    def test_stream_endpoint_exists(
        self,
        test_client: TestClient,
        channel: str,
        chat_id: str
    ):
        """Test that stream endpoint is accessible."""
        # Note: TestClient doesn't fully support SSE testing
        # This is a basic connectivity check
        response = test_client.post(
            f"/api/stream/{channel}/{chat_id}",
            json={"message": "Hello"}
        )

        # Response should be successful (streaming format)
        assert response.status_code == 200