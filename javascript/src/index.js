/**
 * Seren Agent SDK for JavaScript
 *
 * Build monetizable AI agents for the Seren Store.
 *
 * @example
 * ```javascript
 * import { agent } from 'seren-agent';
 * import { getOpenAIClient } from 'seren-agent/llm';
 *
 * export const run = agent({
 *   name: "Web Researcher",
 *   price: "0.05"
 * })(async (input) => {
 *   const client = getOpenAIClient();
 *   // ... your agent logic ...
 *   return { result: "..." };
 * });
 * ```
 *
 * @module seren-agent
 */

export { agent, getAgentMetadata, isSerenAgent } from "./agent.js";
export { getOpenAIClient, getAnthropicClient, getGoogleClient } from "./llm.js";
export { ToolRegistry, defineTool } from "./tools.js";
