# Daily Workflow Agent

A task management agent that extracts actionable items from email and calendar, manages follow-ups, and delivers daily digests with intelligent prioritization.

## Features

- **AI Task Extraction**: Automatically extracts tasks from emails and calendar events
- **Smart Prioritization**: Uses Claude AI to determine task priority and urgency
- **Daily Digests**: Morning summary of overdue, due today, and upcoming tasks
- **Configurable Autonomy**: Control which actions the agent takes automatically vs. with approval
- **Duplicate Detection**: Semantic similarity checks prevent duplicate tasks
- **Reminder System**: Scheduled reminders with configurable notification channels

## Pricing

**$0.005 per invocation** (~$3/month for moderate usage)

Uses Haiku for routine tasks and Sonnet for complex reasoning, achieving 95% cost reduction compared to flat-rate alternatives.

## Usage

### Input Types

#### 1. Signal Processing

Process incoming signals from email, calendar, or manual input:

```python
{
    "type": "signal",
    "source": "email",  # or "calendar", "manual"
    "user_id": "user-123",
    "payload": {
        "from": "john@example.com",
        "subject": "Meeting follow-up",
        "body": "Can you send the pricing doc by Friday?"
    }
}
```

#### 2. Daily Digest

Generate a morning task summary:

```python
{
    "type": "digest",
    "user_id": "user-123"
}
```

#### 3. Action Execution

Execute a specific action:

```python
{
    "type": "action",
    "action_type": "create_task",  # complete_task, reschedule_task, etc.
    "user_id": "user-123",
    "payload": {
        "title": "Review contract",
        "priority": "high",
        "due_date": "2026-01-25T17:00:00"
    }
}
```

#### 4. Query Tasks/Reminders

Query existing tasks or reminders:

```python
{
    "type": "query",
    "query_type": "tasks",  # or "reminders"
    "user_id": "user-123",
    "filters": {
        "status": "pending",
        "due_before": "2026-01-31T23:59:59"
    }
}
```

### Output Examples

**Signal Processing Response:**
```json
{
    "status": "processed",
    "tasks_created": 2,
    "tasks": [
        {"title": "Send pricing doc", "priority": "medium", "due_date": "2026-01-24"},
        {"title": "Schedule follow-up call", "priority": "low"}
    ],
    "duplicates_skipped": 0
}
```

**Daily Digest Response:**
```json
{
    "status": "generated",
    "digest": "📋 Your Day — Monday, January 20\n\nDUE TODAY\n• Send pricing doc to Acme Corp\n...",
    "summary": {
        "overdue_count": 1,
        "due_today_count": 3,
        "upcoming_count": 5
    }
}
```

## Autonomy Levels

Configure how autonomous the agent is for each action type:

| Level | Behavior |
|-------|----------|
| `auto` | Execute immediately, log for review |
| `suggest` | Propose action, await approval |
| `confirm` | Queue action, ask before executing |
| `manual` | Feature available but agent won't trigger |

**Default Settings:**
- `create_task`: auto
- `complete_task`: confirm
- `reschedule_task`: suggest
- `create_event`: suggest
- `send_reply`: manual (always requires human approval)

## Local Development

```bash
# Install dependencies
pip install seren-agent httpx

# Set environment variables
export ANTHROPIC_API_KEY=your-key
export SEREN_API_KEY=your-seren-key
export SEREN_API_URL=https://api.serendb.com

# Run locally
python agent.py
```

## Testing

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_models.py -v
```

## Publishing to Seren Store

```bash
seren agent template publish \
    --name "Daily Workflow Agent" \
    --code ./agent.py \
    --language python \
    --price 0.005
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 DAILY WORKFLOW AGENT                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────┐ │
│  │ Orchestrator│───▶│ Signal Processor │───▶│ Actions │ │
│  │ (Seren-Cron)│    │  (Claude AI)     │    │ (CRUD)  │ │
│  └─────────────┘    └──────────────────┘    └─────────┘ │
│         │                    │                   │      │
│         └────────────────────┼───────────────────┘      │
│                              ▼                          │
│                    ┌──────────────────┐                 │
│                    │    SerenDB       │                 │
│                    │ (Task Storage)   │                 │
│                    └──────────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Main entry point with @agent decorator |
| `models.py` | Data models (Task, Reminder, Signal, etc.) |
| `signals.py` | Signal processing and task extraction |
| `actions.py` | Action execution with autonomy levels |
| `notifications.py` | Notification formatting and delivery |
| `config.py` | Autonomy config, scheduling, model routing |

## Dependencies

- `seren-agent`: Seren Agent SDK
- `httpx`: HTTP client for API calls
- Claude API access (via Seren Models publisher)

## Cost Breakdown

| Activity | Frequency | Model | Est. Cost |
|----------|-----------|-------|-----------|
| Morning digest | 1x/day | Haiku | $0.0015 |
| Email processing | 10x/day | Haiku | $0.015 |
| Calendar processing | 3x/day | Haiku | $0.0045 |
| Priority decisions | 2x/day | Sonnet | $0.01 |
| **Daily Total** | | | **~$0.04** |
| **Monthly Estimate** | | | **~$1.30** |

## License

MIT License - Copyright (c) 2026 SerenAI Software, Inc.
