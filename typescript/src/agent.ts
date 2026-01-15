/**
 * Agent decorator and utilities for Seren templates.
 */

import type { AgentInput, AgentOutput } from "./types";

/**
 * Configuration for a Seren agent.
 */
export interface AgentConfig {
  /** Display name for the agent in the store */
  name: string;
  /** What the agent does (shown in catalog) */
  description?: string;
  /** Price per invocation in USD (e.g., "0.05" for 5 cents) */
  price: string;
  /** Preferred compute backend. If not set, uses store default. */
  computeBackend?: string;
}

/**
 * Agent function signature.
 */
export type AgentFunction<
  I extends AgentInput = AgentInput,
  O extends AgentOutput = AgentOutput,
> = (input: I) => O | Promise<O>;

/**
 * Metadata attached to agent functions.
 */
export interface AgentMetadata {
  name: string;
  description: string;
  price: string;
  computeBackend?: string;
}

/** Symbol for storing agent metadata */
const SEREN_AGENT_SYMBOL = Symbol.for("seren_agent");

/**
 * Create a Seren agent template.
 *
 * This function wraps your agent logic and attaches metadata needed
 * for publishing and execution in the Seren Store.
 *
 * @param config - Agent configuration
 * @param fn - The agent function implementing your logic
 * @returns Wrapped agent function with metadata
 *
 * @example
 * ```typescript
 * import { agent } from 'seren-agent';
 *
 * export const run = agent({
 *   name: "Code Analyzer",
 *   price: "0.10",
 *   description: "Analyzes code for quality issues"
 * }, async (input) => {
 *   const { code } = input;
 *   // ... analysis logic ...
 *   return { score: 85, issues: [] };
 * });
 * ```
 */
export function agent<I extends AgentInput, O extends AgentOutput>(
  config: AgentConfig,
  fn: AgentFunction<I, O>,
): AgentFunction<I, O> & { _seren_agent: AgentMetadata } {
  const metadata: AgentMetadata = {
    name: config.name,
    description: config.description ?? "",
    price: config.price,
    computeBackend: config.computeBackend,
  };

  // Create wrapper function
  const wrapper = async (input: I): Promise<O> => {
    return fn(input);
  };

  // Attach metadata
  (wrapper as any)._seren_agent = metadata;
  (wrapper as any)[SEREN_AGENT_SYMBOL] = metadata;

  return wrapper as AgentFunction<I, O> & { _seren_agent: AgentMetadata };
}

/**
 * Extract Seren agent metadata from a function.
 *
 * @param fn - A function potentially created with `agent()`
 * @returns Agent metadata or undefined if not a Seren agent
 */
export function getAgentMetadata(fn: unknown): AgentMetadata | undefined {
  if (typeof fn !== "function") return undefined;
  return (fn as any)._seren_agent ?? (fn as any)[SEREN_AGENT_SYMBOL];
}

/**
 * Check if a function is a Seren agent.
 *
 * @param fn - Function to check
 * @returns True if the function was created with `agent()`
 */
export function isSerenAgent(fn: unknown): boolean {
  return getAgentMetadata(fn) !== undefined;
}
