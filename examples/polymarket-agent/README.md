# Autonomous Polymarket Trading Agent

An autonomous agent that scans Polymarket prediction markets, estimates fair value with Claude, finds mispricing, sizes positions with Kelly criterion, and executes trades — all through Seren publishers. The agent pays for its own inference and data from its SerenBucks balance.

## Strategy

Every scan cycle (designed to run every 10 minutes via SerenCron):

1. **Scan** 500+ active markets via `polymarket-data`
2. **Research** each opportunity — weather (NOAA), sports (injury reports), crypto (on-chain), politics (polls) — via `perplexity`
3. **Estimate fair value** with Claude via `seren-models`
4. **Find mispricing** > 8% edge
5. **Size positions** with Kelly criterion (quarter-Kelly, max 6% bankroll)
6. **Execute** via `polymarket-trading-serenai`

If bankroll hits $0, the agent stops. It learned to survive.

## Publishers Used

| Publisher | Slug | Role | Cost |
| --------- | ---- | ---- | ---- |
| Polymarket Data | `polymarket-data` | Market scanning | Free |
| Polymarket Trading | `polymarket-trading-serenai` | Order execution | $0.005/order |
| Perplexity | `perplexity` | Real-time research | $0.01/query |
| SerenModels | `seren-models` | Fair value estimation (Claude) | Pay-per-use |
| SerenCron | `seren-cron` | Scheduling scan cycles | $0.0001/run |

## Prerequisites

1. **Seren CLI + MCP Server** — [serenorg/seren](https://github.com/serenorg/seren)
2. **Seren API Key** — `seren auth login`
3. **SerenBucks** — Fund your account (this is the agent's bankroll for API costs)
4. **Polymarket L2 credentials** — POLY_API_KEY, POLY_PASSPHRASE, POLY_SECRET

## Run Locally

```python
from agent import run
from seren_agent.testing import run_local

# Run one scan cycle with $50 bankroll
result = run_local(
    run,
    {
        "action": "scan",
        "bankroll": 50.0,
        "config": {
            "mispricing_threshold": 0.08,
            "max_kelly_fraction": 0.06,
            "max_markets_to_scan": 100,  # smaller for testing
        },
    },
    env_vars={
        "SEREN_API_KEY": "seren_...",
        "POLY_API_KEY": "...",
        "POLY_PASSPHRASE": "...",
    },
)

print(f"Markets scanned: {result['markets_scanned']}")
print(f"Opportunities found: {result['opportunities_found']}")
print(f"Trades executed: {len(result['trades_executed'])}")
print(f"Bankroll after: ${result['bankroll_after']}")

for trade in result["trades_executed"]:
    print(f"  {trade['side']} ${trade['size_usd']:.2f} on '{trade['question'][:60]}...'")
    print(f"    Edge: {trade['edge']:.1%} | Fair: {trade['fair_value']:.0%} vs Market: {trade['market_price']:.0%}")
```

Check positions:

```python
result = run_local(
    run,
    {"action": "positions"},
    env_vars={
        "SEREN_API_KEY": "seren_...",
        "POLY_API_KEY": "...",
        "POLY_PASSPHRASE": "...",
    },
)
```

## Configuration

Override defaults in the `config` field:

| Parameter | Default | Description |
| --------- | ------- | ----------- |
| `mispricing_threshold` | 0.08 | Minimum edge to trade (8%) |
| `max_kelly_fraction` | 0.06 | Max bankroll per trade (6%) |
| `kelly_divisor` | 4 | Kelly fraction divisor (quarter-Kelly) |
| `max_markets_to_scan` | 500 | Markets per cycle |
| `min_liquidity` | 1000 | Minimum market liquidity (USD) |
| `max_positions` | 20 | Max concurrent positions |
| `stop_loss_bankroll` | 0.0 | Stop trading if bankroll drops to this |

## Publish

```bash
seren agent template publish \
    --name "Polymarket Trader" \
    --code ./agent.py \
    --language python \
    --price 0.10 \
    --description "Autonomous prediction market trader using Kelly criterion" \
    --dependencies requests
```

## Schedule with SerenCron

Set up recurring scans every 10 minutes:

```python
# Schedule via MCP
call_publisher(
    publisher="seren-cron",
    method="POST",
    path="/jobs",
    body={
        "schedule": "*/10 * * * *",
        "target": "https://gateway.serendb.com/v1/templates/polymarket-trader/invoke",
        "body": {"action": "scan", "bankroll": 50.0},
    },
)
```

## Actions

| Action | Input | What It Does |
| ------ | ----- | ------------ |
| `scan` | `bankroll`, `config` | Full scan-analyze-trade cycle |
| `positions` | — | Check open positions |
| `status` | — | Positions + current config |

## License

[MIT](../../LICENSE)
