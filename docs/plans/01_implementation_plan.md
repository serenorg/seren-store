# Seren Store: Implementation Plan

**For:** Engineers with zero codebase context
**Principles:** DRY, YAGNI, TDD, frequent commits

---

## Prerequisites

Before starting, ensure you have:
1. Access to `serenai-x402` repo (the existing gateway)
2. Access to `seren` repo (MCP tool)
3. Rust toolchain installed (`rustup`)
4. Docker (for Daytona testing)
5. GitHub CLI (`gh`) configured

### Key References
- Design spec: `docs/plans/00_design_spec.md`
- Existing gateway: `/Users/taariqlewis/Projects/Seren_Projects/serenai-x402`
- MCP tool: `github.com/serenorg/seren`

---

## Phase 1: Database Schema & Template Storage

### Task 1.1: Add Template Table Migration

**What:** Create database migration for storing agent templates.

**Files to touch:**
- `serenai-x402/gateway/src/db/migrations/` — new migration file

**Schema:**
```sql
CREATE TABLE agent_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publisher_id UUID NOT NULL REFERENCES publishers(id),
    slug VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    language VARCHAR(50) NOT NULL, -- 'python', 'typescript', 'rust'
    price DECIMAL(20, 8) NOT NULL,
    dependencies JSONB DEFAULT '[]',
    llm_config JSONB, -- encrypted API key if provided
    is_verified BOOLEAN DEFAULT FALSE,
    total_invocations INTEGER DEFAULT 0,
    successful_invocations INTEGER DEFAULT 0,
    unique_agents_served INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_templates_publisher ON agent_templates(publisher_id);
CREATE INDEX idx_templates_verified ON agent_templates(is_verified);
CREATE INDEX idx_templates_slug ON agent_templates(slug);
```

**How to test:**
1. Run migration: `sqlx migrate run`
2. Verify table exists: `\d agent_templates` in psql
3. Insert test row, verify constraints work

**TDD approach:**
1. Write test that expects table to exist
2. Run test (fails)
3. Create migration
4. Run test (passes)

**Commit:** `Add agent_templates table migration`

---

### Task 1.2: Template Repository Layer

**What:** Create Rust module for template CRUD operations.

**Files to touch:**
- `serenai-x402/gateway/src/db/templates.rs` — new file
- `serenai-x402/gateway/src/db/mod.rs` — add module export

**Functions needed:**
```rust
pub async fn create_template(pool: &PgPool, template: NewTemplate) -> Result<Template>
pub async fn get_template_by_id(pool: &PgPool, id: Uuid) -> Result<Option<Template>>
pub async fn get_template_by_slug(pool: &PgPool, slug: &str) -> Result<Option<Template>>
pub async fn list_templates(pool: &PgPool, filters: TemplateFilters) -> Result<Vec<Template>>
pub async fn update_template(pool: &PgPool, id: Uuid, updates: TemplateUpdate) -> Result<Template>
pub async fn increment_invocation_stats(pool: &PgPool, id: Uuid, success: bool) -> Result<()>
```

**How to test:**
1. Unit tests with test database
2. Test each CRUD operation
3. Test filters (by publisher, verified status, etc.)

**Commit:** `Add template repository layer`

---

## Phase 2: Publish API

### Task 2.1: Publish Endpoint

**What:** Create `POST /api/agents/publish` endpoint.

**Files to touch:**
- `serenai-x402/gateway/src/routes/agents.rs` — new file
- `serenai-x402/gateway/src/routes/mod.rs` — add module and route
- `serenai-x402/gateway/src/main.rs` — mount routes

**Request validation:**
```rust
#[derive(Deserialize, Validate)]
pub struct PublishRequest {
    #[validate(length(min = 1, max = 255))]
    name: String,
    description: Option<String>,
    #[validate(length(min = 1))]
    code: String,
    language: Language, // enum: Python, TypeScript, Rust
    #[validate(range(min = 0.0))]
    price: Decimal,
    dependencies: Option<Vec<String>>,
    llm_config: Option<LlmConfig>,
}
```

