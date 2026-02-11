# ABOUTME: Tool registry and schema helpers for OpenAI-style function calling.
# ABOUTME: Provides ToolRegistry for registering, executing, and schema-exporting tools.
"""Tool calling helpers for Seren agents.

Utilities for implementing tool-using agents with function calling support.
"""

import json
from typing import Any, Callable, Dict, List, Optional


def create_tool_schema(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    required: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create an OpenAI-compatible tool schema.

    Args:
        name: Tool function name
        description: What the tool does
        parameters: JSON Schema for parameters
        required: List of required parameter names

    Returns:
        Tool schema dict for use with chat completions

    Example:
        search_tool = create_tool_schema(
            name="web_search",
            description="Search the web for information",
            parameters={
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results"}
            },
            required=["query"]
        )
    """
    schema = {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": parameters,
            },
        },
    }

    if required:
        schema["function"]["parameters"]["required"] = required

    return schema


def parse_tool_calls(response) -> List[Dict[str, Any]]:
    """Parse tool calls from an OpenAI chat completion response.

    Args:
        response: OpenAI ChatCompletion response object

    Returns:
        List of parsed tool calls with name and arguments

    Example:
        response = client.chat.completions.create(...)
        tool_calls = parse_tool_calls(response)
        for call in tool_calls:
            result = execute_tool(call["name"], call["arguments"])
    """
    calls = []
    message = response.choices[0].message

    if hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:
            calls.append(
                {
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments),
                }
            )

    return calls


def create_tool_result(tool_call_id: str, result: Any) -> Dict[str, Any]:
    """Create a tool result message for the conversation.

    Args:
        tool_call_id: The ID from the original tool call
        result: The result to return (will be JSON serialized)

    Returns:
        Message dict to append to conversation

    Example:
        messages.append(create_tool_result(
            call["id"],
            {"data": search_results}
        ))
    """
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": json.dumps(result) if not isinstance(result, str) else result,
    }


class ToolRegistry:
    """Registry for managing tools in an agent.

    Provides a clean way to register and execute tools by name.

    Example:
        registry = ToolRegistry()

        @registry.register("search", "Search the web")
        def search(query: str) -> dict:
            return {"results": [...]}

        # Later, execute by name
        result = registry.execute("search", {"query": "hello"})
    """

    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        required: Optional[List[str]] = None,
    ) -> Callable:
        """Decorator to register a tool function.

        Args:
            name: Tool name for function calling
            description: What the tool does
            parameters: JSON Schema for parameters (auto-generated if None)
            required: Required parameters

        Returns:
            Decorator function
        """

        def decorator(func: Callable) -> Callable:
            self._tools[name] = func

            # Auto-generate simple schema if not provided
            params = parameters or {}
            schema = create_tool_schema(name, description, params, required)
            self._schemas.append(schema)

            return func

        return decorator

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a registered tool by name.

        Args:
            name: Tool name
            arguments: Arguments dict

        Returns:
            Tool result

        Raises:
            KeyError: If tool not registered
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name](**arguments)

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Get all tool schemas for use with chat completions."""
        return self._schemas.copy()

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
