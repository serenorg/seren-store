# Seren Models API Endpoint Documentation

**Publisher:** Seren Models
**Slug:** `seren-models`
**Publisher ID:** `cdece242-5a2b-4950-a0a5-1433891ca276`
**Base URL:** `https://openrouter.ai/api/v1` (via Seren Publisher)
**Billing Model:** x402 Passthrough (1.15x markup on OpenRouter pricing)

---

## Overview

Seren Models provides access to 200+ AI models from providers including OpenAI, Anthropic, Google, Meta, Mistral, Cohere, and more through a unified API interface. All endpoints use OpenRouter's infrastructure with x402 micropayment support.

**Authentication:** Handled by Seren Publisher (no API key needed for agents)

---

## Endpoints

### 1. Chat Completions

**Primary endpoint for AI model inference**

```
POST /chat/completions
```

**Description:** Send chat messages to any supported model and receive AI-generated responses. Supports streaming, function calling, and vision capabilities depending on the model.

**Request Body:**
```json
{
  "model": "anthropic/claude-sonnet-4-20250514",
  "messages": [
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**Response:**
```json
{
  "id": "gen-123",
  "model": "anthropic/claude-sonnet-4-20250514",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 8,
    "total_tokens": 23
  }
}
```

**Parameters:**
- `model` (required): Model identifier (e.g., `anthropic/claude-sonnet-4-20250514`)
- `messages` (required): Array of message objects with `role` and `content`
- `temperature`: Sampling temperature (0-2, default 1)
- `max_tokens`: Maximum tokens to generate
- `stream`: Enable streaming responses (boolean)
- `top_p`: Nucleus sampling parameter
- `frequency_penalty`: Penalize repeated tokens
- `presence_penalty`: Penalize tokens based on presence
- `tools`: Function calling tools (array)
- `tool_choice`: Control tool selection

**Use Cases:**
- General text generation and Q&A
- Code generation and analysis
- Content creation and editing
- Function calling and tool use
- Vision analysis (for supported models)

**Cost:** Varies by model (passthrough pricing + 15% markup)

---

### 2. List Models

**Get all available models and their properties**

```
GET /models
```

**Description:** Returns a list of all available AI models with their capabilities, pricing, context lengths, and provider information.

**Response:**
```json
{
  "data": [
    {
      "id": "anthropic/claude-sonnet-4-20250514",
      "name": "Claude Sonnet 4 (2025-05-14)",
      "created": 1715644800,
      "context_length": 200000,
      "pricing": {
        "prompt": "0.000003",
        "completion": "0.000015"
      },
      "top_provider": {
        "max_completion_tokens": 8192,
        "is_moderated": true
      },
      "architecture": {
        "modality": "text+image->text",
        "tokenizer": "Claude",
        "instruct_type": null
      }
    }
  ]
}
```

**Use Cases:**
- Discover available models
- Compare model capabilities
- Check pricing before making requests
- Filter models by context length or modality

**Cost:** Free

---

### 3. Get Generation Details

**Retrieve detailed information about a completed generation**

```
GET /generation?id={generation_id}
```

**Description:** Query for generation statistics including precise token counts, costs, and model used after a request completes.

**Parameters:**
- `id` (required): Generation ID returned from chat completion

**Response:**
```json
{
  "id": "gen-123",
  "model": "anthropic/claude-sonnet-4-20250514",
  "streamed": false,
  "generation_time": 1234,
  "created_at": "2026-01-13T18:00:00Z",
  "tokens_prompt": 15,
  "tokens_completion": 8,
  "native_tokens_prompt": 15,
  "native_tokens_completion": 8,
  "total_cost": 0.000165
}
```

**Use Cases:**
- Precise cost accounting
- Token usage analysis
- Generation performance metrics
- Billing reconciliation

**Cost:** Free

---

### 4. List Model Endpoints

**Get all available endpoints for a specific model**

```
GET /models/{model_id}/endpoints
```

**Description:** Lists all provider endpoints that support a specific model, useful for understanding availability and redundancy.

**Path Parameters:**
- `model_id`: Model identifier (e.g., `anthropic/claude-sonnet-4-20250514`)

**Response:**
```json
{
  "data": [
    {
      "provider": "Anthropic",
      "endpoint": "https://api.anthropic.com/v1/messages",
      "available": true,
      "latency_ms": 120
    }
  ]
}
```

**Use Cases:**
- Check model availability
- Understand provider redundancy
- Debug routing issues

**Cost:** Free

---

### 5. Get Credits

**Check remaining credits on OpenRouter account**

```
GET /auth/key
```

**Description:** Returns information about the current API key including remaining credits (when using direct OpenRouter key).

**Response:**
```json
{
  "data": {
    "label": "My API Key",
    "usage": 123.45,
    "limit": 1000.00,
    "is_free_tier": false,
    "rate_limit": {
      "requests": 200,
      "interval": "10s"
    }
  }
}
```

**Note:** For Seren Publisher usage, billing is handled via SerenBucks/x402 protocol. This endpoint shows upstream OpenRouter account status.

**Use Cases:**
- Monitor OpenRouter credit balance
- Check rate limits
- Verify key configuration

**Cost:** Free

---

## Supported Models (Examples)

### Text Models

**Anthropic:**
- `anthropic/claude-opus-4-20250514` - Most capable Claude model
- `anthropic/claude-sonnet-4-20250514` - Balanced performance and cost
- `anthropic/claude-haiku-4-20250107` - Fast and economical

**OpenAI:**
- `openai/gpt-4-turbo` - Latest GPT-4 Turbo
- `openai/gpt-4o` - GPT-4 Optimized
- `openai/gpt-3.5-turbo` - Fast and economical

**Google:**
- `google/gemini-pro-1.5` - Google's most capable model
- `google/gemini-flash-1.5` - Fast inference

**Meta:**
- `meta-llama/llama-3.3-70b-instruct` - Open source flagship
- `meta-llama/llama-3.1-405b-instruct` - Largest Llama model

**Mistral:**
- `mistralai/mistral-large-2411` - Latest large model
- `mistralai/mistral-small-2409` - Efficient smaller model

### Vision Models

- `anthropic/claude-sonnet-4-20250514` - Text + image understanding
- `openai/gpt-4o` - Multimodal GPT-4
- `google/gemini-pro-vision` - Image understanding

### Code Models

- `anthropic/claude-sonnet-4-20250514` - Excellent for code
- `openai/gpt-4-turbo` - Strong code generation
- `deepseek/deepseek-coder-33b-instruct` - Code-specialized

---

## Pricing

Seren Models uses **passthrough pricing** with a 15% markup:

**Base Pricing (varies by model):**
- Claude Sonnet 4: ~$3/1M input tokens, ~$15/1M output tokens
- GPT-4 Turbo: ~$10/1M input tokens, ~$30/1M output tokens
- GPT-3.5 Turbo: ~$0.50/1M input tokens, ~$1.50/1M output tokens
- Llama 3.3 70B: ~$0.50/1M input tokens, ~$0.80/1M output tokens

**Seren Markup:** 1.15x (15% fee)

**Payment:** SerenBucks (prepaid credits) or x402 on-chain payments

---

## Usage Examples

### Example 1: Simple Chat with Claude Sonnet

```javascript
// Via Seren MCP
execute_paid_api({
  publisher: "seren-models",
  method: "POST",
  path: "/chat/completions",
  body: {
    model: "anthropic/claude-sonnet-4-20250514",
    messages: [
      {
        role: "user",
        content: "Calculate the square root of 16384"
      }
    ],
    max_tokens: 100
  }
})

