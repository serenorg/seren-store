# Seren Agent SDK (Python)

Build monetizable AI agents for the Seren Store.

## Installation

```bash
pip install seren-agent

# With LLM provider support
pip install seren-agent[openai]      # OpenAI
pip install seren-agent[anthropic]   # Anthropic
pip install seren-agent[google]      # Google AI
pip install seren-agent[all]         # All providers
```

## Quick Start

Create an agent by decorating a `run` function:

```python
from seren_agent import agent
from seren_agent.llm import get_openai_client

@agent(
    name="Web Researcher",
    description="Researches topics and provides summaries",
    price="0.05"  # $0.05 per invocation
)
def run(input: dict) -> dict:
    """Research a topic and return a summary."""
    query = input["query"]

    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": f"Research: {query}"}
        ]
    )

    return {
        "summary": response.choices[0].message.content,
        "query": query
    }
```

## Agent Contract

All agents must:

1. Have a `run(input: dict) -> dict` function
2. Accept JSON-serializable input
3. Return JSON-serializable output
4. Be decorated with `@agent`

## LLM Helpers

The SDK provides helpers for common LLM providers:

```python
from seren_agent.llm import (
    get_openai_client,
    get_anthropic_client,
    get_google_client,
    get_llm_model,
)

# OpenAI
client = get_openai_client()
response = client.chat.completions.create(...)

# Anthropic
client = get_anthropic_client()
message = client.messages.create(...)

# Google AI
genai = get_google_client()
model = genai.GenerativeModel("gemini-pro")
```

API keys are automatically injected by the compute environment. You don't need to manage them.

## Tool Calling

For agents that use tools:

```python
from seren_agent import agent
from seren_agent.tools import ToolRegistry, parse_tool_calls, create_tool_result
from seren_agent.llm import get_openai_client

registry = ToolRegistry()

@registry.register("search", "Search the web for information")
def search(query: str) -> dict:
    # Your search implementation
    return {"results": [...]}

@agent(name="Tool Agent", price="0.10")
def run(input: dict) -> dict:
    client = get_openai_client()
    messages = [{"role": "user", "content": input["query"]}]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=registry.get_schemas()
    )

    # Handle tool calls
    tool_calls = parse_tool_calls(response)
    for call in tool_calls:
        result = registry.execute(call["name"], call["arguments"])
        messages.append(create_tool_result(call["id"], result))

    # Get final response
    final = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

    return {"answer": final.choices[0].message.content}
```

## Local Testing

Test your agent locally before publishing:

```python
from seren_agent.testing import run_local
from my_agent import run

result = run_local(
    run,
    {"query": "What is Python?"},
    env_vars={"OPENAI_API_KEY": "sk-..."}
)
print(result)
```

## Publishing

Use the Seren CLI to publish your agent:

```bash
seren agent template publish \
    --name "Web Researcher" \
    --code ./agent.py \
    --language python \
    --price 0.05 \
    --description "Researches topics and provides summaries"
```

## Compute Backends

Agents run on compute backends like Daytona, Modal, or E2B. You can optionally specify a preferred backend:

```python
@agent(
    name="ML Agent",
    price="0.50",
    compute_backend="modal"  # Prefer Modal for GPU access
)
def run(input: dict) -> dict:
    ...
```

If not specified, the default backend (Daytona) is used.

## Dependencies

Specify your agent's dependencies when publishing:

```bash
seren agent template publish \
    --code ./agent.py \
    --dependencies openai requests beautifulsoup4
```

## License

MIT
