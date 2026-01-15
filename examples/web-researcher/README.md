# Web Researcher Agent

Research any topic and get a comprehensive summary with sources.

## Usage

```python
# Input
{
    "query": "What are the latest developments in quantum computing?",
    "depth": "moderate",  # optional: "quick" | "moderate" | "thorough"
    "max_sources": 5      # optional: max number of sources to return
}

# Output
{
    "summary": "Comprehensive summary of the topic...",
    "key_points": [
        "Point 1",
        "Point 2",
        ...
    ],
    "sources": [
        {"title": "Source Title", "url": "https://...", "relevance": "..."}
    ],
    "confidence": "medium",
    "metadata": {
        "depth": "moderate",
        "model_used": "gpt-4o",
        "query": "..."
    }
}
```

## Pricing

- **$0.05 per invocation** (covers LLM API costs + compute)

## Configuration

This agent requires an OpenAI API key. When publishing to Seren Store, configure
the LLM settings in your template:

```json
{
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4o"
    }
}
```

## Local Testing

```bash
cd examples/web-researcher
OPENAI_API_KEY=your-key python agent.py
```
