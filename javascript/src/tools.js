/**
 * Tool calling utilities for Seren agent templates.
 *
 * Provides helpers for building agentic workflows with function calling.
 *
 * @module seren-agent/tools
 *
 * @example
 * ```javascript
 * import { ToolRegistry, defineTool } from 'seren-agent/tools';
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
 */

/**
 * Define a tool for function calling.
 *
 * @param {Object} definition - Tool definition
 * @param {string} definition.name - Unique tool name
 * @param {string} definition.description - Human-readable description for the LLM
 * @param {Object} definition.parameters - JSON Schema for parameters
 * @param {function} definition.execute - Async function to execute when called
 * @returns {Object} Tool definition (pass-through for type hints)
 *
 * @example
 * ```javascript
 * const calculator = defineTool({
 *   name: "calculate",
 *   description: "Perform mathematical calculations",
 *   parameters: {
 *     type: "object",
 *     properties: {
 *       expression: { type: "string", description: "Math expression" },
 *     },
 *     required: ["expression"],
 *   },
 *   execute: async ({ expression }) => {
 *     return { result: eval(expression) };
 *   },
 * });
 * ```
 */
export function defineTool(definition) {
    if (!definition.name) {
        throw new Error("Tool name is required");
    }
    if (!definition.description) {
        throw new Error("Tool description is required");
    }
    if (!definition.parameters) {
        throw new Error("Tool parameters schema is required");
    }
    if (typeof definition.execute !== "function") {
        throw new Error("Tool execute function is required");
    }
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
    /**
     * Create a new tool registry.
     *
     * @param {Array} [tools=[]] - Initial tools to register
     */
    constructor(tools = []) {
        /** @type {Map<string, Object>} */
        this.tools = new Map();

        for (const tool of tools) {
            this.register(tool);
        }
    }

    /**
     * Register a tool in the registry.
     *
     * @param {Object} tool - Tool definition
     * @throws {Error} If tool name is already registered
     */
    register(tool) {
        if (this.tools.has(tool.name)) {
            throw new Error(`Tool "${tool.name}" is already registered`);
        }
        this.tools.set(tool.name, tool);
    }

    /**
     * Get a tool by name.
     *
     * @param {string} name - Tool name
     * @returns {Object|undefined} Tool definition or undefined
     */
    get(name) {
        return this.tools.get(name);
    }

    /**
     * Check if a tool is registered.
     *
     * @param {string} name - Tool name
     * @returns {boolean}
     */
    has(name) {
        return this.tools.has(name);
    }

    /**
     * Get all registered tool names.
     *
     * @returns {string[]}
     */
    names() {
        return Array.from(this.tools.keys());
    }

    /**
     * Get tools in OpenAI function calling format.
     *
     * @returns {Array} OpenAI-compatible tool definitions
     *
     * @example
     * ```javascript
     * const response = await openai.chat.completions.create({
     *   model: "gpt-4",
     *   messages: [...],
     *   tools: registry.getOpenAITools(),
     * });
     * ```
     */
    getOpenAITools() {
        return Array.from(this.tools.values()).map((tool) => ({
            type: "function",
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
     * @returns {Array} Anthropic-compatible tool definitions
     *
     * @example
     * ```javascript
     * const response = await anthropic.messages.create({
     *   model: "claude-3-opus-20240229",
     *   messages: [...],
     *   tools: registry.getAnthropicTools(),
     * });
     * ```
     */
    getAnthropicTools() {
        return Array.from(this.tools.values()).map((tool) => ({
            name: tool.name,
            description: tool.description,
            input_schema: tool.parameters,
        }));
    }

    /**
     * Execute a tool by name with given parameters.
     *
     * @param {string} name - Tool name
     * @param {Object} params - Parameters to pass to the tool
     * @returns {Promise<*>} Tool execution result
     * @throws {Error} If tool is not found
     *
     * @example
     * ```javascript
     * // Handle OpenAI tool calls
     * for (const toolCall of response.choices[0].message.tool_calls) {
     *   const result = await registry.execute(
     *     toolCall.function.name,
     *     JSON.parse(toolCall.function.arguments)
     *   );
     * }
     * ```
     */
    async execute(name, params) {
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
     * @param {string} name - Tool name
     * @param {Object} params - Parameters to pass to the tool
     * @returns {Promise<Object>} Result or error object
     */
    async executeSafe(name, params) {
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
