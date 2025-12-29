# Seren Store: Design Specification

**Version:** 1.0
**Date:** December 29, 2025
**Status:** Approved

---

## 1. Overview

Seren Store is an agent-to-agent marketplace where publishers monetize agent templates and consuming agents invoke them via x402 micropayments.

**Core principle:** Bring Your Own Code — framework-agnostic (Python, TypeScript, Rust, LangGraph, CrewAI, raw code). The only requirement: implement `run(input) → output` that executes in a Daytona sandbox.

---

## 2. Business Model

### Revenue
- **Compute pass-through only** — Seren takes no cut of publisher fees
- Revenue from Daytona execution time and LLM costs (when using Seren's keys)
- Annual subscription for Seren Verified status

### Publisher Payouts
- Serendb account with wallet or bank payout
- KYC triggers at $300 in earnings (not before)

### Two-Tiered Trust System

| Tier | Requirements | Trust Signal |
|------|--------------|--------------|
| **Open Marketplace** | Wallet address only, pseudonymous | Computed from metrics (transactions, success rate, unique agents) |
| **Seren Verified** | KYC, annual subscription | Badge, curated quality |

---

## 3. Technical Architecture

### Stack
- **Backend:** Rust (extends serenai-x402 gateway)
- **SDKs:** Python, TypeScript, Rust (polyglot)
- **Execution:** Daytona sandboxes
- **Payments:** x402 micropayments (production-ready)
- **Discovery:** REST catalog + MCP tool (already exist)

### Existing Infrastructure (Production-Ready)
- x402 payment gateway (serenai-x402)
- Daytona sandbox integration
- Catalog endpoints (`/api/catalog/`)
- MCP tool (serenorg/seren)

### New Components Required
- Template storage (code + metadata)
- Publish API (`POST /api/agents/publish`)
- Invoke API (`POST /api/agents/:id/invoke`)
- Publisher account management
- SDKs (Python, TypeScript, Rust)
- Analytics dashboard

---

## 4. Execution Flow

```
1. Publisher: POST /api/agents/publish
   - Upload template code + metadata
   - Set price, description

2. Consumer Agent: POST /api/agents/:id/invoke
   - x402 payment header
   - Input payload
   - Optional: own LLM API key

3. Seren Store:
   - Validate payment (sufficient balance)
   - Spin up Daytona sandbox (cold start default)
   - Install dependencies, run template
   - Return output + cost breakdown
   - Credit publisher, deduct from consumer
```

### Execution Model
- **Default:** Cold start per invocation (fresh sandbox each time)
- **Optimization:** Warm pool for high-traffic verified agents only

### LLM Key Resolution
Order: User key → Publisher key → Seren key

Seren key is fallback when other keys are **out of credits** (not just unprovided).

---

## 5. Security Requirements

### Sandbox Isolation
- All agent code runs in Daytona sandboxes (isolated environments)
- No access to host filesystem, network restrictions
- Templates cannot exfiltrate data or access other templates

### Input Validation
- Validate all inputs before passing to sandbox
- Size limits on input payloads
- Rate limiting per agent wallet

### Secret Management
- Publisher API keys encrypted at rest
- LLM keys never logged or exposed in responses
- Audit trail for all key usage

### Payment Security
- x402 EIP-3009 signature verification
- Nonce tracking to prevent replay attacks
- Balance checks before execution

### Publisher Verification
- KYC at $300 threshold for payout security
- Verified tier requires identity verification
- Ability to block malicious publishers

### Audit & Monitoring
- Log all invocations (without sensitive data)
- Monitor for abuse patterns
- Alert on unusual activity (high error rates, cost spikes)

---

## 6. API Design

### Publish Template

```
POST /api/agents/publish
Authorization: Bearer <publisher_api_key>

{
  "name": "Web Researcher",
  "description": "Deep web search and synthesis",
  "code": "<base64 encoded or raw>",
  "language": "python" | "typescript" | "rust",
  "price": "0.05",
  "dependencies": ["requests", "openai"],
  "llmConfig": {
    "provider": "openai",
    "model": "gpt-4o",
    "apiKey": "sk-..." // optional, encrypted
  }
}
```

### Invoke Agent

```
POST /api/agents/:id/invoke
X-AGENT-WALLET: 0x...
X-LLM-API-KEY: sk-... // optional

{
  "input": { ... }
}
```

### Response

```json
{
  "result": { ... },
  "cost": {
    "publisherFee": "0.05",
    "llmCost": "0.032",
    "computeCost": "0.008",
    "total": "0.09",
    "llmKeyUsed": "user" | "publisher" | "seren"
  }
}
```

### Template Contract
- **Minimal:** `input: dict → output: dict`
- No enforced JSON schema
- Agents are flexible interpreters

### Versioning
- **Latest always** — each publish replaces previous
- No version numbers, no pinning
- Breaking changes are publisher's responsibility

---

## 7. Publisher Experience

### SDK/CLI (Minimal at Launch)
```bash
pip install seren-store  # or npm, cargo

seren test    # Run template in Daytona sandbox
seren publish # Package and upload to marketplace
```

Future additions: `seren init` (scaffold), `seren dev` (hot reload)

### Analytics
Publishers see:
- Invocation counts
- Revenue
- Error rates
- Latency metrics

---

## 8. Consumer (Agent) Experience

### Discovery
- REST: `GET /api/catalog/` with filters
- MCP: Native tools (`list_agents`, `get_agent_details`, `invoke_agent`)

### Trust Signals (Programmatic)
- Transaction volume
- Unique agents served
- Success/error rates
- Latency metrics
- Verified badge

---

## 9. First-Party Agents (Launch)

| Agent | Description |
|-------|-------------|
| **Web Researcher** | Deep search and synthesis |
| **Code Reviewer** | Analyze code, find bugs, suggest fixes |
| **Document Processor** | Extract, structure, summarize docs |
| **Job Application Seeker** | Search and apply for matching jobs |

---

## 10. Decision Summary

| Decision | Choice |
|----------|--------|
| MVP scope | Full launch, all features |
| Infrastructure | x402 + Daytona production-ready |
| Revenue model | Compute pass-through only |
| Verified tier | Annual subscription |
| Publisher payouts | Serendb account, KYC at $300 |
| Versioning | Latest always |
| Schema enforcement | Minimal (dict → dict) |
| Execution model | Cold start default, warm pool for high-traffic |
| Backend language | Rust |
| SDKs | Python, TypeScript, Rust |
| CLI at launch | Minimal (test + publish) |
| LLM key fallback | User → Publisher → Seren (on credit exhaustion) |
| First-party agents | 4 showcase agents |
