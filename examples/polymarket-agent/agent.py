# ABOUTME: Autonomous Polymarket trading agent that finds mispriced prediction markets.
# ABOUTME: Uses Claude for fair value estimation, Kelly criterion for sizing, and self-funds from profits.
"""
Polymarket Trading Agent

Strategy:
  1. Scan active markets via polymarket-data publisher
  2. Research each market category (weather, sports, crypto, politics) with Perplexity
  3. Build fair value estimates with Claude via seren-models
  4. Find mispricing > threshold (default 8%)
  5. Size positions with Kelly criterion (max 6% bankroll)
  6. Execute trades via polymarket-trading-serenai publisher
  7. Track balance — if bankroll hits $0, agent stops

The agent pays for its own inference and data from its SerenBucks balance.
Runs on Daytona. Scheduled externally (e.g., SerenCron every 10 minutes).
"""

import json
import os
import math

from seren_agent import agent


# --- Configuration ---

DEFAULT_CONFIG = {
    "mispricing_threshold": 0.08,   # 8% edge required to trade
    "max_kelly_fraction": 0.06,     # Max 6% of bankroll per trade
    "kelly_divisor": 4,             # Quarter-Kelly for safety
    "max_markets_to_scan": 500,     # Markets per scan cycle
    "min_liquidity": 1000,          # Minimum market liquidity in USD
    "max_positions": 20,            # Max concurrent positions
    "stop_loss_bankroll": 0.0,      # Stop if bankroll hits this
}


# --- Publisher Interface ---

def seren_call(publisher, **kwargs):
    """Call a Seren publisher through the gateway."""
    import requests

    headers = {
        "Authorization": f"Bearer {os.environ['SEREN_API_KEY']}",
        "Content-Type": "application/json",
    }
    for key in ("POLY_API_KEY", "POLY_PASSPHRASE", "POLY_SIGNATURE",
                "POLY_TIMESTAMP", "POLY_NONCE", "POLY_ADDRESS"):
        val = os.environ.get(key)
        if val:
            headers[key] = val

    base = "https://gateway.serendb.com/v1/publishers"
    url = f"{base}/{publisher}"

    if "query" in kwargs:
        url += "/query"
        return requests.post(url, headers=headers,
                             json={"query": kwargs["query"]}).json()

    if "path" in kwargs:
        url += kwargs["path"]

    method = kwargs.get("method", "GET")
    body = kwargs.get("body")
    resp = requests.request(method, url, headers=headers, json=body)
    return resp.json()


# --- Market Scanning ---

def scan_markets(limit=500):
    """Pull active markets from Polymarket."""
    markets = seren_call(
        "polymarket-data",
        path=f"/markets?limit={limit}&active=true&order=liquidity&ascending=false",
    )
    return markets if isinstance(markets, list) else markets.get("data", [])


def get_order_book(token_id):
    """Get order book depth for a token."""
    return seren_call(
        "polymarket-trading-serenai",
        path=f"/book?token_id={token_id}",
    )


def get_positions():
    """Get current open positions."""
    return seren_call("polymarket-trading-serenai", path="/positions")


# --- Research ---

