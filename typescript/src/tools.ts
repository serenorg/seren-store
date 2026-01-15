/**
 * Tool calling utilities for Seren agent templates.
 *
 * Provides helpers for building agentic workflows with function calling.
 *
 * @example
 * ```typescript
 * import { ToolRegistry, defineTool } from "seren-agent/tools";
 *
 * const searchTool = defineTool({
 *   name: "web_search",
 *   description: "Search the web for information",
 *   parameters: {
 *     type: "object",
 *     properties: {
 *       query: { type: "string", description: "Search query" },
 *     },
 *     required: ["query"],
 *   },
 *   execute: async ({ query }) => {
 *     // Implementation
 *     return { results: [...] };
 *   },
 * });
 *
 * const registry = new ToolRegistry([searchTool]);
 *
 * // Get OpenAI-compatible tool definitions
 * const tools = registry.getOpenAITools();
 *
 * // Execute a tool call from LLM response
 * const result = await registry.execute("web_search", { query: "latest news" });
 * ```
 *
 * @module
 */

import type { JsonValue } from "./types";

/**
 * JSON Schema definition for tool parameters.
 */
export interface ToolParameterSchema {
  type: "object";
  properties: Record<
    string,
    {
      type: "string" | "number" | "boolean" | "array" | "object";
      description?: string;
      enum?: string[];
      items?: { type: string };
      default?: JsonValue;
    }
  >;
  required?: string[];
  additionalProperties?: boolean;
}

/**
 * Tool definition for function calling.
 */
export interface ToolDefinition<
  TParams = Record<string, unknown>,
  TResult = unknown,
> {
  /** Unique tool name (used in function calls) */
  name: string;
  /** Human-readable description for the LLM */
  description: string;
  /** JSON Schema for parameters */
  parameters: ToolParameterSchema;
  /** Function to execute when tool is called */
  execute: (params: TParams) => Promise<TResult>;
}

/**
 * OpenAI-compatible tool format.
 */
export interface OpenAITool {
  type: "function";
  function: {
    name: string;
    description: string;
    parameters: ToolParameterSchema;
  };
}

/**
 * Anthropic-compatible tool format.
 */
export interface AnthropicTool {
  name: string;
  description: string;
  input_schema: ToolParameterSchema;
}

/**
 * Define a tool with type-safe parameters and execution.
 *
 * @example
 * ```typescript
 * const calculator = defineTool({
 *   name: "calculate",
 *   description: "Perform mathematical calculations",
 *   parameters: {
 *     type: "object",
 *     properties: {
 *       expression: { type: "string", description: "Math expression to evaluate" },
 *     },
 *     required: ["expression"],
 *   },
 *   execute: async ({ expression }) => {
 *     // Safe evaluation logic here
 *     return { result: eval(expression) };
 *   },
 * });
 * ```
 */
export function defineTool<
  TParams = Record<string, unknown>,
  TResult = unknown,
>(
  definition: ToolDefinition<TParams, TResult>,
): ToolDefinition<TParams, TResult> {
  return definition;
}

/**
 * Registry for managing and executing tools.
 *
 * Provides:
 * - Tool registration and lookup
 * - Format conversion for different LLM providers
 * - Safe tool execution with error handling
 */
export class ToolRegistry {
  private tools: Map<string, ToolDefinition<unknown, unknown>> = new Map();

  /**
   * Create a new tool registry.
   *
   * @param tools - Initial tools to register
   */
  constructor(tools: ToolDefinition<unknown, unknown>[] = []) {
    for (const tool of tools) {
      this.register(tool);
    }
  }

  /**
   * Register a tool in the registry.
   *
   * @param tool - Tool definition to register
   * @throws Error if tool name is already registered
   */
  register<TParams, TResult>(tool: ToolDefinition<TParams, TResult>): void {
    if (this.tools.has(tool.name)) {
      throw new Error(`Tool "${tool.name}" is already registered`);
    }
    this.tools.set(tool.name, tool as ToolDefinition<unknown, unknown>);
  }

  /**
   * Get a tool by name.
   *
   * @param name - Tool name
   * @returns Tool definition or undefined
   */
  get(name: string): ToolDefinition<unknown, unknown> | undefined {
    return this.tools.get(name);
  }

  /**
   * Check if a tool is registered.
   *
   * @param name - Tool name
   */
  has(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * Get all registered tool names.
   */
  names(): string[] {
    return Array.from(this.tools.keys());
  }

  /**
   * Get tools in OpenAI function calling format.
   *
   * @example
   * ```typescript
   * const response = await openai.chat.completions.create({
   *   model: "gpt-4",
   *   messages: [...],
   *   tools: registry.getOpenAITools(),
   * });
   * ```
   */
  getOpenAITools(): OpenAITool[] {
    return Array.from(this.tools.values()).map((tool) => ({
      type: "function" as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.parameters,
      },
    }));
  }

  /**
   * Get tools in Anthropic tool use format.
   *
   * @example
   * ```typescript
   * const response = await anthropic.messages.create({
   *   model: "claude-3-opus-20240229",
   *   messages: [...],
   *   tools: registry.getAnthropicTools(),
   * });
   * ```
   */
  getAnthropicTools(): AnthropicTool[] {
    return Array.from(this.tools.values()).map((tool) => ({
      name: tool.name,
      description: tool.description,
      input_schema: tool.parameters,
    }));
  }

  /**
   * Execute a tool by name with given parameters.
   *
   * @param name - Tool name
   * @param params - Parameters to pass to the tool
   * @returns Tool execution result
   * @throws Error if tool is not found
   *
   * @example
   * ```typescript
   * // Handle OpenAI tool calls
   * for (const toolCall of response.choices[0].message.tool_calls) {
   *   const result = await registry.execute(
   *     toolCall.function.name,
   *     JSON.parse(toolCall.function.arguments)
   *   );
   *   // Add result to messages...
   * }
   * ```
   */
  async execute(
    name: string,
    params: Record<string, unknown>,
  ): Promise<unknown> {
    const tool = this.tools.get(name);
    if (!tool) {
      throw new Error(`Tool "${name}" not found in registry`);
    }
    return tool.execute(params);
  }

  /**
   * Execute a tool and wrap errors in a structured format.
   *
   * Useful for returning errors to LLMs in a consistent format.
   *
   * @param name - Tool name
   * @param params - Parameters to pass to the tool
   * @returns Result or error object
   */
  async executeSafe(
    name: string,
    params: Record<string, unknown>,
  ): Promise<
    { success: true; result: unknown } | { success: false; error: string }
  > {
    try {
      const result = await this.execute(name, params);
      return { success: true, result };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }
}
