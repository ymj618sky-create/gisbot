"""
E2E Tests for Session Management

Tests session creation, retrieval, listing, and deletion.
"""
import pytest
from fastapi.testclient import TestClient


class TestSessionRetrieval:
    """Test suite for session retrieval endpoints."""

    def test_get_existing_session(
        self,
        test_client: TestClient,
        sample_chat_request: dict,
        channel: str,
        chat_id: str
    ):
        """Test retrieving an existing session."""
        # Create a session via chat
        test_client.post("/api/nanobot/chat", json=sample_chat_request)

        # Get the session
        response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )

        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert "channel" in data
        assert "chat_id" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert "message_count" in data

    def test_get_nonexistent_session(
        self,
        test_client: TestClient
    ):
        """Test that non-existent sessions return 404."""
        response = test_client.get(
            "/api/nanobot/session/unknown/nonexistent-chat"
        )

        assert response.status_code == 404

    def test_session_metadata_included(
        self,
        test_client: TestClient,
        sample_chat_request: dict,
        channel: str,
        chat_id: str
    ):
        """Test that session metadata is included in response."""
        test_client.post("/api/nanobot/chat", json=sample_chat_request)

        response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "metadata" in data


class TestSessionDeletion:
    """Test suite for session deletion endpoints."""

    def test_delete_existing_session(
        self,
        test_client: TestClient,
        sample_chat_request: dict,
        channel: str,
        chat_id: str
    ):
        """Test deleting an existing session."""
        # Create a session
        test_client.post("/api/nanobot/chat", json=sample_chat_request)

        # Verify it exists
        get_response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert get_response.status_code == 200

        # Delete the session
        delete_response = test_client.delete(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert delete_response.status_code == 200

        data = delete_response.json()
        assert data["success"] is True
        assert "message" in data

        # Verify it's gone
        get_response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent_session(
        self,
        test_client: TestClient
    ):
        """Test that deleting non-existent session returns 404."""
        response = test_client.delete(
            "/api/nanobot/session/unknown/nonexistent-chat"
        )

        assert response.status_code == 404


class TestSessionListing:
    """Test suite for session listing endpoints."""

    def test_list_sessions(
        self,
        test_client: TestClient
    ):
        """Test listing all sessions."""
        response = test_client.get("/api/nanobot/sessions")

        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert "count" in data
        assert isinstance(data["sessions"], list)
        assert isinstance(data["count"], int)

    def test_list_sessions_with_limit(
        self,
        test_client: TestClient,
        sample_chat_request: dict
    ):
        """Test listing sessions with a limit."""
        # Create a few sessions
        for i in range(3):
            request = {
                "message": f"Message {i}",
                "channel": f"channel-{i}",
                "chat_id": f"chat-{i}",
                "media": None
            }
            test_client.post("/api/nanobot/chat", json=request)

        # List with limit
        response = test_client.get("/api/nanobot/sessions?limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) <= 2

    def test_list_sessions_default_limit(
        self,
        test_client: TestClient
    ):
        """Test that listing has a default limit."""
        response = test_client.get("/api/nanobot/sessions")

        assert response.status_code == 200
        data = response.json()
        # Default limit is 50, so we should get at most 50 sessions
        assert len(data["sessions"]) <= 50

    def test_list_empty_sessions(
        self,
        test_client: TestClient,
        agent_loop
    ):
        """Test listing when no sessions exist."""
        # Create a fresh session manager with no sessions
        import api.routes.agent_nanobot as nanobot_routes
        from core.agent.loop import AgentLoop
        from unittest.mock import patch

        def mock_get_empty_loop():
            from pathlib import Path
            import tempfile
            from session.manager import SessionManager

            temp_dir = Path(tempfile.mkdtemp())
            data_dir = temp_dir / "data"
            data_dir.mkdir()

            empty_session_manager = SessionManager(data_dir=data_dir)
            return AgentLoop(
                workspace=temp_dir,
                provider=agent_loop.provider,
                tool_registry=agent_loop.tool_registry,
                session_manager=empty_session_manager,
                max_iterations=5
            )

        with patch.object(
            nanobot_routes,
            'get_agent_loop',
            side_effect=mock_get_empty_loop
        ):
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(nanobot_routes.router, prefix="/api")
            client = TestClient(app)

            response = client.get("/api/nanobot/sessions")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert len(data["sessions"]) == 0


class TestSessionLifecycle:
    """Test suite for complete session lifecycle."""

    def test_session_full_lifecycle(
        self,
        test_client: TestClient,
        sample_chat_request: dict,
        channel: str,
        chat_id: str
    ):
        """Test complete lifecycle: create -> retrieve -> update -> delete."""
        # 1. Create session via chat
        create_response = test_client.post(
            "/api/nanobot/chat",
            json=sample_chat_request
        )
        assert create_response.status_code == 200
        initial_session_id = create_response.json()["session_id"]

        # 2. Retrieve session
        get_response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert get_response.status_code == 200
        initial_data = get_response.json()
        initial_message_count = initial_data["message_count"]

        # 3. Update session (send another message)
        second_request = {
            **sample_chat_request,
            "message": "Second message"
        }
        test_client.post("/api/nanobot/chat", json=second_request)

        # 4. Retrieve updated session
        get_response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert get_response.status_code == 200
        updated_data = get_response.json()
        assert updated_data["id"] == initial_session_id
        assert updated_data["message_count"] > initial_message_count

        # 5. Delete session
        delete_response = test_client.delete(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert delete_response.status_code == 200

        # 6. Verify deletion
        get_response = test_client.get(
            f"/api/nanobot/session/{channel}/{chat_id}"
        )
        assert get_response.status_code == 404

    def test_multiple_sessions_independence(
        self,
        test_client: TestClient
    ):
        """Test that multiple sessions operate independently."""
        # Create two separate sessions
        session1 = {
            "message": "Hello from session 1",
            "channel": "test",
            "chat_id": "session-1",
            "media": None
        }
        session2 = {
            "message": "Hello from session 2",
            "channel": "test",
            "chat_id": "session-2",
            "media": None
        }

        test_client.post("/api/nanobot/chat", json=session1)
        test_client.post("/api/nanobot/chat", json=session2)

        # Verify both exist
        response1 = test_client.get("/api/nanobot/session/test/session-1")
        response2 = test_client.get("/api/nanobot/session/test/session-2")

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Delete one
        test_client.delete("/api/nanobot/session/test/session-1")

        # Verify one is gone, other still exists
        response1 = test_client.get("/api/nanobot/session/test/session-1")
        response2 = test_client.get("/api/nanobot/session/test/session-2")

        assert response1.status_code == 404
        assert response2.status_code == 200