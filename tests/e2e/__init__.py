"""
End-to-End (E2E) Tests for GIS Agent API

This package contains integration tests that verify the complete API functionality
from HTTP request to response, including:

- Chat flow and multi-turn conversations
- Session management (create, retrieve, update, delete)
- Tool and skills listing
- Tool execution through chat interface

These tests use FastAPI's TestClient and mock LLM providers to test
the complete API without external dependencies.
"""