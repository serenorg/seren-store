"""Testing utilities for Seren agents.

Helpers for testing your agent locally before publishing.
"""

import json
import os
from typing import Any, Callable, Dict, Optional


def run_local(
    agent_func: Callable,
    input_data: Dict[str, Any],
    env_vars: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run an agent locally for testing.

    Sets up the environment and executes the agent function
    as it would be called in the Seren compute environment.

    Args:
        agent_func: The agent function (decorated with @agent)
        input_data: Input data to pass to the agent
        env_vars: Environment variables to set (e.g., API keys)

    Returns:
        Agent output dict

    Example:
        from my_agent import run
        from seren_agent.testing import run_local

        result = run_local(
            run,
            {"query": "What is Python?"},
            env_vars={"OPENAI_API_KEY": "sk-..."}
        )
        print(result)
    """
    # Set environment variables
    original_env = {}
    if env_vars:
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

    try:
        result = agent_func(input_data)
        return result
    finally:
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def validate_output(output: Any) -> bool:
    """Validate that agent output is JSON-serializable.

    Args:
        output: The output to validate

    Returns:
        True if valid, raises otherwise

    Raises:
        TypeError: If output is not JSON-serializable
        ValueError: If output is not a dict
    """
    if not isinstance(output, dict):
        raise ValueError(f"Agent output must be a dict, got {type(output).__name__}")

    try:
        json.dumps(output)
        return True
    except (TypeError, ValueError) as e:
        raise TypeError(f"Agent output is not JSON-serializable: {e}")


def mock_llm_response(content: str) -> Dict[str, Any]:
    """Create a mock LLM response for testing.

    Useful for unit testing agents without making real API calls.

    Args:
        content: The content to return

    Returns:
        Mock response structure
    """
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }


class AgentTestCase:
    """Base class for agent test cases.

    Provides common setup and assertion helpers for testing agents.

    Example:
        class TestMyAgent(AgentTestCase):
            def test_basic_query(self):
                result = self.run_agent({"query": "test"})
                self.assert_has_key(result, "answer")
    """

    def __init__(self, agent_func: Callable):
        self.agent_func = agent_func

    def run_agent(
        self,
        input_data: Dict[str, Any],
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Run the agent with given input."""
        return run_local(self.agent_func, input_data, env_vars)

    def assert_has_key(self, output: Dict[str, Any], key: str) -> None:
        """Assert that output contains a key."""
        assert key in output, f"Expected key '{key}' in output, got: {list(output.keys())}"

    def assert_success(self, output: Dict[str, Any]) -> None:
        """Assert that output doesn't contain an error."""
        assert "error" not in output, f"Agent returned error: {output.get('error')}"

    def assert_error(self, output: Dict[str, Any], error_code: Optional[str] = None) -> None:
        """Assert that output contains an error."""
        assert "error" in output, "Expected error in output"
        if error_code:
            assert output["error"] == error_code, (
                f"Expected error '{error_code}', got '{output['error']}'"
            )


# Alias for convenience - used in example agents
test_agent = run_local
