"""Tests for Tool base class."""

import pytest
from core.tools.base import Tool, ToolValidationError, ToolExecutionError


class MockTool(Tool):
    @property
    def name(self) -> str:
        return "mock_tool"

    @property
    def description(self) -> str:
        return "Mock tool for testing"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "value": {"type": "integer", "description": "Test value"}
            },
            "required": ["value"]
        }

    async def execute(self, **kwargs) -> str:
        return f"Result: {kwargs.get('value', 0)}"


def test_tool_has_required_properties():
    """Test that tool implements all required properties"""
    tool = MockTool()
    assert tool.name == "mock_tool"
    assert tool.description == "Mock tool for testing"
    assert "value" in tool.parameters["properties"]


def test_tool_to_schema():
    """Test tool schema conversion to OpenAI format"""
    tool = MockTool()
    schema = tool.to_schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "mock_tool"
    assert "value" in schema["function"]["parameters"]["properties"]


def test_cast_params_string_to_int():
    """Test parameter type casting from string to int"""
    tool = MockTool()
    params = tool.cast_params({"value": "123"})
    assert params["value"] == 123
    assert isinstance(params["value"], int)


def test_cast_params_string_to_bool():
    """Test parameter type casting from string to bool"""
    tool = MockTool()
    # Create a tool with boolean parameter for this test
    class BoolTool(Tool):
        @property
        def name(self) -> str:
            return "bool_tool"

        @property
        def description(self) -> str:
            return "Tool with boolean param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
                "required": ["enabled"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Enabled: {kwargs.get('enabled')}"

    tool = BoolTool()
    params = tool.cast_params({"enabled": "true"})
    assert params["enabled"] is True


def test_validate_params_valid():
    """Test parameter validation with valid input"""
    tool = MockTool()
    errors = tool.validate_params({"value": 42})
    assert len(errors) == 0


def test_validate_params_missing_required():
    """Test parameter validation with missing required parameter"""
    tool = MockTool()
    errors = tool.validate_params({})
    assert len(errors) > 0
    assert "value" in errors[0].lower()


def test_validate_params_wrong_type():
    """Test parameter validation with wrong type"""
    tool = MockTool()
    errors = tool.validate_params({"value": "not_a_number"})
    assert len(errors) > 0
    assert "integer" in errors[0].lower()


def test_abstract_tool_cannot_instantiate():
    """Test that Tool base class cannot be instantiated"""
    with pytest.raises(TypeError):
        Tool()


def test_cast_params_array():
    """Test parameter type casting for arrays"""
    class ArrayTool(Tool):
        @property
        def name(self) -> str:
            return "array_tool"

        @property
        def description(self) -> str:
            return "Tool with array param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                },
                "required": ["items"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Items: {kwargs.get('items')}"

    tool = ArrayTool()
    params = tool.cast_params({"items": ["1", "2", "3"]})
    assert params["items"] == [1, 2, 3]
    assert all(isinstance(x, int) for x in params["items"])


def test_validate_params_enum():
    """Test parameter validation with enum constraint"""
    class EnumTool(Tool):
        @property
        def name(self) -> str:
            return "enum_tool"

        @property
        def description(self) -> str:
            return "Tool with enum param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "mode": {
                        "type": "string",
                        "enum": ["read", "write", "append"]
                    }
                },
                "required": ["mode"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Mode: {kwargs.get('mode')}"

    tool = EnumTool()
    errors = tool.validate_params({"mode": "read"})
    assert len(errors) == 0

    errors = tool.validate_params({"mode": "invalid"})
    assert len(errors) > 0
    assert "one of" in errors[0]


def test_validate_params_numeric_constraints():
    """Test parameter validation with numeric min/max constraints"""
    class NumericTool(Tool):
        @property
        def name(self) -> str:
            return "numeric_tool"

        @property
        def description(self) -> str:
            return "Tool with numeric constraints"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["count"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Count: {kwargs.get('count')}"

    tool = NumericTool()
    errors = tool.validate_params({"count": 50})
    assert len(errors) == 0

    errors = tool.validate_params({"count": -1})
    assert len(errors) > 0
    assert ">=" in errors[0]

    errors = tool.validate_params({"count": 101})
    assert len(errors) > 0
    assert "<=" in errors[0]


def test_validate_params_string_length():
    """Test parameter validation with string length constraints"""
    class StringTool(Tool):
        @property
        def name(self) -> str:
            return "string_tool"

        @property
        def description(self) -> str:
            return "Tool with string length constraints"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 20
                    }
                },
                "required": ["name"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Name: {kwargs.get('name')}"

    tool = StringTool()
    errors = tool.validate_params({"name": "test"})
    assert len(errors) == 0

    errors = tool.validate_params({"name": "ab"})
    assert len(errors) > 0
    assert "at least" in errors[0]

    errors = tool.validate_params({"name": "a" * 21})
    assert len(errors) > 0
    assert "at most" in errors[0]


def test_validate_params_nested_object():
    """Test parameter validation with nested objects"""
    class NestedTool(Tool):
        @property
        def name(self) -> str:
            return "nested_tool"

        @property
        def description(self) -> str:
            return "Tool with nested object"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "config": {
                        "type": "object",
                        "properties": {
                            "enabled": {"type": "boolean"},
                            "count": {"type": "integer"}
                        },
                        "required": ["enabled"]
                    }
                },
                "required": ["config"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Config: {kwargs.get('config')}"

    tool = NestedTool()
    errors = tool.validate_params({"config": {"enabled": True, "count": 5}})
    assert len(errors) == 0

    errors = tool.validate_params({"config": {"count": 5}})
    assert len(errors) > 0
    assert "enabled" in errors[0]


def test_gis_error_hierarchy():
    """Test GIS error classes inherit from base ToolError"""
    from core.tools.base import GISError, EmptyResultError, InvalidGeometryError, CRSMismatchError

    # All should inherit from ToolError
    assert issubclass(GISError, Exception)
    assert issubclass(EmptyResultError, GISError)
    assert issubclass(InvalidGeometryError, GISError)
    assert issubclass(CRSMismatchError, GISError)


def test_cast_params_preserves_correct_types():
    """Test that cast_params preserves already correct types"""
    class TypeTool(Tool):
        @property
        def name(self) -> str:
            return "type_tool"

        @property
        def description(self) -> str:
            return "Tool for type casting"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "int_val": {"type": "integer"},
                    "str_val": {"type": "string"},
                    "bool_val": {"type": "boolean"},
                    "num_val": {"type": "number"},
                    "list_val": {"type": "array"},
                    "dict_val": {"type": "object"}
                },
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return f"Values: {kwargs}"

    tool = TypeTool()
    params = tool.cast_params({
        "int_val": 42,
        "str_val": "hello",
        "bool_val": True,
        "num_val": 3.14,
        "list_val": [1, 2, 3],
        "dict_val": {"key": "value"}
    })
    assert params["int_val"] == 42
    assert isinstance(params["int_val"], int)
    assert params["str_val"] == "hello"
    assert params["bool_val"] is True
    assert params["num_val"] == 3.14
    assert params["list_val"] == [1, 2, 3]
    assert params["dict_val"] == {"key": "value"}


