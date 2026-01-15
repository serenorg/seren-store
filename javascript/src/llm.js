/**
 * LLM client helpers for Seren agent templates.
 *
 * These helpers read API keys from environment variables that are
 * automatically injected by the compute backend during execution.
 *
 * @module seren-agent/llm
 */

import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

/**
 * Get an OpenAI client instance.
 *
 * Uses the OPENAI_API_KEY environment variable, which is injected
 * by the compute backend from the template's LLM configuration.
 *
 * @param {string} [apiKey] - Optional API key override (for local testing)
 * @returns {import('openai').default} OpenAI client instance
 * @throws {Error} If openai package is not installed or API key is not set
 *
 * @example
 * ```javascript
 * import { getOpenAIClient } from 'seren-agent/llm';
 *
 * const openai = getOpenAIClient();
 * const response = await openai.chat.completions.create({
 *   model: "gpt-4",
 *   messages: [{ role: "user", content: "Hello!" }],
 * });
 * ```
 */
export function getOpenAIClient(apiKey) {
    const key = apiKey || process.env.OPENAI_API_KEY;
    if (!key) {
        throw new Error(
            "OPENAI_API_KEY not set. Ensure LLM config is provided when publishing the template.",
        );
    }

    // Dynamic import to avoid requiring the package if not used
    let OpenAI;
    try {
        OpenAI = require("openai").default;
    } catch {
        throw new Error(
            "openai package not installed. Run: npm install openai",
        );
    }

    return new OpenAI({ apiKey: key });
}

/**
 * Get an Anthropic client instance.
 *
 * Uses the ANTHROPIC_API_KEY environment variable, which is injected
 * by the compute backend from the template's LLM configuration.
 *
 * @param {string} [apiKey] - Optional API key override (for local testing)
 * @returns {import('@anthropic-ai/sdk').default} Anthropic client instance
 * @throws {Error} If @anthropic-ai/sdk package is not installed or API key is not set
 *
 * @example
 * ```javascript
 * import { getAnthropicClient } from 'seren-agent/llm';
 *
 * const anthropic = getAnthropicClient();
 * const message = await anthropic.messages.create({
 *   model: "claude-3-opus-20240229",
 *   max_tokens: 1024,
 *   messages: [{ role: "user", content: "Hello!" }],
 * });
 * ```
 */
export function getAnthropicClient(apiKey) {
    const key = apiKey || process.env.ANTHROPIC_API_KEY;
    if (!key) {
        throw new Error(
            "ANTHROPIC_API_KEY not set. Ensure LLM config is provided when publishing the template.",
        );
    }

    let Anthropic;
    try {
        Anthropic = require("@anthropic-ai/sdk").default;
    } catch {
        throw new Error(
            "@anthropic-ai/sdk package not installed. Run: npm install @anthropic-ai/sdk",
        );
    }

    return new Anthropic({ apiKey: key });
}

/**
 * Get a Google Generative AI client instance.
 *
 * Uses the GOOGLE_API_KEY environment variable, which is injected
 * by the compute backend from the template's LLM configuration.
 *
 * @param {string} [apiKey] - Optional API key override (for local testing)
 * @returns {import('@google/generative-ai').GoogleGenerativeAI} Google AI client instance
 * @throws {Error} If @google/generative-ai package is not installed or API key is not set
 *
 * @example
 * ```javascript
 * import { getGoogleClient } from 'seren-agent/llm';
 *
 * const google = getGoogleClient();
 * const model = google.getGenerativeModel({ model: "gemini-pro" });
 * const result = await model.generateContent("Hello!");
 * ```
 */
export function getGoogleClient(apiKey) {
    const key = apiKey || process.env.GOOGLE_API_KEY;
    if (!key) {
        throw new Error(
            "GOOGLE_API_KEY not set. Ensure LLM config is provided when publishing the template.",
        );
    }

    let GoogleGenerativeAI;
    try {
        GoogleGenerativeAI =
            require("@google/generative-ai").GoogleGenerativeAI;
    } catch {
        throw new Error(
            "@google/generative-ai package not installed. Run: npm install @google/generative-ai",
        );
    }

    return new GoogleGenerativeAI(key);
}
