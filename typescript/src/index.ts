/**
 * Seren Agent SDK for TypeScript
 *
 * Build monetizable AI agents for the Seren Store.
 *
 * @example
 * ```typescript
 * import { agent } from 'seren-agent';
 * import { getOpenAIClient } from 'seren-agent/llm';
 *
 * export const run = agent({
 *   name: "Web Researcher",
 *   price: "0.05"
 * }, async (input) => {
 *   const client = getOpenAIClient();
 *   // ... your agent logic ...
 *   return { result: "..." };
 * });
 * ```
 */

export { agent, getAgentMetadata, isSerenAgent } from "./agent";
export type { AgentConfig, AgentFunction, AgentMetadata } from "./agent";
export type {
  AgentInput,
  AgentOutput,
  ErrorOutput,
  SuccessOutput,
  JsonValue,
} from "./types";

// Re-export LLM helpers for convenience
export { getOpenAIClient, getAnthropicClient, getGoogleClient } from "./llm";

// Re-export tool utilities
export { ToolRegistry, defineTool } from "./tools";
export type {
  ToolDefinition,
  ToolParameterSchema,
  OpenAITool,
  AnthropicTool,
} from "./tools";
