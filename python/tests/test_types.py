# ABOUTME: Tests for type definitions and TypedDict contracts.
# ABOUTME: Verifies AgentInput, AgentOutput, ErrorOutput, SuccessOutput behave correctly.
from seren_agent.types import (
    AgentInput,
    AgentOutput,
    ErrorOutput,
    SuccessOutput,
    JsonValue,
    JsonDict,
)


class TestAgentInput:
    """Tests for AgentInput TypedDict."""

    def test_can_create_empty(self):
        inp: AgentInput = {}
        assert isinstance(inp, dict)

    def test_can_extend(self):
        class SearchInput(AgentInput):
            query: str

        inp: SearchInput = {"query": "hello"}
        assert inp["query"] == "hello"


class TestAgentOutput:
    """Tests for AgentOutput TypedDict."""

    def test_can_create_empty(self):
        out: AgentOutput = {}
        assert isinstance(out, dict)

    def test_can_extend(self):
        class SearchOutput(AgentOutput):
            summary: str

        out: SearchOutput = {"summary": "results here"}
        assert out["summary"] == "results here"


class TestErrorOutput:
    """Tests for ErrorOutput TypedDict."""

    def test_structure(self):
        err: ErrorOutput = {
            "error": "validation_error",
            "message": "Query is required",
            "details": None,
        }
        assert err["error"] == "validation_error"
        assert err["message"] == "Query is required"

    def test_with_details(self):
        err: ErrorOutput = {
            "error": "api_error",
            "message": "Rate limited",
            "details": {"retry_after": 30},
        }
        assert err["details"]["retry_after"] == 30


class TestSuccessOutput:
    """Tests for SuccessOutput TypedDict."""

    def test_basic(self):
        out: SuccessOutput = {"success": True, "data": "hello"}
        assert out["success"] is True

    def test_with_metadata(self):
        out: SuccessOutput = {
            "success": True,
            "data": [1, 2, 3],
            "metadata": {"count": 3},
        }
        assert out["metadata"]["count"] == 3
