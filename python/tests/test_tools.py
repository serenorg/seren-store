# ABOUTME: Tests for tool registry, schema generation, and tool call parsing.
# ABOUTME: Covers ToolRegistry, create_tool_schema, parse_tool_calls, create_tool_result.
import json
import pytest
from seren_agent.tools import (
    ToolRegistry,
    create_tool_schema,
    create_tool_result,
    parse_tool_calls,
)


class TestCreateToolSchema:
    """Tests for create_tool_schema."""

    def test_basic_schema(self):
        schema = create_tool_schema(
            name="search",
            description="Search the web",
            parameters={"query": {"type": "string"}},
        )

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "search"
        assert schema["function"]["description"] == "Search the web"
        assert "query" in schema["function"]["parameters"]["properties"]

    def test_schema_with_required(self):
        schema = create_tool_schema(
            name="search",
            description="Search",
            parameters={"query": {"type": "string"}},
            required=["query"],
        )

        assert schema["function"]["parameters"]["required"] == ["query"]

    def test_schema_without_required(self):
        schema = create_tool_schema(
            name="search",
            description="Search",
            parameters={"query": {"type": "string"}},
        )

        assert "required" not in schema["function"]["parameters"]


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_and_execute(self):
        registry = ToolRegistry()

        @registry.register("add", "Add two numbers")
        def add(a: int, b: int) -> int:
            return a + b

        result = registry.execute("add", {"a": 2, "b": 3})
        assert result == 5

    def test_get_schemas(self):
        registry = ToolRegistry()

        @registry.register("search", "Search the web")
        def search(query: str) -> dict:
            return {"results": []}

        schemas = registry.get_schemas()
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "search"

    def test_schemas_returns_copy(self):
        registry = ToolRegistry()

        @registry.register("test", "Test tool")
        def test_fn() -> dict:
            return {}

        schemas1 = registry.get_schemas()
        schemas2 = registry.get_schemas()
        assert schemas1 is not schemas2

    def test_has_tool(self):
        registry = ToolRegistry()

        @registry.register("search", "Search")
        def search(query: str) -> dict:
            return {}

        assert registry.has_tool("search") is True
        assert registry.has_tool("nonexistent") is False

    def test_execute_unregistered_raises(self):
        registry = ToolRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.execute("nonexistent", {})

    def test_multiple_tools(self):
        registry = ToolRegistry()

        @registry.register("search", "Search the web")
        def search(query: str) -> dict:
            return {"results": [query]}

        @registry.register("calculate", "Do math")
        def calculate(expression: str) -> dict:
            return {"result": eval(expression)}

        assert registry.execute("search", {"query": "hello"}) == {"results": ["hello"]}
        assert registry.execute("calculate", {"expression": "2+3"}) == {"result": 5}
        assert len(registry.get_schemas()) == 2


class TestParseToolCalls:
    """Tests for parse_tool_calls using mock response objects."""

    def _make_response(self, tool_calls=None):
        """Create a mock OpenAI response object."""

        class MockFunction:
            def __init__(self, name, arguments):
                self.name = name
                self.arguments = arguments

        class MockToolCall:
            def __init__(self, id, name, arguments):
                self.id = id
                self.function = MockFunction(name, json.dumps(arguments))

        class MockMessage:
            def __init__(self, tool_calls):
                self.tool_calls = tool_calls

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockResponse:
            def __init__(self, choices):
                self.choices = choices

        mock_calls = None
        if tool_calls:
            mock_calls = [
                MockToolCall(tc["id"], tc["name"], tc["arguments"])
                for tc in tool_calls
            ]

        return MockResponse([MockChoice(MockMessage(mock_calls))])

    def test_no_tool_calls(self):
        response = self._make_response(tool_calls=None)
        calls = parse_tool_calls(response)
        assert calls == []

    def test_single_tool_call(self):
        response = self._make_response(
            tool_calls=[
                {"id": "call_1", "name": "search", "arguments": {"query": "hello"}}
            ]
        )
        calls = parse_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["id"] == "call_1"
        assert calls[0]["name"] == "search"
        assert calls[0]["arguments"] == {"query": "hello"}

    def test_multiple_tool_calls(self):
        response = self._make_response(
            tool_calls=[
                {"id": "call_1", "name": "search", "arguments": {"query": "a"}},
                {"id": "call_2", "name": "calc", "arguments": {"expr": "1+1"}},
            ]
        )
        calls = parse_tool_calls(response)
        assert len(calls) == 2


class TestCreateToolResult:
    """Tests for create_tool_result."""

    def test_dict_result_serialized(self):
        result = create_tool_result("call_1", {"data": "hello"})
        assert result["role"] == "tool"
        assert result["tool_call_id"] == "call_1"
        assert json.loads(result["content"]) == {"data": "hello"}

    def test_string_result_not_double_serialized(self):
        result = create_tool_result("call_1", "plain text")
        assert result["content"] == "plain text"

    def test_list_result_serialized(self):
        result = create_tool_result("call_1", [1, 2, 3])
        assert json.loads(result["content"]) == [1, 2, 3]
