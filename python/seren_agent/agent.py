"""Agent decorator for Seren templates.

The @agent decorator marks a function as a Seren agent template. Templates
must implement the contract: run(input: dict) -> dict

The decorator is backend-agnostic - the same code runs on Daytona, Modal,
E2B, or any other supported compute backend.
"""

from typing import Callable, Optional
from functools import wraps


def agent(
    name: str,
    description: str = "",
    price: str = "0.01",
    compute_backend: Optional[str] = None,
) -> Callable:
    """Decorator to mark a function as a Seren agent template.

    Args:
        name: Display name for the agent in the store
        description: What the agent does (shown in catalog)
        price: Price per invocation in USD (e.g., "0.05" for 5 cents)
        compute_backend: Preferred execution backend. If None, uses store default.
            Options: "daytona", "modal", "e2b", etc.

    Returns:
        Decorated function with _seren_agent metadata

    Raises:
        ValueError: If name is empty or price is invalid

    Example:
        @agent(name="Code Analyzer", price="0.10", description="Analyzes code quality")
        def run(input: dict) -> dict:
            code = input["code"]
            # ... analysis logic ...
            return {"score": 85, "issues": [...]}
    """
    # Validate required parameters
    if not name or not name.strip():
        raise ValueError("Agent name is required and cannot be empty")

    if not price or not price.strip():
        raise ValueError("Agent price is required and cannot be empty")

    # Validate price format (should be a valid decimal string)
    try:
        price_float = float(price)
        if price_float < 0:
            raise ValueError("Agent price cannot be negative")
    except ValueError as e:
        if "could not convert" in str(e).lower():
            raise ValueError(f"Agent price must be a valid number, got: {price}")
        raise

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(input_data: dict) -> dict:
            return func(input_data)

        # Attach metadata for the Seren CLI and publishing tools
        wrapper._seren_agent = {
            "name": name.strip(),
            "description": description,
            "price": price,
            "compute_backend": compute_backend,
            "function_name": func.__name__,
        }

        return wrapper

    return decorator


def get_agent_metadata(func: Callable) -> Optional[dict]:
    """Extract Seren agent metadata from a decorated function.

    Args:
        func: A function potentially decorated with @agent

    Returns:
        Agent metadata dict or None if not a Seren agent
    """
    return getattr(func, "_seren_agent", None)


def is_seren_agent(func: Callable) -> bool:
    """Check if a function is a Seren agent template.

    Args:
        func: Function to check

    Returns:
        True if the function is decorated with @agent
    """
    return hasattr(func, "_seren_agent")