**Flow:**
1. Authenticate publisher (existing middleware)
2. Validate request
3. Generate slug from name (lowercase, hyphenated, unique)
4. Encrypt LLM API key if provided
5. Insert template
6. Return template ID and slug

**Security checks:**
- Publisher must be authenticated
- Code size limit (e.g., 1MB)
- Validate language is supported
- Sanitize dependencies list

**How to test:**
1. Test successful publish
2. Test validation failures (missing fields, invalid price)
3. Test duplicate slug handling
4. Test unauthenticated request rejected

**Commit:** `Add publish endpoint for agent templates`

---

### Task 2.2: Template Code Storage

**What:** Decide and implement code storage strategy.

**Options:**
1. Store in database (TEXT column) — simplest, use for MVP
2. Store in blob storage (S3/GCS) — better for large templates

**For MVP:** Use database. Code is in `agent_templates.code` column.

**Files to touch:**
- Already covered in 2.1

**How to test:**
- Publish template with substantial code
- Retrieve and verify code is intact

**Commit:** (Part of 2.1)

---

## Phase 3: Invoke API & Daytona Integration

### Task 3.1: Invoke Endpoint (Skeleton)

**What:** Create `POST /api/agents/:id/invoke` endpoint skeleton.

**Files to touch:**
- `serenai-x402/gateway/src/routes/agents.rs` — add invoke handler

**Request:**
```rust
#[derive(Deserialize)]
pub struct InvokeRequest {
    input: serde_json::Value, // dict → dict, minimal contract
}
```

**Headers:**
- `X-AGENT-WALLET` — consumer's wallet address (required)
- `X-LLM-API-KEY` — consumer's own LLM key (optional)
- `X-PAYMENT` — x402 payment header (existing)

**Flow (skeleton):**
1. Parse template ID from path
2. Fetch template from database
3. Validate payment (sufficient balance)
4. TODO: Execute in Daytona
5. Return result + cost breakdown

**How to test:**
1. Test template not found → 404
2. Test missing wallet header → 400
3. Test insufficient balance → 402
4. (Execution tested in 3.2)

**Commit:** `Add invoke endpoint skeleton`

---

### Task 3.2: Daytona Execution Service

**What:** Create service to run template code in Daytona sandbox.

**Files to touch:**
- `serenai-x402/gateway/src/services/daytona.rs` — new file
- `serenai-x402/gateway/src/services/mod.rs` — add module

**Check existing Daytona integration:**
Look in serenai-x402 for existing Daytona code. If exists, extend it. If not, create from scratch using Daytona SDK.

**Interface:**
```rust
pub struct DaytonaService {
    // connection to Daytona
}

impl DaytonaService {
    pub async fn execute(
        &self,
        code: &str,
        language: Language,
        dependencies: &[String],
        input: serde_json::Value,
        llm_config: Option<ResolvedLlmConfig>,
    ) -> Result<ExecutionResult>
}

pub struct ExecutionResult {
    output: serde_json::Value,
    execution_time_ms: u64,
    llm_tokens_used: Option<u64>,
}
```

**Security:**
- Sandbox timeout (e.g., 60 seconds max)
- Memory limit
- No network access except allowed LLM endpoints
- No filesystem persistence

**How to test:**
1. Test Python code execution with simple input/output
2. Test TypeScript execution
3. Test Rust execution
4. Test timeout handling
5. Test dependency installation

**Commit:** `Add Daytona execution service`

---

### Task 3.3: LLM Key Resolution

**What:** Implement the key hierarchy: User → Publisher → Seren.

**Files to touch:**
- `serenai-x402/gateway/src/services/llm.rs` — new file