def research_market(market_question, market_category):
    """Research a market using Perplexity for up-to-date information."""
    category_prompts = {
        "weather": f"Latest NOAA forecast and weather data relevant to: {market_question}",
        "sports": f"Latest injury reports, team news, and betting odds for: {market_question}",
        "crypto": f"Latest on-chain metrics, sentiment analysis, and news for: {market_question}",
        "politics": f"Latest polls, expert analysis, and news for: {market_question}",
    }
    prompt = category_prompts.get(
        market_category,
        f"Latest information and expert analysis for: {market_question}",
    )

    result = seren_call(
        "perplexity",
        method="POST",
        path="/chat/completions",
        body={
            "model": "sonar",
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    choices = result.get("choices", [{}])
    return choices[0].get("message", {}).get("content", "") if choices else ""


# --- Fair Value Estimation ---

def estimate_fair_value(market, research_context):
    """Use Claude to estimate fair value probability for a market outcome."""
    prompt = f"""You are a prediction market analyst. Estimate the TRUE probability of this outcome.

Market: {market.get('question', '')}
Current price (implied probability): {market.get('price', 'unknown')}
Category: {market.get('category', 'unknown')}

Research context:
{research_context}

Respond with ONLY a JSON object:
{{"probability": 0.XX, "confidence": "high"|"medium"|"low", "reasoning": "one sentence"}}

Be calibrated. If uncertain, say confidence is "low"."""

    result = seren_call(
        "seren-models",
        method="POST",
        path="/v1/chat/completions",
        body={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

    try:
        # Strip markdown code fences if present
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        return {"probability": None, "confidence": "low", "reasoning": "parse error"}


# --- Position Sizing (Kelly Criterion) ---

def kelly_size(fair_prob, market_price, bankroll, config):
    """Calculate position size using fractional Kelly criterion.

    Kelly formula: f* = (bp - q) / b
    where b = odds, p = win probability, q = 1 - p

    Returns (side, size_usd) or (None, 0) if no edge.
    """
    threshold = config["mispricing_threshold"]
    max_fraction = config["max_kelly_fraction"]
    divisor = config["kelly_divisor"]

    # Determine if we should buy YES or NO
    if fair_prob > market_price + threshold:
        # YES is underpriced — buy YES
        p = fair_prob
        odds = (1.0 / market_price) - 1.0  # decimal odds minus 1
        side = "BUY"
    elif fair_prob < market_price - threshold:
        # NO is underpriced — buy NO (equivalent to selling YES)
        p = 1.0 - fair_prob
        odds = (1.0 / (1.0 - market_price)) - 1.0
        side = "SELL"
    else:
        return None, 0.0

    if odds <= 0:
        return None, 0.0

    q = 1.0 - p
    kelly_fraction = (odds * p - q) / odds

    if kelly_fraction <= 0:
        return None, 0.0

    # Fractional Kelly (divide by divisor for safety)
    fraction = min(kelly_fraction / divisor, max_fraction)
    size_usd = bankroll * fraction

    # Floor to 2 decimal places
    size_usd = math.floor(size_usd * 100) / 100

    if size_usd < 1.0:  # Minimum trade size
        return None, 0.0

    return side, size_usd


# --- Trade Execution ---

def execute_trade(token_id, side, size_usd, price):
    """Place an order on Polymarket via the trading publisher."""
    order = {
        "tokenID": token_id,
        "side": side,
        "price": str(price),
        "size": str(size_usd),
        "type": "GTC",  # Good-til-cancelled
    }

    result = seren_call(
        "polymarket-trading-serenai",
        method="POST",
        path="/order",
        body=order,
    )
    return result


# --- Categorization ---

def categorize_market(question):
    """Simple keyword-based market categorization."""
    q = question.lower()
    if any(w in q for w in ("weather", "temperature", "hurricane", "storm",
                             "rain", "snow", "noaa", "climate")):
        return "weather"
    if any(w in q for w in ("nfl", "nba", "mlb", "nhl", "soccer", "football",
                             "game", "match", "championship", "super bowl",
                             "world cup", "injury", "playoffs")):
        return "sports"
    if any(w in q for w in ("bitcoin", "ethereum", "crypto", "btc", "eth",
                             "token", "defi", "blockchain", "solana")):
        return "crypto"
    if any(w in q for w in ("election", "president", "senate", "congress",
                             "vote", "poll", "governor", "democrat",
                             "republican", "trump", "biden")):
        return "politics"
    return "general"


# --- Main Agent Loop ---

@agent(
    name="Polymarket Trader",
    description=(
        "Autonomous prediction market trader. Scans markets, estimates fair value "
        "with Claude, finds mispricing, sizes with Kelly criterion, and executes. "
        "Pays its own API costs from trading profits."
    ),
    price="0.10",
    compute_backend="daytona",
)
def run(input: dict) -> dict:
    """Run one scan-analyze-trade cycle.

    Input:
        action: "scan" (default) | "positions" | "status"
        bankroll: Current bankroll in USD (required for scan)
        config: Optional config overrides

    Output:
        trades_executed: list of trades made
        opportunities_found: number of mispriced markets
        markets_scanned: total markets checked
        bankroll_after: bankroll after trades
    """
    action = input.get("action", "scan")
    config = {**DEFAULT_CONFIG, **input.get("config", {})}

    if action == "positions":
        return {"positions": get_positions()}

    if action == "status":
        positions = get_positions()
        return {
            "positions": positions,
            "config": config,
        }

    # --- Scan Mode ---
    bankroll = input.get("bankroll")
    if not bankroll or bankroll <= config["stop_loss_bankroll"]:
        return {
            "error": "bankroll_depleted",
            "message": "Bankroll is zero or below stop-loss. Agent stopping.",
            "bankroll": bankroll,
        }

    # Check how many positions we already have
    current_positions = get_positions()
    position_count = len(current_positions) if isinstance(current_positions, list) else 0
    if position_count >= config["max_positions"]:
        return {
            "message": "Max positions reached. Waiting for exits.",
            "position_count": position_count,
            "max_positions": config["max_positions"],
        }

    # Scan markets
    markets = scan_markets(limit=config["max_markets_to_scan"])

    trades_executed = []
    opportunities = []

    for market in markets:
        question = market.get("question", "")
        if not question:
            continue

        # Get current price (implied probability)
        price = None
        for outcome in market.get("outcomes", []):
            if outcome.get("name", "").lower() == "yes":
                price = float(outcome.get("price", 0))
                token_id = outcome.get("token_id", "")
                break

        if price is None or price <= 0.01 or price >= 0.99:
            continue  # Skip extreme prices

        # Categorize and research
        category = categorize_market(question)
        research = research_market(question, category)

        # Estimate fair value
        estimate = estimate_fair_value(
            {"question": question, "price": price, "category": category},
            research,
        )

        fair_prob = estimate.get("probability")
        confidence = estimate.get("confidence", "low")

        if fair_prob is None or confidence == "low":
            continue

        # Check for mispricing and size the trade
        edge = abs(fair_prob - price)
        if edge < config["mispricing_threshold"]:
            continue

        side, size_usd = kelly_size(fair_prob, price, bankroll, config)
        if side is None:
            continue

        opportunity = {
            "question": question,
            "category": category,
            "market_price": price,
            "fair_value": fair_prob,
            "edge": round(edge, 4),
            "confidence": confidence,
            "side": side,
            "size_usd": size_usd,
            "reasoning": estimate.get("reasoning", ""),
        }
        opportunities.append(opportunity)

        # Execute if we have room for more positions
        if len(trades_executed) + position_count < config["max_positions"]:
            trade_price = price if side == "BUY" else (1.0 - price)
            result = execute_trade(token_id, side, size_usd, trade_price)
            opportunity["trade_result"] = result
            trades_executed.append(opportunity)
            bankroll -= size_usd

            if bankroll <= config["stop_loss_bankroll"]:
                break

    return {
        "markets_scanned": len(markets),
        "opportunities_found": len(opportunities),
        "trades_executed": trades_executed,
        "bankroll_after": round(bankroll, 2),
        "positions_held": position_count + len(trades_executed),
    }