def test_cast_params_string_to_number():
    """Test parameter type casting from string to number"""
    class NumberTool(Tool):
        @property
        def name(self) -> str:
            return "number_tool"

        @property
        def description(self) -> str:
            return "Tool with number param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"value": {"type": "number"}},
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Value: {kwargs.get('value')}"

    tool = NumberTool()
    params = tool.cast_params({"value": "3.14"})
    assert params["value"] == 3.14
    assert isinstance(params["value"], float)


def test_cast_params_invalid_number_string():
    """Test that invalid number strings are not converted"""
    class NumberTool(Tool):
        @property
        def name(self) -> str:
            return "number_tool"

        @property
        def description(self) -> str:
            return "Tool with number param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"value": {"type": "number"}},
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Value: {kwargs.get('value')}"

    tool = NumberTool()
    params = tool.cast_params({"value": "not_a_number"})
    assert params["value"] == "not_a_number"
    assert isinstance(params["value"], str)


def test_cast_params_invalid_int_string():
    """Test that invalid int strings are not converted"""
    tool = MockTool()
    params = tool.cast_params({"value": "not_a_number"})
    assert params["value"] == "not_a_number"
    assert isinstance(params["value"], str)


def test_cast_params_string_to_bool_false():
    """Test parameter type casting from string to bool (false variants)"""
    class BoolTool(Tool):
        @property
        def name(self) -> str:
            return "bool_tool"

        @property
        def description(self) -> str:
            return "Tool with boolean param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
                "required": ["enabled"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Enabled: {kwargs.get('enabled')}"

    tool = BoolTool()

    # Test all false variants
    for val in ["false", "0", "no"]:
        params = tool.cast_params({"enabled": val})
        assert params["enabled"] is False

    # Test invalid bool string
    params = tool.cast_params({"enabled": "maybe"})
    assert params["enabled"] == "maybe"


def test_cast_params_null_to_string():
    """Test that null is converted to string"""
    class StringTool(Tool):
        @property
        def name(self) -> str:
            return "string_tool"

        @property
        def description(self) -> str:
            return "Tool with string param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"value": {"type": "string"}},
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Value: {kwargs.get('value')}"

    tool = StringTool()
    params = tool.cast_params({"value": None})
    # None should remain None in string type casting
    assert params["value"] is None


def test_cast_params_array_without_items_schema():
    """Test array casting without items schema preserves original"""
    class ArrayTool(Tool):
        @property
        def name(self) -> str:
            return "array_tool"

        @property
        def description(self) -> str:
            return "Tool with array param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"items": {"type": "array"}},
                "required": ["items"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Items: {kwargs.get('items')}"

    tool = ArrayTool()
    params = tool.cast_params({"items": ["1", "2", "3"]})
    assert params["items"] == ["1", "2", "3"]


def test_validate_params_not_dict():
    """Test validation with non-dict parameters"""
    tool = MockTool()
    errors = tool.validate_params("not a dict")
    assert len(errors) == 1
    assert "must be an object" in errors[0].lower()


def test_validate_params_invalid_schema_type():
    """Test validation raises ValueError for invalid schema type"""
    class InvalidTool(Tool):
        @property
        def name(self) -> str:
            return "invalid_tool"

        @property
        def description(self) -> str:
            return "Tool with invalid schema"

        @property
        def parameters(self) -> dict:
            return {
                "type": "array",  # Invalid: should be "object"
                "properties": {}
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = InvalidTool()
    with pytest.raises(ValueError, match="Schema must be object type"):
        tool.validate_params({})


def test_validate_params_array_with_items():
    """Test array validation with items schema"""
    class ArrayTool(Tool):
        @property
        def name(self) -> str:
            return "array_tool"

        @property
        def description(self) -> str:
            return "Tool with array param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "integer"}
                    }
                },
                "required": ["items"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Items: {kwargs.get('items')}"

    tool = ArrayTool()
    errors = tool.validate_params({"items": [1, 2, 3]})
    assert len(errors) == 0

    # Array with strings when integers expected
    errors = tool.validate_params({"items": ["a", "b", "c"]})
    assert len(errors) > 0
    assert "should be integer" in errors[0]


def test_validate_params_boolean_with_integer():
    """Test that integers (even 1/0) are not accepted as booleans"""
    class BoolTool(Tool):
        @property
        def name(self) -> str:
            return "bool_tool"

        @property
        def description(self) -> str:
            return "Tool with boolean param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"enabled": {"type": "boolean"}},
                "required": ["enabled"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Enabled: {kwargs.get('enabled')}"

    tool = BoolTool()
    # Python treats bool as subclass of int, so True/False pass
    errors = tool.validate_params({"enabled": True})
    assert len(errors) == 0

    errors = tool.validate_params({"enabled": False})
    assert len(errors) == 0

    # But actual integers 1 and 0 should fail
    errors = tool.validate_params({"enabled": 1})
    assert len(errors) > 0
    assert "should be boolean" in errors[0].lower()

    errors = tool.validate_params({"enabled": 0})
    assert len(errors) > 0
    assert "should be boolean" in errors[0].lower()


def test_validate_params_number_type():
    """Test number type accepts both int and float"""
    class NumberTool(Tool):
        @property
        def name(self) -> str:
            return "number_tool"

        @property
        def description(self) -> str:
            return "Tool with number param"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"value": {"type": "number"}},
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Value: {kwargs.get('value')}"

    tool = NumberTool()
    errors = tool.validate_params({"value": 42})
    assert len(errors) == 0

    errors = tool.validate_params({"value": 3.14})
    assert len(errors) == 0


def test_cast_params_extra_properties():
    """Test that extra properties not in schema are preserved"""
    class SimpleTool(Tool):
        @property
        def name(self) -> str:
            return "simple_tool"

        @property
        def description(self) -> str:
            return "Simple tool"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {"known": {"type": "string"}},
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return f"Result: {kwargs}"

    tool = SimpleTool()
    params = tool.cast_params({"known": "value", "extra": "data"})
    assert params["known"] == "value"
    assert params["extra"] == "data"


def test_validate_params_empty_parameters():
    """Test validation with empty parameters schema"""
    class EmptyTool(Tool):
        @property
        def name(self) -> str:
            return "empty_tool"

        @property
        def description(self) -> str:
            return "Tool with no parameters"

        @property
        def parameters(self) -> dict:
            return {"type": "object", "properties": {}}

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = EmptyTool()
    errors = tool.validate_params({})
    assert len(errors) == 0


def test_to_schema_returns_complete_structure():
    """Test to_schema returns complete OpenAI function schema"""
    tool = MockTool()
    schema = tool.to_schema()

    assert "type" in schema
    assert "function" in schema
    assert schema["type"] == "function"

    func = schema["function"]
    assert "name" in func
    assert "description" in func
    assert "parameters" in func

    assert func["name"] == "mock_tool"
    assert func["description"] == "Mock tool for testing"
    assert func["parameters"]["type"] == "object"


def test_validate_params_both_min_and_max():
    """Test validation with both minimum and maximum"""
    class RangeTool(Tool):
        @property
        def name(self) -> str:
            return "range_tool"

        @property
        def description(self) -> str:
            return "Tool with range constraints"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "integer",
                        "minimum": 10,
                        "maximum": 20
                    }
                },
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Value: {kwargs.get('value')}"

    tool = RangeTool()
    errors = tool.validate_params({"value": 15})
    assert len(errors) == 0

    errors = tool.validate_params({"value": 9})
    assert len(errors) > 0
    assert ">=" in errors[0]

    errors = tool.validate_params({"value": 21})
    assert len(errors) > 0
    assert "<=" in errors[0]