**Logic:**
```rust
pub fn resolve_llm_key(
    user_key: Option<&str>,
    publisher_key: Option<&str>,
    seren_key: &str,
) -> ResolvedKey {
    // 1. Try user key if provided
    // 2. Try publisher key if provided
    // 3. Fall back to Seren key
    // Track which key was used for billing
}
```

**Credit exhaustion fallback:**
When a key fails due to credit exhaustion (not auth failure), try the next in hierarchy.

**How to test:**
1. Test user key used when provided
2. Test publisher key used when user key missing
3. Test Seren key used when both missing
4. Test fallback on credit exhaustion error

**Commit:** `Add LLM key resolution with fallback`

---

### Task 3.4: Complete Invoke Flow

**What:** Wire everything together in invoke endpoint.

**Files to touch:**
- `serenai-x402/gateway/src/routes/agents.rs` — complete invoke handler

**Flow:**
1. Validate payment, reserve funds
2. Resolve LLM key
3. Execute in Daytona
4. Calculate costs (compute time + LLM tokens)
5. Finalize payment (deduct actual cost)
6. Credit publisher their fee
7. Update invocation stats
8. Return result + cost breakdown

**Error handling:**
- Execution failure → refund consumer, log error
- Timeout → refund, return error
- LLM failure → try fallback key, if all fail → refund

**How to test:**
1. End-to-end test: publish template, invoke, verify result
2. Test cost calculation accuracy
3. Test publisher credited correctly
4. Test refund on failure

**Commit:** `Complete invoke flow with billing`

---

## Phase 4: Publisher Account Management

### Task 4.1: Verification Status

**What:** Add verified flag and subscription tracking.

**Files to touch:**
- `serenai-x402/gateway/src/db/migrations/` — add columns to publishers
- `serenai-x402/gateway/src/db/publishers.rs` — update queries

**Schema additions:**
```sql
ALTER TABLE publishers ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE publishers ADD COLUMN verified_at TIMESTAMPTZ;
ALTER TABLE publishers ADD COLUMN verification_expires_at TIMESTAMPTZ;
```

**How to test:**
1. Test setting verified status
2. Test verification expiry check

**Commit:** `Add publisher verification status`

---

### Task 4.2: KYC Threshold Check

**What:** Track cumulative payouts, require KYC at $300.

**Files to touch:**
- `serenai-x402/gateway/src/db/migrations/` — add payout tracking
- `serenai-x402/gateway/src/services/payouts.rs` — threshold logic

**Schema:**
```sql
ALTER TABLE publishers ADD COLUMN total_payouts DECIMAL(20, 8) DEFAULT 0;
ALTER TABLE publishers ADD COLUMN kyc_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE publishers ADD COLUMN kyc_completed_at TIMESTAMPTZ;
```

**Logic:**
- Before processing payout, check if `total_payouts + pending_payout > 300`
- If yes and `kyc_completed = false`, block payout, notify publisher

**How to test:**
1. Test payout under $300 → succeeds without KYC
2. Test payout pushing over $300 → blocked if no KYC
3. Test payout after KYC → succeeds

**Commit:** `Add KYC threshold check for payouts`

---

## Phase 5: SDKs

### Task 5.1: Python SDK

**What:** Create `seren-store` Python package.

**New repo or directory:** `seren-store-python/` (or subdirectory of seren-store)

**Structure:**
```
seren_store/
  __init__.py
  client.py      # API client
  template.py    # @agent decorator
  cli.py         # CLI commands
pyproject.toml
README.md
```

**Features:**
- `@agent` decorator for defining templates
- `seren test` — test template locally in Daytona
- `seren publish` — upload to marketplace

**Example usage:**
```python
from seren_store import agent

@agent(name="Web Researcher", price=0.05)
def web_researcher(input: dict) -> dict:
    # implementation
    return {"result": "..."}
```

**How to test:**
1. Unit tests for client
2. Integration test: decorate function, publish, invoke
3. CLI tests with subprocess

**Commit:** `Add Python SDK with test and publish commands`

---

### Task 5.2: TypeScript SDK

