# ABOUTME: Tests for the testing utilities module.
# ABOUTME: Covers run_local env injection, validate_output, mock_llm_response, AgentTestCase.
import os
import pytest
from seren_agent.agent import agent
from seren_agent.testing import (
    run_local,
    validate_output,
    mock_llm_response,
    AgentTestCase,
    test_agent as run_local_alias,
)


@agent(name="Echo Agent", price="0.01")
def echo_agent(input: dict) -> dict:
    return {"echo": input.get("message", "")}


@agent(name="Env Agent", price="0.01")
def env_agent(input: dict) -> dict:
    return {"key": os.environ.get("TEST_KEY", "not_set")}


class TestRunLocal:
    """Tests for run_local."""

    def test_basic_execution(self):
        result = run_local(echo_agent, {"message": "hello"})
        assert result == {"echo": "hello"}

    def test_env_vars_injected(self):
        result = run_local(
            env_agent,
            {},
            env_vars={"TEST_KEY": "injected_value"},
        )
        assert result == {"key": "injected_value"}

    def test_env_vars_restored_after_run(self):
        original = os.environ.get("TEST_RESTORE_KEY")
        assert original is None

        run_local(
            env_agent,
            {},
            env_vars={"TEST_RESTORE_KEY": "temporary"},
        )

        assert os.environ.get("TEST_RESTORE_KEY") is None

    def test_env_vars_restored_on_exception(self):
        @agent(name="Error Agent", price="0.01")
        def error_agent(input: dict) -> dict:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            run_local(
                error_agent,
                {},
                env_vars={"TEST_ERROR_KEY": "temp"},
            )

        assert os.environ.get("TEST_ERROR_KEY") is None

    def test_no_env_vars(self):
        result = run_local(echo_agent, {"message": "test"})
        assert result == {"echo": "test"}


class TestValidateOutput:
    """Tests for validate_output."""

    def test_valid_dict(self):
        assert validate_output({"key": "value"}) is True

    def test_nested_dict(self):
        assert validate_output({"data": {"nested": [1, 2, 3]}}) is True

    def test_non_dict_raises(self):
        with pytest.raises(ValueError, match="must be a dict"):
            validate_output("not a dict")

    def test_non_dict_list_raises(self):
        with pytest.raises(ValueError, match="must be a dict"):
            validate_output([1, 2, 3])

    def test_non_serializable_raises(self):
        with pytest.raises(TypeError, match="not JSON-serializable"):
            validate_output({"func": lambda x: x})


class TestMockLlmResponse:
    """Tests for mock_llm_response."""

    def test_structure(self):
        response = mock_llm_response("Hello world")
        assert response["choices"][0]["message"]["content"] == "Hello world"
        assert response["choices"][0]["message"]["role"] == "assistant"

    def test_empty_content(self):
        response = mock_llm_response("")
        assert response["choices"][0]["message"]["content"] == ""


class TestAgentTestCase:
    """Tests for AgentTestCase."""

    def test_run_agent(self):
        tc = AgentTestCase(echo_agent)
        result = tc.run_agent({"message": "hello"})
        assert result == {"echo": "hello"}

    def test_assert_has_key_passes(self):
        tc = AgentTestCase(echo_agent)
        result = tc.run_agent({"message": "test"})
        tc.assert_has_key(result, "echo")

    def test_assert_has_key_fails(self):
        tc = AgentTestCase(echo_agent)
        result = tc.run_agent({"message": "test"})
        with pytest.raises(AssertionError, match="Expected key"):
            tc.assert_has_key(result, "missing_key")

    def test_assert_success_passes(self):
        tc = AgentTestCase(echo_agent)
        result = tc.run_agent({"message": "test"})
        tc.assert_success(result)

    def test_assert_success_fails(self):
        tc = AgentTestCase(echo_agent)
        with pytest.raises(AssertionError, match="returned error"):
            tc.assert_success({"error": "something_wrong"})

    def test_assert_error_passes(self):
        tc = AgentTestCase(echo_agent)
        tc.assert_error({"error": "bad_input"})

    def test_assert_error_with_code(self):
        tc = AgentTestCase(echo_agent)
        tc.assert_error({"error": "bad_input"}, error_code="bad_input")

    def test_assert_error_wrong_code(self):
        tc = AgentTestCase(echo_agent)
        with pytest.raises(AssertionError, match="Expected error"):
            tc.assert_error({"error": "bad_input"}, error_code="wrong_code")


class TestTestAgentAlias:
    """Test that test_agent is an alias for run_local."""

    def test_alias_works(self):
        result = run_local_alias(echo_agent, {"message": "alias"})
        assert result == {"echo": "alias"}
