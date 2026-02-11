# ABOUTME: Factory functions for LLM clients (OpenAI, Anthropic, Google).
# ABOUTME: Reads API keys from env vars injected by the compute backend.
"""LLM client helpers for Seren agents.

These helpers provide a consistent way to access LLM APIs using environment
variables injected by the compute backend. The key hierarchy is:

1. User-provided key (via X-LLM-API-KEY header at invocation)
2. Publisher-configured key (set when publishing the template)
3. Seren platform key (fallback for verified publishers)

You don't need to manage keys - just call get_*_client() and it works.
"""

import os
from typing import Any, Dict, List, Optional

import httpx

# Default Seren API URL
DEFAULT_SEREN_API_URL = "https://api.serendb.com"
DEFAULT_SEREN_PUBLISHER = "seren-models"


class ChatCompletions:
    """Chat completions interface matching OpenAI's API structure."""

    def __init__(self, client: "SerenLLMClient"):
        self._client = client

    def create(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to client's default_model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            top_p: Nucleus sampling parameter
            stream: Enable streaming (not yet supported)
            **kwargs: Additional parameters passed to the API

        Returns:
            API response dict with choices and usage
        """
        body: Dict[str, Any] = {
            "model": model or self._client.default_model,
            "messages": messages,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if temperature is not None:
            body["temperature"] = temperature
        if top_p is not None:
            body["top_p"] = top_p
        if stream:
            body["stream"] = stream
        body.update(kwargs)

        return self._client._request("POST", "/chat/completions", json=body)


class Messages:
    """Messages interface matching Anthropic's API structure."""

    def __init__(self, client: "SerenLLMClient"):
        self._client = client

    def create(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Create a message (Anthropic-style interface).

        This is an alias for chat.completions.create() for compatibility
        with code written for the Anthropic SDK.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to client's default_model)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            API response dict
        """
        return self._client.chat.completions.create(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )


class Chat:
    """Chat namespace containing completions."""

    def __init__(self, client: "SerenLLMClient"):
        self.completions = ChatCompletions(client)


class SerenLLMClient:
    """HTTP client for accessing LLMs through Seren Publishers.

    Routes LLM requests through Seren's publisher infrastructure,
    providing unified billing and access control without requiring
    provider-specific SDK packages.

    Args:
        api_key: Seren API key. If not provided, uses SEREN_API_KEY env var.
        base_url: Seren API URL. If not provided, uses SEREN_API_URL env var
                  or defaults to https://api.serendb.com
        publisher: Publisher slug to route requests through.
                   Defaults to 'seren-models'.
        default_model: Default model for requests.

    Raises:
        RuntimeError: If no API key is available

    Example:
        client = SerenLLMClient(default_model="anthropic/claude-sonnet-4-20250514")
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=100
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        publisher: str = DEFAULT_SEREN_PUBLISHER,
        default_model: str = "anthropic/claude-sonnet-4-20250514",
    ):
        self.api_key = api_key or os.environ.get("SEREN_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "SEREN_API_KEY not set. Set the environment variable or pass api_key parameter."
            )

        self.base_url = base_url or os.environ.get(
            "SEREN_API_URL", DEFAULT_SEREN_API_URL
        )
        self.publisher = publisher
        self.default_model = default_model

        self._http_client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

        # Initialize interface namespaces
        self.chat = Chat(self)
        self.messages = Messages(self)

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the Seren publisher API.

        Args:
            method: HTTP method
            path: API path (appended to publisher route)
            json: Request body

        Returns:
            Response JSON

        Raises:
            Exception: On HTTP errors
        """
        url = f"/publishers/{self.publisher}{path}"
        response = self._http_client.request(method, url, json=json)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._http_client.close()

    def __enter__(self) -> "SerenLLMClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


def get_seren_claude_client(
    api_key: Optional[str] = None,
    model: str = "anthropic/claude-sonnet-4-20250514",
) -> SerenLLMClient:
    """Get a Claude client routed through Seren Publishers.

    This client makes requests through the seren-models publisher,
    which provides access to Claude models without requiring the
    anthropic package. Only SEREN_API_KEY is needed.

    Args:
        api_key: Optional Seren API key override
        model: Default Claude model to use

    Returns:
        SerenLLMClient configured for Claude

    Raises:
        RuntimeError: If SEREN_API_KEY is not set

    Example:
        from seren_agent.llm import get_seren_claude_client

        client = get_seren_claude_client()
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=100
        )
        print(response["choices"][0]["message"]["content"])
    """
    return SerenLLMClient(
        api_key=api_key,
        default_model=model,
    )


def get_seren_openai_client(
    api_key: Optional[str] = None,
    model: str = "openai/gpt-4o",
) -> SerenLLMClient:
    """Get an OpenAI client routed through Seren Publishers.

    This client makes requests through the seren-models publisher,
    which provides access to OpenAI models without requiring the
    openai package. Only SEREN_API_KEY is needed.

    Args:
        api_key: Optional Seren API key override
        model: Default OpenAI model to use

    Returns:
        SerenLLMClient configured for OpenAI models

    Raises:
        RuntimeError: If SEREN_API_KEY is not set

    Example:
        from seren_agent.llm import get_seren_openai_client

        client = get_seren_openai_client()
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=100
        )
        print(response["choices"][0]["message"]["content"])
    """
    return SerenLLMClient(
        api_key=api_key,
        default_model=model,
    )


# =============================================================================
# Original provider-specific clients (require provider SDK packages)
# =============================================================================


def get_openai_client(api_key: Optional[str] = None):
    """Get an OpenAI client using injected OPENAI_API_KEY.

    Args:
        api_key: Optional override. If not provided, uses environment variable.

    Returns:
        OpenAI client instance

    Raises:
        RuntimeError: If no API key is available
        ImportError: If openai package is not installed

    Example:
        from seren_agent.llm import get_openai_client

        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "openai package not installed. Add 'openai' to your dependencies."
        )

    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Ensure LLM config is provided when publishing "
            "or the caller passes X-LLM-API-KEY header."
        )
    return OpenAI(api_key=key)