**What:** Create `@seren-store/sdk` npm package.

**Structure:**
```
src/
  index.ts
  client.ts
  template.ts
  cli.ts
package.json
tsconfig.json
```

**Same features as Python SDK.**

**Commit:** `Add TypeScript SDK`

---

### Task 5.3: Rust SDK

**What:** Create `seren-store` Rust crate.

**Structure:**
```
src/
  lib.rs
  client.rs
  template.rs
Cargo.toml
```

**Use proc macro for `#[agent]` attribute.**

**Commit:** `Add Rust SDK`

---

## Phase 6: First-Party Agents

### Task 6.1: Web Researcher Agent

**What:** Build and publish the Web Researcher showcase agent.

**Files:** New directory `agents/web-researcher/`

**Implementation:**
- Uses web search API (existing x402 publishers?)
- Synthesizes results with LLM
- Returns structured summary + sources

**How to test:**
1. Unit tests with mocked search
2. Integration test with real search API
3. Invoke via API, verify output structure

**Commit:** `Add Web Researcher first-party agent`

---

### Task 6.2: Code Reviewer Agent

**What:** Build Code Reviewer agent.

**Files:** `agents/code-reviewer/`

**Implementation:**
- Accepts code as input
- Analyzes for bugs, style issues, security
- Returns findings with line references

**Commit:** `Add Code Reviewer first-party agent`

---

### Task 6.3: Document Processor Agent

**What:** Build Document Processor agent.

**Files:** `agents/document-processor/`

**Implementation:**
- Accepts document (text, PDF via extraction)
- Extracts key information
- Returns structured data + summary

**Commit:** `Add Document Processor first-party agent`

---

### Task 6.4: Job Application Seeker Agent

**What:** Build Job Application Seeker agent.

**Files:** `agents/job-seeker/`

**Implementation:**
- Accepts career profile/resume
- Searches job boards
- Returns matching jobs, can initiate applications

**Commit:** `Add Job Application Seeker first-party agent`

---

## Phase 7: Analytics

### Task 7.1: Publisher Analytics Endpoint

**What:** Endpoint for publishers to view their stats.

**Files:**
- `serenai-x402/gateway/src/routes/analytics.rs` — extend existing or create

**Endpoint:** `GET /api/publishers/me/analytics`

**Returns:**
- Total invocations (by day/week/month)
- Revenue earned
- Error rates
- Average latency
- Top consuming agents

**How to test:**
1. Create invocations, verify counts
2. Test date range filtering

**Commit:** `Add publisher analytics endpoint`

---

## Phase 8: Catalog Updates

### Task 8.1: Update Catalog for Templates

**What:** Extend existing catalog to include agent templates.

**Files:**
- `serenai-x402/gateway/src/routes/catalog.rs` — add template listing

**Endpoints:**
- `GET /api/catalog/agents` — list agent templates
- `GET /api/catalog/agents/:slug` — get template details

**How to test:**
1. Publish template, verify appears in catalog
2. Test filtering by verified, category, price

**Commit:** `Add agent templates to catalog`

---

### Task 8.2: Update MCP Tool

**What:** Add template discovery/invoke to MCP tool.

**Files:** In `serenorg/seren` repo

**New tools:**
- `list_agent_templates` — query catalog
- `invoke_agent` — call an agent template

**Commit:** `Add agent template tools to MCP server`

---

## Testing Strategy

### Unit Tests
- Every function gets unit tests
- Mock external services (Daytona, LLM APIs) for unit tests

### Integration Tests
- Test full flows with real database
- Use test Daytona instance

### End-to-End Tests
- Publish → Invoke → Verify result
- Payment flow validation

### Security Tests
- Attempt sandbox escape
- Attempt to access other templates' data
- Test rate limiting
- Test payment replay protection

---

## Deployment Checklist

Before deploying each phase:
1. All tests pass
2. Migrations reviewed
3. Security review completed
4. Documentation updated
5. Monitoring/alerts configured
