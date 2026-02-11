# ABOUTME: Client for Seren Notes publisher via Seren Gateway.
# ABOUTME: Stores unstructured context for AI-readable task memory.

import os
import requests
from typing import Optional, List
from datetime import datetime
import json

SEREN_GATEWAY = os.environ.get("SEREN_GATEWAY_URL", "https://api.serendb.com/agent/api")
SEREN_NOTES_SLUG = "seren-notes"


def _call_notes_api(method: str, path: str, payload: Optional[dict] = None) -> dict:
    """Call Seren Notes via Seren Gateway."""
    api_key = os.environ.get("SEREN_API_KEY")
    if not api_key:
        return {"error": "SEREN_API_KEY environment variable not set"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    url = f"{SEREN_GATEWAY}/{SEREN_NOTES_SLUG}{path}"

    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=payload if method in ("POST", "PUT", "PATCH") else None,
        )

        if not response.ok:
            return {"error": response.text, "status": response.status_code}

        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}


def log_context_note(
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    parent_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    """
    Log an unstructured context note for AI-readable memory.

    Used for:
    - Recording context about why a task was created
    - Logging user override patterns for learning
    - Storing email/calendar context that informed decisions

    Args:
        title: Note title
        content: Note content (markdown supported)
        tags: List of tags for organization (default: ["workflow-context"])
        parent_id: Optional parent note ID for hierarchy
        idempotency_key: Optional key for safe retries

    Returns:
        API response dict with note data or error
    """
    payload = {
        "title": title,
        "content": content,
        "format": "markdown",
        "tags": tags or ["workflow-context"],
    }

    if parent_id:
        payload["parent_id"] = parent_id
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key

    return _call_notes_api("POST", "/notes", payload)


def append_to_note(note_id: str, content: str) -> dict:
    """
    Append content to an existing note.

    Useful for streaming/incremental updates without replacing entire note.

    Args:
        note_id: UUID of note to append to
        content: Content to append

    Returns:
        API response dict
    """
    return _call_notes_api("POST", f"/notes/{note_id}/append", {"content": content})


def search_context(query: str, limit: int = 10) -> dict:
    """
    Search context notes for relevant past information.

    Args:
        query: Full-text search query
        limit: Maximum results to return (default: 10)

    Returns:
        API response dict with matching notes
    """
    return _call_notes_api("GET", f"/notes/search?query={query}&limit={limit}")


def get_note(note_id: str) -> dict:
    """
    Retrieve a specific note by ID.

    Args:
        note_id: UUID of note

    Returns:
        API response dict with note data
    """
    return _call_notes_api("GET", f"/notes/{note_id}")


def list_notes(
    parent_id: Optional[str] = None,
    tag: Optional[str] = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    List notes with optional filters.

    Args:
        parent_id: Filter by parent note
        tag: Filter by tag
        include_archived: Include archived notes
        limit: Maximum results (default: 50, max: 100)
        offset: Pagination offset

    Returns:
        API response dict with notes list
    """
    params = [f"limit={limit}", f"offset={offset}"]
    if parent_id:
        params.append(f"parent_id={parent_id}")
    if tag:
        params.append(f"tag={tag}")
    if include_archived:
        params.append("include_archived=true")

    return _call_notes_api("GET", f"/notes?{'&'.join(params)}")


def list_notes_by_tag(tag: str, limit: int = 50) -> dict:
    """
    List notes filtered by tag.

    Args:
        tag: Tag to filter by
        limit: Maximum results

    Returns:
        API response dict with notes list
    """
    return list_notes(tag=tag, limit=limit)


def update_note(
    note_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    is_archived: Optional[bool] = None,
    is_pinned: Optional[bool] = None,
    expected_version: Optional[int] = None,
) -> dict:
    """
    Update a note.

    Args:
        note_id: UUID of note to update
        title: New title (optional)
        content: New content (optional)
        is_archived: Archive status (optional)
        is_pinned: Pin status (optional)
        expected_version: For optimistic concurrency control (optional)

    Returns:
        API response dict
    """
    payload = {}
    if title is not None:
        payload["title"] = title
    if content is not None:
        payload["content"] = content
    if is_archived is not None:
        payload["is_archived"] = is_archived
    if is_pinned is not None:
        payload["is_pinned"] = is_pinned
    if expected_version is not None:
        payload["expected_version"] = expected_version

    return _call_notes_api("PATCH", f"/notes/{note_id}", payload)


def delete_note(note_id: str) -> dict:
    """
    Permanently delete a note.

    Args:
        note_id: UUID of note to delete

    Returns:
        API response dict
    """
    return _call_notes_api("DELETE", f"/notes/{note_id}")


def list_tags() -> dict:
    """
    List all unique tags across notes.

    Returns:
        API response dict with tags list
    """
    return _call_notes_api("GET", "/notes/tags")


def add_tags(note_id: str, tags: List[str]) -> dict:
    """
    Add tags to a note.

    Args:
        note_id: UUID of note
        tags: Tags to add

    Returns:
        API response dict
    """
    return _call_notes_api("POST", f"/notes/{note_id}/tags", {"tags": tags})


def remove_tags(note_id: str, tags: List[str]) -> dict:
    """
    Remove tags from a note.

    Args:
        note_id: UUID of note
        tags: Tags to remove

    Returns:
        API response dict
    """
    return _call_notes_api("DELETE", f"/notes/{note_id}/tags", {"tags": tags})


def log_user_override(task_id: str, original: dict, override: dict, user_id: str) -> dict:
    """
    Log when user modifies or dismisses AI-suggested tasks.

    This helps the learning system understand user preferences.

    Args:
        task_id: ID of the task that was overridden
        original: Original AI-suggested task data
        override: Task data after user modification
        user_id: User identifier

    Returns:
        API response dict
    """
    return log_context_note(
        title=f"User override: {original.get('title', 'Unknown task')}",
        content=f"""## Override Details

**Task ID:** {task_id}
**User:** {user_id}
**Timestamp:** {datetime.now().isoformat()}

## Original (AI-suggested)
```json
{json.dumps(original, indent=2)}
```

## After Override
```json
{json.dumps(override, indent=2)}
```

## Learning Signal
- If dismissed: User found this type of signal non-actionable
- If priority changed: User's urgency perception differs from AI
- If due date changed: User has context AI doesn't have
""",
        tags=["learning", "user-override", f"user:{user_id}"],
    )


def get_relevant_context(query: str, user_id: str, limit: int = 5) -> str:
    """
    Search past context notes to inform AI decisions.

    Args:
        query: Search query for relevant context
        user_id: User identifier to scope search
        limit: Maximum notes to return

    Returns:
        Formatted string of relevant context snippets
    """
    results = search_context(f"{query} user:{user_id}", limit=limit)

    if "error" in results:
        return ""

    context_snippets = []
    for note in results.get("data", []):
        context_snippets.append(f"## {note['title']}\n{note['content'][:500]}")

    return "\n\n---\n\n".join(context_snippets)
