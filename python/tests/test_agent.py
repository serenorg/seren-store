# ABOUTME: Tests for the @agent decorator, metadata attachment, and validation.
# ABOUTME: Covers valid usage, edge cases, and error conditions for agent creation.
import pytest
from seren_agent.agent import agent, get_agent_metadata, is_seren_agent


class TestAgentDecorator:
    """Tests for the @agent decorator."""

    def test_basic_decoration(self):
        @agent(name="Test Agent", price="0.05")
        def run(input: dict) -> dict:
            return {"result": input["query"]}

        result = run({"query": "hello"})
        assert result == {"result": "hello"}

    def test_metadata_attached(self):
        @agent(name="Test Agent", description="A test", price="0.10")
        def run(input: dict) -> dict:
            return {}

        meta = run._seren_agent
        assert meta["name"] == "Test Agent"
        assert meta["description"] == "A test"
        assert meta["price"] == "0.10"
        assert meta["function_name"] == "run"
        assert meta["compute_backend"] is None

    def test_compute_backend(self):
        @agent(name="GPU Agent", price="0.50", compute_backend="modal")
        def run(input: dict) -> dict:
            return {}

        assert run._seren_agent["compute_backend"] == "modal"

    def test_preserves_function_name(self):
        @agent(name="Test", price="0.01")
        def my_custom_agent(input: dict) -> dict:
            return {}

        assert my_custom_agent.__name__ == "my_custom_agent"
        assert my_custom_agent._seren_agent["function_name"] == "my_custom_agent"

    def test_name_stripped(self):
        @agent(name="  Padded Name  ", price="0.01")
        def run(input: dict) -> dict:
            return {}

        assert run._seren_agent["name"] == "Padded Name"

    def test_zero_price_allowed(self):
        @agent(name="Free Agent", price="0.00")
        def run(input: dict) -> dict:
            return {}

        assert run._seren_agent["price"] == "0.00"


class TestAgentValidation:
    """Tests for decorator input validation."""

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name is required"):
            @agent(name="", price="0.01")
            def run(input: dict) -> dict:
                return {}

    def test_whitespace_name_raises(self):
        with pytest.raises(ValueError, match="name is required"):
            @agent(name="   ", price="0.01")
            def run(input: dict) -> dict:
                return {}

    def test_empty_price_raises(self):
        with pytest.raises(ValueError, match="price is required"):
            @agent(name="Test", price="")
            def run(input: dict) -> dict:
                return {}

    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            @agent(name="Test", price="-0.50")
            def run(input: dict) -> dict:
                return {}

    def test_invalid_price_format_raises(self):
        with pytest.raises(ValueError, match="valid number"):
            @agent(name="Test", price="free")
            def run(input: dict) -> dict:
                return {}


class TestGetAgentMetadata:
    """Tests for get_agent_metadata helper."""

    def test_returns_metadata_for_agent(self):
        @agent(name="Test", price="0.01")
        def run(input: dict) -> dict:
            return {}

        meta = get_agent_metadata(run)
        assert meta is not None
        assert meta["name"] == "Test"

    def test_returns_none_for_plain_function(self):
        def plain_func():
            pass

        assert get_agent_metadata(plain_func) is None


class TestIsSerenAgent:
    """Tests for is_seren_agent helper."""

    def test_true_for_decorated(self):
        @agent(name="Test", price="0.01")
        def run(input: dict) -> dict:
            return {}

        assert is_seren_agent(run) is True

    def test_false_for_plain(self):
        def plain_func():
            pass

        assert is_seren_agent(plain_func) is False
