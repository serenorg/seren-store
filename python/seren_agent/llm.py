"""LLM client helpers for Seren agents.

These helpers provide a consistent way to access LLM APIs using environment
variables injected by the compute backend. The key hierarchy is:

1. User-provided key (via X-LLM-API-KEY header at invocation)
2. Publisher-configured key (set when publishing the template)
3. Seren platform key (fallback for verified publishers)

You don't need to manage keys - just call get_*_client() and it works.
"""

import os
from typing import Optional


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
