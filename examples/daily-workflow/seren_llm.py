# ABOUTME: LLM client that routes through Seren Models publisher.
# ABOUTME: Provides Claude access via Seren's API instead of direct Anthropic.

import os
import httpx
from dataclasses import dataclass
from typing import List, Optional


SEREN_API_URL = os.environ.get("SEREN_API_URL", "https://api.serendb.com")
SEREN_API_KEY = os.environ.get("SEREN_API_KEY", "")


@dataclass
class MessageContent:
    """Mimics Anthropic message content structure."""
    text: str
    type: str = "text"


@dataclass
class Message:
    """Mimics Anthropic message structure."""
    content: List[MessageContent]
    role: str = "assistant"


class SerenClaudeClient:
    """Claude client that routes through Seren Models publisher.

    Uses Seren's /agent/api endpoint with OpenAI-compatible format via OpenRouter.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or SEREN_API_KEY
        self.base_url = SEREN_API_URL

    def create_message(
        self,
        model: str,
        max_tokens: int,
        messages: List[dict],
    ) -> Message:
        """Create a message using Seren Models publisher.

        Args:
            model: Claude model name (e.g., claude-haiku-4-20250514)
            max_tokens: Maximum tokens in response
            messages: List of message dicts with role and content

        Returns:
            Message object with response content
        """
        # Seren API wrapper format - calls /agent/api with publisher routing
        # Model IDs should already include provider prefix (e.g., anthropic/claude-3.5-haiku)
        payload = {
            "publisher": "seren-models",
            "method": "POST",
            "path": "/chat/completions",
            "body": {
                "model": model,
                "max_tokens": max_tokens,
                "messages": messages,
            },
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/agent/api",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                raise RuntimeError(f"Seren API error: {response.status_code} - {response.text}")

            data = response.json()

            # Response body contains the OpenAI-format response from the publisher
            body = data.get("body", data)

            # Parse OpenAI-format response into Anthropic-like Message structure
            content = []
            for choice in body.get("choices", []):
                message = choice.get("message", {})
                if message.get("content"):
                    content.append(MessageContent(text=message.get("content", "")))

            return Message(content=content)

    @property
    def messages(self):
        """Provide messages.create() interface for compatibility."""
        return self


    def create(self, model: str, max_tokens: int, messages: List[dict]) -> Message:
        """Alias for create_message to match Anthropic client interface."""
        return self.create_message(model, max_tokens, messages)


def get_seren_claude_client(api_key: Optional[str] = None) -> SerenClaudeClient:
    """Get a Claude client that routes through Seren.

    Args:
        api_key: Optional Seren API key. Uses SEREN_API_KEY env var if not provided.

    Returns:
        SerenClaudeClient instance
    """
    return SerenClaudeClient(api_key=api_key)
