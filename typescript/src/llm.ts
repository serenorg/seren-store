/**
 * LLM client helpers for Seren agents.
 *
 * These helpers provide a consistent way to access LLM APIs using environment
 * variables injected by the compute backend.
 */

import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

// Default Seren API URL
const DEFAULT_SEREN_API_URL = "https://api.serendb.com";
const DEFAULT_SEREN_PUBLISHER = "seren-models";

/**
 * Message format for chat completions.
 */
export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

/**
 * Options for chat completion requests.
 */
export interface ChatCompletionOptions {
  messages: ChatMessage[];
  model?: string;
  max_tokens?: number;
  temperature?: number;
  top_p?: number;
  stream?: boolean;
  [key: string]: unknown;
}

/**
 * Chat completion response.
 */
export interface ChatCompletionResponse {
  id?: string;
  model?: string;
  choices: Array<{
    message: {
      role: string;
      content: string;
    };
    finish_reason?: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

/**
 * Options for creating a SerenLLMClient.
 */
export interface SerenLLMClientOptions {
  apiKey?: string;
  baseUrl?: string;
  publisher?: string;
  defaultModel?: string;
}

/**
 * Chat completions interface matching OpenAI's API structure.
 */
class ChatCompletions {
  constructor(private client: SerenLLMClient) {}

  /**
   * Create a chat completion.
   *
   * @param options - Chat completion options
   * @returns Promise resolving to completion response
   */
  async create(
    options: ChatCompletionOptions,
  ): Promise<ChatCompletionResponse> {
    const body: Record<string, unknown> = {
      model: options.model ?? this.client.defaultModel,
      messages: options.messages,
    };

    if (options.max_tokens !== undefined) body.max_tokens = options.max_tokens;
    if (options.temperature !== undefined)
      body.temperature = options.temperature;
    if (options.top_p !== undefined) body.top_p = options.top_p;
    if (options.stream !== undefined) body.stream = options.stream;

    // Copy any additional options
    for (const [key, value] of Object.entries(options)) {
      if (
        ![
          "messages",
          "model",
          "max_tokens",
          "temperature",
          "top_p",
          "stream",
        ].includes(key)
      ) {
        body[key] = value;
      }
    }

    return this.client._request("POST", "/chat/completions", body);
  }
}

/**
 * Messages interface matching Anthropic's API structure.
 */
class Messages {
  constructor(private client: SerenLLMClient) {}

  /**
   * Create a message (Anthropic-style interface).
   *
   * This is an alias for chat.completions.create() for compatibility
   * with code written for the Anthropic SDK.
   */
  async create(
    options: ChatCompletionOptions,
  ): Promise<ChatCompletionResponse> {
    return this.client.chat.completions.create(options);
  }
}

/**
 * Chat namespace containing completions.
 */
class Chat {
  completions: ChatCompletions;

  constructor(client: SerenLLMClient) {
    this.completions = new ChatCompletions(client);
  }
}

/**
 * HTTP client for accessing LLMs through Seren Publishers.
 *
 * Routes LLM requests through Seren's publisher infrastructure,
 * providing unified billing and access control without requiring
 * provider-specific SDK packages.
 *
 * @example
 * ```typescript
 * const client = new SerenLLMClient({
 *   defaultModel: "anthropic/claude-sonnet-4-20250514"
 * });
 * const response = await client.chat.completions.create({
 *   messages: [{ role: "user", content: "Hello!" }],
 *   max_tokens: 100
 * });
 * ```
 */
export class SerenLLMClient {
  readonly apiKey: string;
  readonly baseUrl: string;
  readonly publisher: string;
  readonly defaultModel: string;
  readonly chat: Chat;
  readonly messages: Messages;

  constructor(options: SerenLLMClientOptions = {}) {
    this.apiKey = options.apiKey ?? process.env.SEREN_API_KEY ?? "";
    if (!this.apiKey) {
      throw new Error(
        "SEREN_API_KEY not set. Set the environment variable or pass apiKey option.",
      );
    }

    this.baseUrl =
      options.baseUrl ?? process.env.SEREN_API_URL ?? DEFAULT_SEREN_API_URL;
    this.publisher = options.publisher ?? DEFAULT_SEREN_PUBLISHER;
    this.defaultModel =
      options.defaultModel ?? "anthropic/claude-sonnet-4-20250514";

    this.chat = new Chat(this);
    this.messages = new Messages(this);
  }

  /**
   * Make an HTTP request to the Seren publisher API.
   * @internal
   */
  async _request(
    method: string,
    path: string,
    body?: Record<string, unknown>,
  ): Promise<ChatCompletionResponse> {
    const url = `${this.baseUrl}/publishers/${this.publisher}${path}`;

    const response = await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorBody}`);
    }

    return response.json() as Promise<ChatCompletionResponse>;
  }
}

/**
 * Get a Claude client routed through Seren Publishers.
 *
 * This client makes requests through the seren-models publisher,
 * which provides access to Claude models without requiring the
 * @anthropic-ai/sdk package. Only SEREN_API_KEY is needed.
 *
 * @param options - Optional configuration
 * @param options.apiKey - Seren API key override
 * @param options.model - Default Claude model to use
 * @returns SerenLLMClient configured for Claude
 * @throws Error if SEREN_API_KEY is not set
 *
 * @example
 * ```typescript
 * import { getSerenClaudeClient } from 'seren-agent/llm';
 *
 * const client = getSerenClaudeClient();
 * const response = await client.chat.completions.create({
 *   messages: [{ role: "user", content: "Hello!" }],
 *   max_tokens: 100
 * });
 * console.log(response.choices[0].message.content);
 * ```
 */
export function getSerenClaudeClient(options?: {
  apiKey?: string;
  model?: string;
}): SerenLLMClient {
  return new SerenLLMClient({
    apiKey: options?.apiKey,
    defaultModel: options?.model ?? "anthropic/claude-sonnet-4-20250514",
  });
}

/**
 * Get an OpenAI client routed through Seren Publishers.
 *
 * This client makes requests through the seren-models publisher,
 * which provides access to OpenAI models without requiring the
 * openai package. Only SEREN_API_KEY is needed.
 *
 * @param options - Optional configuration
 * @param options.apiKey - Seren API key override
 * @param options.model - Default OpenAI model to use
 * @returns SerenLLMClient configured for OpenAI models
 * @throws Error if SEREN_API_KEY is not set
 *
 * @example
 * ```typescript
 * import { getSerenOpenAIClient } from 'seren-agent/llm';
 *
 * const client = getSerenOpenAIClient();
 * const response = await client.chat.completions.create({
 *   messages: [{ role: "user", content: "Hello!" }],
 *   max_tokens: 100
 * });
 * console.log(response.choices[0].message.content);
 * ```
 */
export function getSerenOpenAIClient(options?: {
  apiKey?: string;
  model?: string;
}): SerenLLMClient {
  return new SerenLLMClient({
    apiKey: options?.apiKey,
    defaultModel: options?.model ?? "openai/gpt-4o",
  });
}

// =============================================================================
// Original provider-specific clients (require provider SDK packages)
// =============================================================================

/**
 * Get an OpenAI client using the injected OPENAI_API_KEY.
 *
 * @param apiKey - Optional override. If not provided, uses environment variable.
 * @returns OpenAI client instance
 * @throws Error if no API key is available or openai package is not installed
 *
 * @example
 * ```typescript
 * import { getOpenAIClient } from 'seren-agent/llm';
 *
 * const client = getOpenAIClient();
 * const response = await client.chat.completions.create({
 *   model: "gpt-4o",
 *   messages: [{ role: "user", content: "Hello!" }]
 * });
 * ```
 */
export function getOpenAIClient(apiKey?: string) {
  let OpenAI;
  try {
    OpenAI = require("openai").default;
  } catch {
    throw new Error("openai package not installed. Run: npm install openai");
  }

  const key = apiKey ?? process.env.OPENAI_API_KEY;
  if (!key) {
    throw new Error(
      "OPENAI_API_KEY not set. Ensure LLM config is provided when publishing " +
        "or the caller passes X-LLM-API-KEY header.",
    );
  }

  return new OpenAI({ apiKey: key });
}

/**
 * Get an Anthropic client using the injected ANTHROPIC_API_KEY.
 *
 * @param apiKey - Optional override. If not provided, uses environment variable.
 * @returns Anthropic client instance
 * @throws Error if no API key is available or anthropic package is not installed
 *
 * @example
 * ```typescript
 * import { getAnthropicClient } from 'seren-agent/llm';
 *
 * const client = getAnthropicClient();
 * const message = await client.messages.create({
 *   model: "claude-sonnet-4-20250514",
 *   max_tokens: 1024,
 *   messages: [{ role: "user", content: "Hello!" }]
 * });
 * ```
 */
export function getAnthropicClient(apiKey?: string) {
  let Anthropic;
  try {
    Anthropic = require("@anthropic-ai/sdk").default;
  } catch {
    throw new Error(
      "@anthropic-ai/sdk package not installed. Run: npm install @anthropic-ai/sdk",
    );
  }

  const key = apiKey ?? process.env.ANTHROPIC_API_KEY;
  if (!key) {
    throw new Error(
      "ANTHROPIC_API_KEY not set. Ensure LLM config is provided when publishing " +
        "or the caller passes X-LLM-API-KEY header.",
    );
  }

  return new Anthropic({ apiKey: key });
}

/**
 * Get a Google Generative AI client using the injected GOOGLE_API_KEY.
 *
 * @param apiKey - Optional override. If not provided, uses environment variable.
 * @returns Google GenerativeAI instance
 * @throws Error if no API key is available or @google/generative-ai is not installed
 *
 * @example
 * ```typescript
 * import { getGoogleClient } from 'seren-agent/llm';
 *
 * const genai = getGoogleClient();
 * const model = genai.getGenerativeModel({ model: "gemini-pro" });
 * const result = await model.generateContent("Hello!");
 * ```
 */
export function getGoogleClient(apiKey?: string) {
  let GoogleGenerativeAI;
  try {
    GoogleGenerativeAI = require("@google/generative-ai").GoogleGenerativeAI;
  } catch {
    throw new Error(
      "@google/generative-ai package not installed. Run: npm install @google/generative-ai",
    );
  }

  const key = apiKey ?? process.env.GOOGLE_API_KEY;
  if (!key) {
    throw new Error(
      "GOOGLE_API_KEY not set. Ensure LLM config is provided when publishing " +
        "or the caller passes X-LLM-API-KEY header.",
    );
  }

  return new GoogleGenerativeAI(key);
}

/**
 * Get the configured LLM model name from environment.
 *
 * @returns Model name if set, undefined otherwise
 */
export function getLLMModel(): string | undefined {
  return process.env.LLM_MODEL;
}

/**
 * Get a generic LLM API key from environment.
 *
 * @returns API key if set, undefined otherwise
 */
export function getGenericAPIKey(): string | undefined {
  return process.env.LLM_API_KEY;
}
