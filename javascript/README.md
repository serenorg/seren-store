# Seren Agent SDK for JavaScript

Build monetizable AI agent templates that run on any compute backend.

## Installation

```bash
npm install seren-agent
# or
pnpm add seren-agent
# or
yarn add seren-agent
```

## Quick Start

```javascript
import { agent } from "seren-agent";
import { getOpenAIClient } from "seren-agent/llm";

// Define your agent with pricing
export const run = agent({
  name: "Web Researcher",
  description: "Research topics and provide comprehensive summaries",
  price: "0.05", // $0.05 per invocation
})(async (input) => {
  const openai = getOpenAIClient();

  const response = await openai.chat.completions.create({
    model: "gpt-4",
    messages: [
      { role: "system", content: "You are a research assistant." },
      { role: "user", content: `Research: ${input.query}` },
    ],
  });

  return {
    summary: response.choices[0]?.message?.content ?? "",
    model: "gpt-4",
  };
});
```

## Agent Contract

Every agent must export a `run` function with this signature:

```javascript
// input: Object -> Promise<Object>
async function run(input) {
  return { result: "..." };
}
```

The SDK's `agent()` wrapper adds metadata for the Seren Store:

```javascript
import { agent } from "seren-agent";

export const run = agent({
  name: "My Agent",           // Display name in store
  description: "...",         // What the agent does
  price: "0.01",              // Price per invocation in USD
  compute_backend: "modal",   // Optional: prefer specific backend
})(async (input) => {
  // Your logic here
  return { result: "..." };
});
```

## LLM Clients

The SDK provides helpers that read API keys from environment variables (injected by the compute backend):

```javascript
import { getOpenAIClient, getAnthropicClient, getGoogleClient } from "seren-agent/llm";

// OpenAI (uses OPENAI_API_KEY)
const openai = getOpenAIClient();
const completion = await openai.chat.completions.create({...});

// Anthropic (uses ANTHROPIC_API_KEY)
const anthropic = getAnthropicClient();
const message = await anthropic.messages.create({...});

// Google AI (uses GOOGLE_API_KEY)
const google = getGoogleClient();
const model = google.getGenerativeModel({ model: "gemini-pro" });
```

**Note:** Install the LLM SDKs you need as peer dependencies:
```bash
npm install openai              # For OpenAI
npm install @anthropic-ai/sdk   # For Anthropic
npm install @google/generative-ai  # For Google AI
```

## Tool Calling

Build agentic workflows with function calling:

```javascript
import { ToolRegistry, defineTool } from "seren-agent/tools";
import { getOpenAIClient } from "seren-agent/llm";

// Define tools
const searchTool = defineTool({
  name: "web_search",
  description: "Search the web for information",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
    },
    required: ["query"],
  },
  execute: async ({ query }) => {
    // Your search implementation
    return { results: ["result1", "result2"] };
  },
});

// Create registry
const registry = new ToolRegistry([searchTool]);

// Use with OpenAI
const openai = getOpenAIClient();
const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [{ role: "user", content: "Search for latest AI news" }],
  tools: registry.getOpenAITools(),
});

// Execute tool calls
const toolCalls = response.choices[0]?.message?.tool_calls ?? [];
for (const call of toolCalls) {
  const result = await registry.execute(
    call.function.name,
    JSON.parse(call.function.arguments)
  );
  console.log(result);
}
```

## Compute Backends

Agents are **backend-agnostic** - the same code runs on any supported backend:

| Backend | Slug | Best For |
|---------|------|----------|
| Daytona | `daytona` | General purpose (default) |
| Modal | `modal` | GPU/ML workloads |
| E2B | `e2b` | Code execution |
| Fly.io | `fly` | Long-running agents |

Specify a preference (optional):

```javascript
export const run = agent({
  name: "ML Agent",
  price: "0.10",
  compute_backend: "modal", // Prefer Modal for GPU access
})(async (input) => {
  // This will run on Modal if available
});
```

## Publishing

Use the Seren CLI to publish your agent:

```bash
# Install CLI
npm install -g @seren/cli

# Publish template
seren agent template publish \
  --name "Web Researcher" \
  --code ./src/index.js \
  --language javascript \
  --price 0.05 \
  --description "Research topics via web search"
```

## Error Handling

Return errors in a structured format:

```javascript
export const run = agent({...})(async (input) => {
  if (!input.query) {
    return {
      error: "validation_error",
      message: "Query is required",
    };
  }

  try {
    // Your logic
    return { result: "..." };
  } catch (e) {
    return {
      error: "execution_error",
      message: e.message || "Unknown error",
    };
  }
});
```

## Local Development

Test your agent locally before publishing:

```javascript
// test.js
import { run } from "./index.js";

async function test() {
  // Set environment variables for local testing
  process.env.OPENAI_API_KEY = "sk-...";

  const result = await run({ query: "What is quantum computing?" });
  console.log(result);
}

test();
```

## Examples

See the [examples directory](../examples/) for complete agent implementations:

- **Web Researcher** - Research topics via web search + LLM
- **Code Reviewer** - Analyze code for bugs and improvements
- **Document Processor** - Extract structured data from documents

## License

MIT
