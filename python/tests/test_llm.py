# ABOUTME: Unit tests for Seren Publisher routing LLM clients.
# ABOUTME: Tests get_seren_claude_client and related functions.

import os
import pytest
from unittest.mock import patch, MagicMock
import json

from seren_agent.llm import (
    get_seren_claude_client,
    get_seren_openai_client,
    SerenLLMClient,
)


class TestSerenLLMClient:
    """Tests for the SerenLLMClient class."""

    def test_client_requires_api_key(self):
        """Client should raise error if no SEREN_API_KEY is set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SEREN_API_KEY", None)
            with pytest.raises(RuntimeError, match="SEREN_API_KEY"):
                SerenLLMClient()

    def test_client_accepts_explicit_api_key(self):
        """Client should accept an explicit API key."""
        with patch.dict(os.environ, {}, clear=True):
            client = SerenLLMClient(api_key="test-key")
            assert client.api_key == "test-key"

    def test_client_uses_env_api_key(self):
        """Client should use SEREN_API_KEY from environment."""
        with patch.dict(os.environ, {"SEREN_API_KEY": "env-key"}):
            client = SerenLLMClient()
            assert client.api_key == "env-key"

    def test_client_default_base_url(self):
        """Client should use default Seren API URL."""
        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = SerenLLMClient()
            assert "seren" in client.base_url.lower() or "localhost" in client.base_url

    def test_client_custom_base_url(self):
        """Client should accept custom base URL via env var."""
        with patch.dict(
            os.environ,
            {"SEREN_API_KEY": "test-key", "SEREN_API_URL": "https://custom.api.com"},
        ):
            client = SerenLLMClient()
            assert client.base_url == "https://custom.api.com"


class TestSerenClaudeClient:
    """Tests for get_seren_claude_client function."""

    def test_returns_client_with_claude_model(self):
        """Should return a client configured for Claude models."""
        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_claude_client()
            assert client.default_model.startswith("anthropic/")

    def test_custom_model_override(self):
        """Should allow overriding the default model."""
        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_claude_client(model="anthropic/claude-opus-4-20250514")
            assert client.default_model == "anthropic/claude-opus-4-20250514"


class TestSerenOpenAIClient:
    """Tests for get_seren_openai_client function."""

    def test_returns_client_with_openai_model(self):
        """Should return a client configured for OpenAI models."""
        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_openai_client()
            assert client.default_model.startswith("openai/")

    def test_custom_model_override(self):
        """Should allow overriding the default model."""
        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_openai_client(model="openai/gpt-4-turbo")
            assert client.default_model == "openai/gpt-4-turbo"


class TestChatCompletions:
    """Tests for the chat completions interface."""

    @patch("seren_agent.llm.httpx.Client.request")
    def test_chat_completions_create(self, mock_request):
        """Should make correct API call for chat completions."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_request.return_value = mock_response

        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_claude_client()
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=100,
            )

        assert response["choices"][0]["message"]["content"] == "Hello!"
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        # Verify the request body includes model and messages
        body = call_args.kwargs.get("json") or json.loads(
            call_args.kwargs.get("data", "{}")
        )
        assert "model" in body
        assert "messages" in body

    @patch("seren_agent.llm.httpx.Client.request")
    def test_chat_completions_with_custom_model(self, mock_request):
        """Should allow overriding model per request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hi!"}}],
        }
        mock_request.return_value = mock_response

        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_claude_client()
            client.chat.completions.create(
                model="anthropic/claude-opus-4-20250514",
                messages=[{"role": "user", "content": "Hi"}],
            )

        call_args = mock_request.call_args
        body = call_args.kwargs.get("json") or json.loads(
            call_args.kwargs.get("data", "{}")
        )
        assert body["model"] == "anthropic/claude-opus-4-20250514"

    @patch("seren_agent.llm.httpx.Client.request")
    def test_handles_api_error(self, mock_request):
        """Should handle API errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.json.return_value = {
            "error": {"message": "Insufficient balance", "code": 402}
        }
        mock_response.raise_for_status.side_effect = Exception("402 Payment Required")
        mock_request.return_value = mock_response

        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_claude_client()
            with pytest.raises(Exception):
                client.chat.completions.create(
                    messages=[{"role": "user", "content": "Hi"}],
                )


class TestMessagesInterface:
    """Tests for the messages interface (Anthropic-style)."""

    @patch("seren_agent.llm.httpx.Client.request")
    def test_messages_create(self, mock_request):
        """Should support Anthropic-style messages.create() interface."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Hello!"}}],
        }
        mock_request.return_value = mock_response

        with patch.dict(os.environ, {"SEREN_API_KEY": "test-key"}):
            client = get_seren_claude_client()
            response = client.messages.create(
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=100,
            )

        # Should convert to standard response format
        assert "content" in response or "choices" in response