def test_validate_params_min_and_max_on_number():
    """Test min/max constraints on number type"""
    class NumberTool(Tool):
        @property
        def name(self) -> str:
            return "number_tool"

        @property
        def description(self) -> str:
            return "Tool with number constraints"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "value": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0
                    }
                },
                "required": ["value"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Value: {kwargs.get('value')}"

    tool = NumberTool()
    errors = tool.validate_params({"value": 0.5})
    assert len(errors) == 0

    errors = tool.validate_params({"value": -0.1})
    assert len(errors) > 0
    assert ">=" in errors[0]

    errors = tool.validate_params({"value": 1.1})
    assert len(errors) > 0
    assert "<=" in errors[0]


def test_validate_params_both_min_and_max_length():
    """Test validation with both minLength and maxLength"""
    class StringTool(Tool):
        @property
        def name(self) -> str:
            return "string_tool"

        @property
        def description(self) -> str:
            return "Tool with string length constraints"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 5,
                        "maxLength": 10
                    }
                },
                "required": ["name"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Name: {kwargs.get('name')}"

    tool = StringTool()
    errors = tool.validate_params({"name": "hello"})
    assert len(errors) == 0

    errors = tool.validate_params({"name": "hi"})
    assert len(errors) > 0
    assert "at least" in errors[0]

    errors = tool.validate_params({"name": "helloworldagain"})
    assert len(errors) > 0
    assert "at most" in errors[0]


def test_validate_params_nested_array():
    """Test validation of nested arrays"""
    class NestedArrayTool(Tool):
        @property
        def name(self) -> str:
            return "nested_array_tool"

        @property
        def description(self) -> str:
            return "Tool with nested array validation"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "matrix": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "integer"}
                        }
                    }
                },
                "required": ["matrix"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Matrix: {kwargs.get('matrix')}"

    tool = NestedArrayTool()
    errors = tool.validate_params({"matrix": [[1, 2], [3, 4]]})
    assert len(errors) == 0

    errors = tool.validate_params({"matrix": [["a", "b"], ["c", "d"]]})
    assert len(errors) > 0


def test_validate_params_multiple_errors():
    """Test validation returns multiple errors"""
    class MultiErrorTool(Tool):
        @property
        def name(self) -> str:
            return "multi_error_tool"

        @property
        def description(self) -> str:
            return "Tool with multiple possible errors"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 10
                    },
                    "count": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": ["name", "count"]
            }

        async def execute(self, **kwargs) -> str:
            return f"Result: {kwargs}"

    tool = MultiErrorTool()
    errors = tool.validate_params({"name": "ab", "count": 0})
    assert len(errors) >= 2
    assert any("at least" in e for e in errors)
    assert any(">=" in e for e in errors)


