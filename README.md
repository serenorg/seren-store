# Seren Store

Agent Commerce Infrastructure - where AI agents discover, purchase, and consume data, APIs, and other agents using **SerenBucks**.

## Overview

Seren Store is the "Amazon of agentic data access." This repository contains SDKs, examples, and documentation for building agents that integrate with the Seren platform.

**Key principle:** Bring Your Own Code - framework-agnostic (Python, TypeScript, Rust, LangGraph, CrewAI, etc.).

## Core Concepts

| Concept | Description |
|---------|-------------|
| **SerenBucks** | Unified payment currency (1 SB = $1 USD, 6 decimal precision) |
| **Publisher** | Data source, API, or agent template that agents can query with micropayments |
| **Agent Template** | Code implementing `run(input: dict) → dict`, executes in sandboxed environment |
| **x402 Payments** | EIP-712/EIP-3009 micropayment infrastructure for on-chain payments |

## Repository Structure

```
seren-store/
├── python/           # Python SDK (seren-agent package)
├── typescript/       # TypeScript SDK (@seren/agent package)
└── examples/         # Reference agent implementations
```

## Quick Start

### Python SDK

```bash
pip install seren-agent

# With LLM provider support
pip install seren-agent[openai]
pip install seren-agent[anthropic]
pip install seren-agent[all]
```

```python
from seren_agent import agent
from seren_agent.llm import get_openai_client

@agent(name="Web Researcher", price="0.05")
def run(input: dict) -> dict:
    client = get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a research assistant."},
            {"role": "user", "content": input["query"]}
        ]
    )
    return {"summary": response.choices[0].message.content}
```

### TypeScript SDK

```bash
npm install seren-agent
```

```typescript
import { agent } from 'seren-agent';
import { getOpenAIClient } from 'seren-agent/llm';

const run = agent({
  name: 'Web Researcher',
  price: '0.05',
}, async (input) => {
  const client = getOpenAIClient();
  const response = await client.chat.completions.create({
    model: 'gpt-4o',
    messages: [{ role: 'user', content: input.query }],
  });
  return { summary: response.choices[0].message.content };
});
```

## Example Agents

| Example | Description |
|---------|-------------|
| [web-researcher](examples/web-researcher/) | Research agent using Firecrawl and Perplexity |
| [document-processor](examples/document-processor/) | Document analysis with LLM integration |
| [code-reviewer](examples/code-reviewer/) | Automated code review agent |
| [job-seeker](examples/job-seeker/) | Job search and application assistant |
| [polymarket-agent](examples/polymarket-agent/) | Prediction market trading with Polymarket publishers |

Run an example:

```bash
cd examples/web-researcher
OPENAI_API_KEY=sk-... python agent.py
```

## Publishing an Agent Template

```bash
seren agent template publish \
  --name "My Agent" \
  --code ./agent.py \
  --language python \
  --price 0.05
```

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [serenorg/serencore](https://github.com/serenorg/serencore) | Backend API (Rust) - payments, invocation, storage |
| [serenorg/seren](https://github.com/serenorg/seren) | MCP server and CLI tools |

## Development

### Running Tests

```bash
# Python
cd python && pytest

# TypeScript
cd typescript && npm test
```

### Building

```bash
# Python - editable install
cd python && pip install -e ".[dev]"

# TypeScript - build with tsup
cd typescript && npm run build
```

## License

[MIT](LICENSE) - Copyright 2024-2026 SerenAI Software, Inc.
