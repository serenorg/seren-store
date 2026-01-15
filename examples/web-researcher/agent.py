"""
Web Researcher Agent

Researches topics by gathering information from the web and synthesizing
a comprehensive summary using LLM analysis.

Price: $0.05 per invocation (covers LLM API costs + compute)
"""

from seren_agent import agent
from seren_agent.llm import get_openai_client


@agent(
    name="Web Researcher",
    description="Research any topic and get a comprehensive summary with sources. "
    "Provide a query and optionally specify depth (quick, moderate, thorough).",
    price="0.05",
)
def run(input: dict) -> dict:
    """
    Research a topic and return a structured summary.

    Input:
        query: str - The research question or topic
        depth: str - Research depth: "quick" (default), "moderate", or "thorough"
        max_sources: int - Maximum number of sources to include (default: 5)

    Output:
        summary: str - Comprehensive summary of findings
        key_points: list[str] - Bullet points of main findings
        sources: list[dict] - List of sources with title, url, relevance
        confidence: str - Confidence level in the research (low, medium, high)
    """
    query = input.get("query")
    if not query:
        return {"error": "Missing required field: query"}

    depth = input.get("depth", "quick")
    max_sources = input.get("max_sources", 5)

    # Validate depth
    if depth not in ("quick", "moderate", "thorough"):
        depth = "quick"

    # Configure research parameters based on depth
    depth_config = {
        "quick": {"iterations": 1, "model": "gpt-4o-mini"},
        "moderate": {"iterations": 2, "model": "gpt-4o"},
        "thorough": {"iterations": 3, "model": "gpt-4o"},
    }
    config = depth_config[depth]

    client = get_openai_client()

    # For this example, we simulate web research by using the LLM's knowledge
    # In production, this would integrate with a web search API (e.g., via Seren publisher)
    system_prompt = """You are a research assistant. Your task is to provide comprehensive
    information about the given topic. Structure your response as follows:

    1. A detailed summary (2-3 paragraphs)
    2. Key points (5-7 bullet points)
    3. Suggested sources (real, verifiable sources when possible)
    4. Confidence assessment

    Be factual, cite specific information, and acknowledge limitations in your knowledge."""

    # Perform research
    response = client.chat.completions.create(
        model=config["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Research the following topic thoroughly: {query}",
            },
        ],
        temperature=0.7,
    )

    research_text = response.choices[0].message.content

    # Parse and structure the response
    # In production, you'd use a more robust parsing approach
    key_points = []
    sources = []

    # Extract key points (lines starting with - or *)
    for line in research_text.split("\n"):
        line = line.strip()
        if line.startswith(("-", "*", "•")) and len(line) > 3:
            key_points.append(line.lstrip("-*• "))
            if len(key_points) >= 7:
                break

    # Generate source suggestions
    source_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Generate a JSON array of relevant sources for the topic. "
                "Each source should have: title, url (realistic but may be example), "
                "and relevance (brief description). Return only valid JSON.",
            },
            {"role": "user", "content": f"Topic: {query}\n\nGenerate {max_sources} sources."},
        ],
        temperature=0.5,
    )

    try:
        import json

        sources_text = source_response.choices[0].message.content
        # Clean up potential markdown code blocks
        if "```" in sources_text:
            sources_text = sources_text.split("```")[1]
            if sources_text.startswith("json"):
                sources_text = sources_text[4:]
        sources = json.loads(sources_text)[:max_sources]
    except (json.JSONDecodeError, IndexError):
        sources = [
            {
                "title": "General Reference",
                "url": "https://example.com",
                "relevance": "Primary research source",
            }
        ]

    # Determine confidence based on topic complexity and depth
    confidence = "medium"
    if depth == "thorough" and len(key_points) >= 5:
        confidence = "high"
    elif depth == "quick" or len(key_points) < 3:
        confidence = "low"

    return {
        "summary": research_text,
        "key_points": key_points[:7],
        "sources": sources,
        "confidence": confidence,
        "metadata": {
            "depth": depth,
            "model_used": config["model"],
            "query": query,
        },
    }


if __name__ == "__main__":
    # Local testing
    from seren_agent.testing import test_agent

    result = test_agent(
        run,
        {"query": "What are the latest developments in quantum computing?", "depth": "quick"},
        env={"OPENAI_API_KEY": "your-key-here"},
    )
    print(result)
