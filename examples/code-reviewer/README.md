# Code Reviewer Agent

Analyze code for bugs, security issues, style problems, and get actionable
improvement suggestions.

## Usage

```python
# Input
{
    "code": "def foo():\n    ...",
    "language": "python",           # optional, auto-detected
    "focus": ["bugs", "security"],  # optional: bugs, security, style, performance
    "context": "This is a payment processing function"  # optional
}

# Output
{
    "issues": [
        {
            "severity": "critical",
            "category": "security",
            "line": 5,
            "description": "SQL injection vulnerability",
            "suggestion": "Use parameterized queries"
        }
    ],
    "summary": "The code has 2 critical issues...",
    "score": 45,
    "suggestions": [
        "Consider using type hints",
        "Add input validation"
    ],
    "metadata": {
        "language": "python",
        "focus_areas": ["bugs", "security"],
        "issues_found": 3,
        "critical_count": 1,
        "high_count": 1
    }
}
```

## Supported Languages

- Python
- TypeScript
- JavaScript
- Rust
- Go

## Pricing

- **$0.03 per invocation**

## Focus Areas

| Area | Description |
|------|-------------|
| `bugs` | Logical errors, edge cases, potential runtime errors |
| `security` | SQL injection, XSS, authentication issues, secrets exposure |
| `style` | Code formatting, naming conventions, readability |
| `performance` | Inefficient algorithms, unnecessary operations, memory issues |

## Local Testing

```bash
cd examples/code-reviewer
OPENAI_API_KEY=your-key python agent.py
```
