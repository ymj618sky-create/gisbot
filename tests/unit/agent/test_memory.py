"""Tests for Memory Store."""

import pytest
from pathlib import Path
from core.agent.memory import MemoryStore
import tempfile


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace


def test_read_long_term_empty(temp_workspace):
    """Test reading long-term memory when file doesn't exist"""
    store = MemoryStore(temp_workspace)
    content = store.read_long_term()
    assert content == ""


def test_write_long_term(temp_workspace):
    """Test writing long-term memory"""
    store = MemoryStore(temp_workspace)
    store.write_long_term("Test memory content")
    content = store.read_long_term()
    assert content == "Test memory content"


def test_append_history(temp_workspace):
    """Test appending to history"""
    store = MemoryStore(temp_workspace)
    store.append_history("[2026-03-19 10:00] Test entry")
    content = (temp_workspace / "memory" / "HISTORY.md").read_text()
    assert "[2026-03-19 10:00] Test entry" in content


def test_get_memory_context_empty(temp_workspace):
    """Test getting memory context when empty"""
    store = MemoryStore(temp_workspace)
    context = store.get_memory_context()
    assert context == ""


def test_get_memory_context_with_content(temp_workspace):
    """Test getting memory context with content"""
    store = MemoryStore(temp_workspace)
    store.write_long_term("# Important Fact\nThis is a fact that matters.")
    context = store.get_memory_context()
    assert "## Long-term Memory" in context
    assert "Important Fact" in context


def test_memory_directory_created(temp_workspace):
    """Test that memory directory is created automatically"""
    memory_dir = temp_workspace / "memory"
    assert not memory_dir.exists()

    store = MemoryStore(temp_workspace)
    assert memory_dir.exists()


def test_append_multiple_history_entries(temp_workspace):
    """Test appending multiple history entries"""
    store = MemoryStore(temp_workspace)
    store.append_history("[2026-03-19 10:00] Entry 1")
    store.append_history("[2026-03-19 10:05] Entry 2")
    store.append_history("[2026-03-19 10:10] Entry 3")

    content = (temp_workspace / "memory" / "HISTORY.md").read_text()
    assert "Entry 1" in content
    assert "Entry 2" in content
    assert "Entry 3" in content


def test_overwrite_long_term(temp_workspace):
    """Test overwriting long-term memory"""
    store = MemoryStore(temp_workspace)
    store.write_long_term("Original content")
    store.write_long_term("New content")
    content = store.read_long_term()
    assert content == "New content"
    assert "Original" not in content


def test_append_history_with_newline_handling(temp_workspace):
    """Test that append_history handles newlines correctly"""
    store = MemoryStore(temp_workspace)
    store.append_history("[2026-03-19 10:00] Entry 1")
    store.append_history("[2026-03-19 10:05] Entry 2")

    content = (temp_workspace / "memory" / "HISTORY.md").read_text()
    # Should have blank lines between entries
    assert "\n\n" in content