// Response:
{
  "status": 200,
  "body": {
    "choices": [{
      "message": {
        "content": "The square root of 16384 is 128."
      }
    }],
    "usage": {
      "total_tokens": 42
    }
  },
  "cost": "0.000189",  // 1.15x markup applied
  "payment_source": "prepaid_balance"
}
```

### Example 2: List Available Models

```javascript
execute_paid_api({
  publisher: "seren-models",
  method: "GET",
  path: "/models"
})

// Returns list of 200+ models with capabilities
```

### Example 3: Streaming Response

```javascript
execute_paid_api_stream({
  publisher: "seren-models",
  method: "POST",
  path: "/chat/completions",
  body: {
    model: "anthropic/claude-sonnet-4-20250514",
    messages: [
      {
        role: "user",
        content: "Write a haiku about AI"
      }
    ],
    stream: true
  }
})

// Streams response chunks in real-time
```

### Example 4: Function Calling

```javascript
execute_paid_api({
  publisher: "seren-models",
  method: "POST",
  path: "/chat/completions",
  body: {
    model: "openai/gpt-4-turbo",
    messages: [
      {
        role: "user",
        content: "What's the weather in Tokyo?"
      }
    ],
    tools: [
      {
        type: "function",
        function: {
          name: "get_weather",
          description: "Get current weather for a location",
          parameters: {
            type: "object",
            properties: {
              location: { type: "string" }
            }
          }
        }
      }
    ]
  }
})
```

---

## Model Selection Guide

### For General Tasks
- **Best Quality**: `anthropic/claude-opus-4-20250514`
- **Balanced**: `anthropic/claude-sonnet-4-20250514`
- **Fast & Cheap**: `anthropic/claude-haiku-4-20250107`

### For Code Generation
- **Best**: `anthropic/claude-sonnet-4-20250514`
- **Alternative**: `openai/gpt-4-turbo`
- **Specialized**: `deepseek/deepseek-coder-33b-instruct`

### For Long Context
- **200K context**: `anthropic/claude-sonnet-4-20250514`
- **128K context**: `openai/gpt-4-turbo`
- **100K context**: `google/gemini-pro-1.5`

### For Vision Tasks
- **Best**: `anthropic/claude-sonnet-4-20250514`
- **Alternative**: `openai/gpt-4o`
- **Specialized**: `google/gemini-pro-vision`

### For Cost Optimization
- **Cheapest capable**: `anthropic/claude-haiku-4-20250107`
- **Open source**: `meta-llama/llama-3.3-70b-instruct`
- **Budget GPT**: `openai/gpt-3.5-turbo`

---

## Rate Limits

Rate limits are enforced by OpenRouter and passed through by Seren:

- **Default**: 200 requests per 10 seconds
- **Burst**: Up to 500 requests in short bursts
- **Concurrent**: 50 simultaneous streaming connections

**Note:** SerenBucks balance must be sufficient for request. Insufficient balance returns 402 Payment Required.

---

## Error Handling

**Common Error Codes:**

- `400 Bad Request`: Invalid request format or parameters
- `401 Unauthorized`: Invalid or missing authentication
- `402 Payment Required`: Insufficient SerenBucks balance
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: OpenRouter service error
- `503 Service Unavailable`: Model temporarily unavailable

**Error Response Format:**
```json
{
  "error": {
    "message": "Insufficient credits",
    "type": "insufficient_balance",
    "code": 402
  }
}
```

---

## Additional Resources

- **OpenRouter Docs**: https://openrouter.ai/docs
- **Model List**: https://openrouter.ai/models
- **Seren Publisher**: https://serendb.com/bestsellers/seren-models
- **Seren API Docs**: https://docs.serendb.com

---

**Last Updated:** January 13, 2026
**Publisher:** SerenAI
**Contact:** taariq@serendb.com

Taariq Lewis, SerenAI, Paloma, and Volume at https://serendb.com