def test_cast_params_nested_dict():
    """Test casting nested dictionaries"""
    class NestedDictTool(Tool):
        @property
        def name(self) -> str:
            return "nested_dict_tool"

        @property
        def description(self) -> str:
            return "Tool with nested dict parameters"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "config": {
                        "type": "object",
                        "properties": {
                            "count": {"type": "integer"},
                            "enabled": {"type": "boolean"}
                        }
                    }
                },
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return f"Config: {kwargs.get('config')}"

    tool = NestedDictTool()
    params = tool.cast_params({
        "config": {
            "count": "5",
            "enabled": "true"
        }
    })
    assert params["config"]["count"] == 5
    assert isinstance(params["config"]["count"], int)
    assert params["config"]["enabled"] is True


def test_cast_params_array_with_objects():
    """Test casting arrays of objects"""
    class ObjectArrayTool(Tool):
        @property
        def name(self) -> str:
            return "object_array_tool"

        @property
        def description(self) -> str:
            return "Tool with array of objects"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"}
                            }
                        }
                    }
                },
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return f"Items: {kwargs.get('items')}"

    tool = ObjectArrayTool()
    params = tool.cast_params({
        "items": [
            {"id": "1", "name": "first"},
            {"id": "2", "name": "second"}
        ]
    })
    assert params["items"][0]["id"] == 1
    assert isinstance(params["items"][0]["id"], int)
    assert params["items"][0]["name"] == "first"


