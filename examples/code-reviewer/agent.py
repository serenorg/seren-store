"""
Code Reviewer Agent

Analyzes code for bugs, style issues, security vulnerabilities, and provides
improvement suggestions using LLM-powered analysis.

Price: $0.03 per invocation
"""

from seren_agent import agent
from seren_agent.llm import get_openai_client


@agent(
    name="Code Reviewer",
    description="Analyze code for bugs, security issues, style problems, and get "
    "actionable improvement suggestions. Supports Python, TypeScript, JavaScript, Rust, and Go.",
    price="0.03",
)
def run(input: dict) -> dict:
    """
    Review code and return structured feedback.

    Input:
        code: str - The code to review
        language: str - Programming language (auto-detected if not provided)
        focus: list[str] - Areas to focus on: "bugs", "security", "style", "performance"
        context: str - Additional context about the code (optional)

    Output:
        issues: list[dict] - Found issues with severity, line, description, suggestion
        summary: str - Overall assessment
        score: int - Code quality score (0-100)
        suggestions: list[str] - General improvement suggestions
    """
    code = input.get("code")
    if not code:
        return {"error": "Missing required field: code"}

    language = input.get("language", "auto")
    focus = input.get("focus", ["bugs", "security", "style", "performance"])
    context = input.get("context", "")

    # Validate focus areas
    valid_focus = {"bugs", "security", "style", "performance"}
    focus = [f for f in focus if f in valid_focus] or list(valid_focus)

    client = get_openai_client()

    # Build the review prompt
    focus_instructions = "\n".join(
        [
            f"- {f.upper()}: {'Check for logical errors and potential bugs' if f == 'bugs' else ''}"
            f"{'Check for security vulnerabilities (injection, XSS, etc.)' if f == 'security' else ''}"
            f"{'Check code style, readability, and best practices' if f == 'style' else ''}"
            f"{'Check for performance issues and optimization opportunities' if f == 'performance' else ''}"
            for f in focus
        ]
    )

    system_prompt = f"""You are an expert code reviewer. Analyze the provided code and return a structured review.

Language hint: {language}
Focus areas:
{focus_instructions}

{"Additional context: " + context if context else ""}

Return your response as valid JSON with this structure:
{{
    "issues": [
        {{
            "severity": "critical|high|medium|low",
            "category": "bug|security|style|performance",
            "line": <line number or null>,
            "description": "What the issue is",
            "suggestion": "How to fix it"
        }}
    ],
    "summary": "Overall assessment of the code quality",
    "score": <0-100>,
    "suggestions": ["General improvement suggestion 1", ...]
}}

Be specific and actionable. Reference line numbers when possible."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Review this code:\n\n```\n{code}\n```"},
        ],
        temperature=0.3,  # Lower temperature for more consistent analysis
        response_format={"type": "json_object"},
    )

    try:
        import json

        result = json.loads(response.choices[0].message.content)

        # Validate and normalize the response
        issues = result.get("issues", [])
        for issue in issues:
            # Ensure required fields
            issue.setdefault("severity", "medium")
            issue.setdefault("category", "style")
            issue.setdefault("line", None)
            issue.setdefault("description", "")
            issue.setdefault("suggestion", "")

        # Sort issues by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 2))

        return {
            "issues": issues,
            "summary": result.get("summary", "Code review completed."),
            "score": max(0, min(100, result.get("score", 50))),
            "suggestions": result.get("suggestions", []),
            "metadata": {
                "language": language,
                "focus_areas": focus,
                "issues_found": len(issues),
                "critical_count": sum(1 for i in issues if i["severity"] == "critical"),
                "high_count": sum(1 for i in issues if i["severity"] == "high"),
            },
        }
    except Exception as e:
        return {
            "error": f"Failed to parse review response: {str(e)}",
            "raw_response": response.choices[0].message.content,
        }


if __name__ == "__main__":
    # Local testing
    from seren_agent.testing import test_agent

    sample_code = '''
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item["price"] * item["quantity"]
    return total

def get_user_input():
    query = input("Enter SQL query: ")
    return f"SELECT * FROM users WHERE name = '{query}'"
'''

    result = test_agent(
        run,
        {"code": sample_code, "language": "python", "focus": ["bugs", "security"]},
        env={"OPENAI_API_KEY": "your-key-here"},
    )
    print(result)
