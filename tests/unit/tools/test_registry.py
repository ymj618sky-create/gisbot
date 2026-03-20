"""Tests for Tool Registry."""

import pytest
from core.tools.base import Tool
from core.tools.registry import ToolRegistry


class SimpleTool(Tool):
    @property
    def name(self) -> str:
        return "simple"

    @property
    def description(self) -> str:
        return "Simple test tool"

    @property
    def parameters(self) -> dict:
        return {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> str:
        return "simple result"


def test_tool_registration():
    """Test registering a tool"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    assert tool.name in registry.tool_names


def test_tool_get():
    """Test getting a registered tool"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    retrieved = registry.get("simple")
    assert retrieved is tool


def test_tool_unregister():
    """Test unregistering a tool"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    registry.unregister("simple")
    assert "simple" not in registry.tool_names


def test_tool_has():
    """Test checking if tool exists"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    assert registry.has("simple")
    assert not registry.has("nonexistent")


def test_get_definitions():
    """Test getting all tool definitions"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    definitions = registry.get_definitions()
    assert len(definitions) == 1
    assert definitions[0]["function"]["name"] == "simple"


@pytest.mark.asyncio
async def test_execute_tool():
    """Test executing a tool"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    result = await registry.execute("simple", {})
    assert result == "simple result"


@pytest.mark.asyncio
async def test_execute_nonexistent_tool():
    """Test executing a tool that doesn't exist"""
    registry = ToolRegistry()
    result = await registry.execute("nonexistent", {})
    assert "not found" in result.lower()


@pytest.mark.asyncio
async def test_execute_with_invalid_params():
    """Test executing a tool with invalid parameters"""

    class TestTool(Tool):
        @property
        def name(self) -> str:
            return "test"

        @property
        def description(self) -> str:
            return "Test tool"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"executed with {kwargs['value']}"

    registry = ToolRegistry()
    tool = TestTool()
    registry.register(tool)
    result = await registry.execute("test", {})
    assert "invalid parameters" in result.lower()


def test_registry_length():
    """Test getting registry length"""
    registry = ToolRegistry()
    assert len(registry) == 0
    registry.register(SimpleTool())
    assert len(registry) == 1


def test_registry_contains():
    """Test 'in' operator on registry"""
    registry = ToolRegistry()
    tool = SimpleTool()
    registry.register(tool)
    assert "simple" in registry
    assert "other" not in registry


@pytest.mark.asyncio
async def test_execute_with_type_casting():
    """Test that parameters are type cast before validation"""

    class IntTool(Tool):
        @property
        def name(self) -> str:
            return "int_tool"

        @property
        def description(self) -> str:
            return "Tool with integer parameter"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"value": {"type": "integer"}},
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"value type: {type(kwargs['value']).__name__}"

    registry = ToolRegistry()
    tool = IntTool()
    registry.register(tool)
    result = await registry.execute("int_tool", {"value": "123"})
    assert "int" in result


@pytest.mark.asyncio
async def test_execute_tool_with_exception():
    """Test execution error is caught and returned"""

    class FailingTool(Tool):
        @property
        def name(self) -> str:
            return "failing"

        @property
        def description(self) -> str:
            return "Tool that always fails"

        @property
        def parameters(self) -> dict:
            return {"type": "object", "properties": {}}

        async def execute(self, **kwargs) -> str:
            raise ValueError("Tool execution failed")

    registry = ToolRegistry()
    tool = FailingTool()
    registry.register(tool)
    result = await registry.execute("failing", {})
    assert "Error" in result
    assert "Tool execution failed" in result


def test_register_same_name_twice():
    """Test registering tool with same name overwrites"""

    class ToolV1(Tool):
        @property
        def name(self) -> str:
            return "same_name"

        @property
        def description(self) -> str:
            return "Version 1"

        @property
        def parameters(self) -> dict:
            return {"type": "object", "properties": {}}

        async def execute(self, **kwargs) -> str:
            return "v1"

    class ToolV2(Tool):
        @property
        def name(self) -> str:
            return "same_name"

        @property
        def description(self) -> str:
            return "Version 2"

        @property
        def parameters(self) -> dict:
            return {"type": "object", "properties": {}}

        async def execute(self, **kwargs) -> str:
            return "v2"

    registry = ToolRegistry()
    registry.register(ToolV1())
    registry.register(ToolV2())

    tool = registry.get("same_name")
    assert tool.description == "Version 2"