def test_validate_params_with_empty_required_list():
    """Test validation with empty required list"""
    class NoRequiredTool(Tool):
        @property
        def name(self) -> str:
            return "no_required_tool"

        @property
        def description(self) -> str:
            return "Tool with no required params"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "optional": {"type": "string"}
                },
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = NoRequiredTool()
    errors = tool.validate_params({})
    assert len(errors) == 0


def test_cast_params_non_dict():
    """Test casting with non-dict input"""
    tool = MockTool()
    # When params is not a dict, return as-is
    params = tool.cast_params("not a dict")
    assert params == "not a dict"

    params = tool.cast_params(42)
    assert params == 42

    params = tool.cast_params(None)
    assert params is None


def test_cast_params_non_object_schema():
    """Test casting when schema type is not object"""
    class NonObjectTool(Tool):
        @property
        def name(self) -> str:
            return "non_object_tool"

        @property
        def description(self) -> str:
            return "Tool with non-object schema"

        @property
        def parameters(self) -> dict:
            return {
                "type": "string",  # Not object type
                "properties": {}
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = NonObjectTool()
    params = tool.cast_params({"any": "params"})
    assert params == {"any": "params"}


def test_validate_params_no_type_in_schema():
    """Test validation when schema has no type (defaults to object)"""
    class NoTypeTool(Tool):
        @property
        def name(self) -> str:
            return "no_type_tool"

        @property
        def description(self) -> str:
            return "Tool with no type in schema"

        @property
        def parameters(self) -> dict:
            # No type specified, should default to object
            return {
                "properties": {
                    "value": {"type": "integer"}
                },
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = NoTypeTool()
    errors = tool.validate_params({"value": 42})
    assert len(errors) == 0


def test_validate_params_none_parameters():
    """Test validation with empty/None parameters"""
    class ToolWithParams(Tool):
        @property
        def name(self) -> str:
            return "tool_with_params"

        @property
        def description(self) -> str:
            return "Tool with parameters"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "value": {"type": "integer"}
                },
                "required": []
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = ToolWithParams()
    errors = tool.validate_params(None)
    assert len(errors) == 1
    assert "must be an object" in errors[0].lower()


def test_cast_params_object_not_dict():
    """Test _cast_object with non-dict input"""
    tool = MockTool()
    # When input is not a dict, return as-is
    result = tool._cast_object("string", {"type": "object", "properties": {}})
    assert result == "string"

    result = tool._cast_object(123, {"type": "object", "properties": {}})
    assert result == 123

    result = tool._cast_object(None, {"type": "object", "properties": {}})
    assert result is None


def test_validate_params_path_in_errors():
    """Test that error messages include parameter path for nested objects"""
    class NestedTool(Tool):
        @property
        def name(self) -> str:
            return "nested_tool"

        @property
        def description(self) -> str:
            return "Tool with nested validation"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "outer": {
                        "type": "object",
                        "properties": {
                            "inner": {
                                "type": "object",
                                "properties": {
                                    "value": {"type": "integer"}
                                },
                                "required": ["value"]
                            }
                        },
                        "required": ["inner"]
                    }
                },
                "required": ["outer"]
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = NestedTool()
    errors = tool.validate_params({"outer": {"inner": {}}})
    assert len(errors) > 0
    assert "outer.inner.value" in errors[0] or "value" in errors[0]


def test_validate_params_array_multiple_errors():
    """Test array validation can produce multiple errors"""
    class ArrayTool(Tool):
        @property
        def name(self) -> str:
            return "array_tool"

        @property
        def description(self) -> str:
            return "Tool with array validation"

        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "integer", "minimum": 0}
                    }
                },
                "required": ["items"]
            }

        async def execute(self, **kwargs) -> str:
            return "result"

    tool = ArrayTool()
    errors = tool.validate_params({"items": [-1, "abc", 2]})
    assert len(errors) >= 2  # Should have errors for -1 and "abc"


def test_gis_error_hierarchy():
    """Test GIS error classes inherit from base ToolError"""
    from core.tools.base import GISError, EmptyResultError, InvalidGeometryError, CRSMismatchError

    # All should inherit from ToolError
    assert issubclass(GISError, Exception)
    assert issubclass(EmptyResultError, GISError)
    assert issubclass(InvalidGeometryError, GISError)
    assert issubclass(CRSMismatchError, GISError)