/**
 * LLM client helpers for Seren agents.
 *
 * These helpers provide a consistent way to access LLM APIs using environment
 * variables injected by the compute backend.
 */

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
  // Dynamic import to avoid bundling if not used
  const OpenAI = require("openai").default;

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
  const Anthropic = require("@anthropic-ai/sdk").default;

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
  const { GoogleGenerativeAI } = require("@google/generative-ai");

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
