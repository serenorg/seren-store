/**
 * Type definitions for Seren agents.
 */

/**
 * JSON-compatible value type.
 */
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };

/**
 * Base type for agent input.
 *
 * All agent inputs are JSON-serializable objects. Extend this interface
 * for your specific agent's input schema.
 *
 * @example
 * ```typescript
 * interface WebResearchInput extends AgentInput {
 *   query: string;
 *   maxResults?: number;
 *   includeSources?: boolean;
 * }
 * ```
 */
export interface AgentInput {
  [key: string]: JsonValue;
}

/**
 * Base type for agent output.
 *
 * All agent outputs must be JSON-serializable objects. Extend this interface
 * for your specific agent's output schema.
 *
 * @example
 * ```typescript
 * interface WebResearchOutput extends AgentOutput {
 *   summary: string;
 *   sources: string[];
 *   confidence: number;
 * }
 * ```
 */
export interface AgentOutput {
  [key: string]: JsonValue;
}

/**
 * Standard error output format.
 */
export interface ErrorOutput extends AgentOutput {
  error: string;
  message: string;
  details?: { [key: string]: JsonValue };
}

/**
 * Standard success output format.
 */
export interface SuccessOutput extends AgentOutput {
  success: boolean;
  data?: JsonValue;
  metadata?: { [key: string]: JsonValue };
}