def get_anthropic_client(api_key: Optional[str] = None):
    """Get an Anthropic client using injected ANTHROPIC_API_KEY.

    Args:
        api_key: Optional override. If not provided, uses environment variable.

    Returns:
        Anthropic client instance

    Raises:
        RuntimeError: If no API key is available
        ImportError: If anthropic package is not installed

    Example:
        from seren_agent.llm import get_anthropic_client

        client = get_anthropic_client()
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello!"}]
        )
    """
    try:
        from anthropic import Anthropic
    except ImportError:
        raise ImportError(
            "anthropic package not installed. Add 'anthropic' to your dependencies."
        )

    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Ensure LLM config is provided when publishing "
            "or the caller passes X-LLM-API-KEY header."
        )
    return Anthropic(api_key=key)


def get_google_client(api_key: Optional[str] = None):
    """Get a Google Generative AI client using injected GOOGLE_API_KEY.

    Args:
        api_key: Optional override. If not provided, uses environment variable.

    Returns:
        Configured google.generativeai module

    Raises:
        RuntimeError: If no API key is available
        ImportError: If google-generativeai package is not installed

    Example:
        from seren_agent.llm import get_google_client

        genai = get_google_client()
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content("Hello!")
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError(
            "google-generativeai package not installed. "
            "Add 'google-generativeai' to your dependencies."
        )

    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY not set. Ensure LLM config is provided when publishing "
            "or the caller passes X-LLM-API-KEY header."
        )
    genai.configure(api_key=key)
    return genai


def get_llm_model() -> Optional[str]:
    """Get the configured LLM model name from environment.

    Returns:
        Model name if set, None otherwise

    Example:
        model = get_llm_model() or "gpt-4o"
    """
    return os.environ.get("LLM_MODEL")


def get_generic_api_key() -> Optional[str]:
    """Get a generic LLM API key from environment.

    This is useful for providers not explicitly supported.

    Returns:
        API key if set, None otherwise
    """
    return os.environ.get("LLM_API_KEY")
