"""Type definitions for Seren agents.

These types provide structure and documentation for agent inputs/outputs.
They're optional but recommended for better code quality and documentation.
"""

from typing import Any, Dict, List, Optional, TypedDict, Union


class AgentInput(TypedDict, total=False):
    """Base type for agent input.

    All agent inputs are JSON-serializable dictionaries. You can extend
    this type for your specific agent's input schema.

    Example:
        class WebResearchInput(AgentInput):
            query: str
            max_results: int
            include_sources: bool
    """

    pass


class AgentOutput(TypedDict, total=False):
    """Base type for agent output.

    All agent outputs must be JSON-serializable dictionaries. You can extend
    this type for your specific agent's output schema.

    Example:
        class WebResearchOutput(AgentOutput):
            summary: str
            sources: List[str]
            confidence: float
    """

    pass


# Common field types for agent I/O
JsonValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JsonDict = Dict[str, JsonValue]


class ErrorOutput(TypedDict):
    """Standard error output format.

    Use this when your agent encounters an error that should be
    communicated to the caller.

    Example:
        if not input.get("query"):
            return ErrorOutput(
                error="missing_input",
                message="The 'query' field is required"
            )
    """

    error: str
    message: str
    details: Optional[Dict[str, Any]]


class SuccessOutput(TypedDict, total=False):
    """Standard success output format.

    A minimal success response structure. Extend for your specific needs.
    """

    success: bool
    data: Any
    metadata: Optional[Dict[str, Any]]
