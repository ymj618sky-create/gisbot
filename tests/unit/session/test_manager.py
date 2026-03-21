"""Tests for Session Manager."""

import pytest
from pathlib import Path
import tempfile
import json
from session.manager import SessionManager


def test_create_session():
    """Test creating a new session"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        session = manager.create_session("web", "chat123", sender_id="user123")

        assert session.id is not None
        assert session.channel == "web"
        assert session.chat_id == "chat123"
        assert session.sender_id == "user123"


def test_get_session():
    """Test retrieving an existing session"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        created = manager.create_session("web", "chat123", sender_id="user123")

        retrieved = manager.get_session(created.id)

        assert retrieved.id == created.id
        assert retrieved.channel == created.channel
        assert retrieved.chat_id == created.chat_id


def test_get_session_not_found():
    """Test retrieving non-existent session"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))

        session = manager.get_session("non-existent-id")

        assert session is None


def test_save_session():
    """Test saving session updates"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        session = manager.create_session("web", "chat123", sender_id="user123")

        # Add a message
        session.add_message({"role": "user", "content": "Hello"})

        # Save
        manager.save_session(session)

        # Retrieve and verify
        retrieved = manager.get_session(session.id)

        assert len(retrieved.messages) == 1
        assert retrieved.messages[0]["content"] == "Hello"


def test_delete_session():
    """Test deleting a session"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        session = manager.create_session("web", "chat123", sender_id="user123")

        manager.delete_session(session.id)

        retrieved = manager.get_session(session.id)

        assert retrieved is None


def test_list_sessions():
    """Test listing all sessions"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))

        # Create multiple sessions
        session1 = manager.create_session("web", "chat1", sender_id="user1")
        session2 = manager.create_session("web", "chat2", sender_id="user2")

        sessions = manager.list_sessions()

        assert len(sessions) == 2
        session_ids = [s.id for s in sessions]
        assert session1.id in session_ids
        assert session2.id in session_ids


def test_session_memory_window():
    """Test session memory window trimming"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        session = manager.create_session("web", "chat123", sender_id="user123", memory_window=5)

        # Add 15 messages to trigger trimming (threshold is memory_window * 2 = 10)
        for i in range(15):
            session.add_message({"role": "user", "content": f"Message {i}"})

        # Memory window should trim to last 5 messages
        manager.save_session(session)

        retrieved = manager.get_session(session.id)

        # Messages should be trimmed, and earliest should be from later indices
        assert len(retrieved.messages) <= 10  # Should be trimmed


def test_get_by_channel_and_chat_id():
    """Test getting session by channel and chat ID"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        session = manager.create_session("web", "chat123", sender_id="user123")

        retrieved = manager.get_by_channel_chat_id("web", "chat123")

        assert retrieved.id == session.id


def test_get_by_channel_and_chat_id_not_found():
    """Test getting non-existent session by channel and chat ID"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))

        session = manager.get_by_channel_chat_id("web", "nonexistent")

        assert session is None


def test_session_metadata():
    """Test storing and retrieving session metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SessionManager(data_dir=Path(tmpdir))
        session = manager.create_session("web", "chat123", sender_id="user123")

        session.set_metadata("key1", "value1")
        session.set_metadata("key2", 123)

        manager.save_session(session)

        retrieved = manager.get_session(session.id)

        assert retrieved.get_metadata("key1") == "value1"
        assert retrieved.get_metadata("key2") == 123
        assert retrieved.get_metadata("nonexistent") is None