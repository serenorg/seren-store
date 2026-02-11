# ABOUTME: Package entry point for the seren-agent SDK.
# ABOUTME: Exports the @agent decorator and base types for building Seren agent templates.
"""Seren Agent SDK - Build monetizable AI agents for the Seren Store.

This SDK provides a simple interface for creating agent templates that can
run on multiple compute backends (Daytona, Modal, E2B, etc.) and be monetized
via x402 micropayments.

Example:
    from seren_agent import agent
    from seren_agent.llm import get_openai_client

    @agent(name="Web Researcher", price="0.05")
    def run(input: dict) -> dict:
        client = get_openai_client()
        # ... your agent logic ...
        return {"result": "..."}
"""

from .agent import agent
from .types import AgentInput, AgentOutput

__version__ = "0.1.0"
__all__ = ["agent", "AgentInput", "AgentOutput"]
