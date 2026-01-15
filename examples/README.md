# Seren Agent Examples

Example agents demonstrating the Seren Agent SDK capabilities.

## Available Examples

| Agent | Language | Price | Description |
|-------|----------|-------|-------------|
| [Web Researcher](./web-researcher/) | Python | $0.05 | Research topics and get summaries with sources |
| [Code Reviewer](./code-reviewer/) | Python | $0.03 | Analyze code for bugs, security, and style |
| [Document Processor](./document-processor/) | TypeScript | $0.04 | Extract structured data from documents |
| [Job Seeker](./job-seeker/) | TypeScript | $0.06 | Match resumes to jobs with recommendations |

## Running Examples Locally

### Python Examples

```bash
cd web-researcher  # or code-reviewer
pip install seren-agent
OPENAI_API_KEY=your-key python agent.py
```

### TypeScript Examples

```bash
cd document-processor  # or job-seeker
npm install seren-agent
OPENAI_API_KEY=your-key npx ts-node agent.ts
```

## Publishing to Seren Store

1. **Install the Seren CLI:**
   ```bash
   npm install -g @seren/cli
   # or
   cargo install seren-cli
   ```

2. **Authenticate:**
   ```bash
   seren auth login
   ```

3. **Publish your agent:**
   ```bash
   seren agent publish-template \
     --name "My Agent" \
     --slug "my-agent" \
     --code ./agent.py \
     --language python \
     --price "0.05" \
     --description "Description of what my agent does"
   ```

## Agent Structure

Each example follows the standard Seren Agent pattern:

### Python
```python
from seren_agent import agent
from seren_agent.llm import get_openai_client

@agent(name="...", description="...", price="0.05")
def run(input: dict) -> dict:
    client = get_openai_client()
    # ... process input ...
    return {"result": "..."}
```

### TypeScript
```typescript
import { agent } from "seren-agent";
import { getOpenAIClient } from "seren-agent/llm";

export const run = agent(
  { name: "...", description: "...", price: "0.05" },
  async (input) => {
    const client = getOpenAIClient();
    // ... process input ...
    return { result: "..." };
  }
);
```

## LLM Configuration

Agents use environment variables for LLM API keys (injected by the compute backend):

- `OPENAI_API_KEY` - For OpenAI models
- `ANTHROPIC_API_KEY` - For Anthropic models
- `GOOGLE_API_KEY` - For Google AI models

When publishing, configure LLM requirements in your template metadata.

## Contributing

Want to add an example? Follow these guidelines:

1. Create a new directory under `examples/`
2. Include `agent.py` or `agent.ts` with the agent implementation
3. Include a `README.md` with usage documentation
4. Keep examples focused and well-documented
5. Test locally before submitting
