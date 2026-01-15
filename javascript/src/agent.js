/**
 * Agent decorator and metadata utilities.
 *
 * @module seren-agent/agent
 */

/** Symbol for agent metadata (prevents accidental access) */
const SEREN_AGENT_SYMBOL = Symbol.for("seren.agent");

/**
 * Create a Seren agent template.
 *
 * Wraps an async function with metadata for the Seren Store.
 * The agent is backend-agnostic - same code runs on any compute provider.
 *
 * @param {Object} config - Agent configuration
 * @param {string} config.name - Display name for the agent in the store
 * @param {string} [config.description] - Description of what the agent does
 * @param {string} config.price - Price per invocation in USD (e.g., "0.05")
 * @param {string} [config.computeBackend] - Preferred compute backend (e.g., "daytona", "modal")
 * @param {function} fn - The agent function implementing your logic
 * @returns {function} Wrapped agent function with metadata
 *
 * @example
 * ```javascript
 * import { agent } from 'seren-agent';
 *
 * export const run = agent({
 *   name: "Web Researcher",
 *   description: "Research topics via web search",
 *   price: "0.05"
 * }, async (input) => {
 *   const { query } = input;
 *   // Your agent logic here
 *   return { summary: "...", sources: [...] };
 * });
 * ```
 */
export function agent(config, fn) {
    const { name, description = "", price, computeBackend } = config;

    if (!name) {
        throw new Error("Agent name is required");
    }
    if (!price) {
        throw new Error("Agent price is required");
    }
    if (typeof fn !== "function") {
        throw new Error("Agent function is required as second argument");
    }

    // Create wrapper that preserves the original function
    async function wrappedAgent(input) {
        return fn(input);
    }

    // Attach metadata
    const metadata = {
        name,
        description,
        price,
        computeBackend,
    };

    wrappedAgent._seren_agent = metadata;
    wrappedAgent[SEREN_AGENT_SYMBOL] = metadata;

    return wrappedAgent;
}

/**
 * Get metadata from a Seren agent function.
 *
 * @param {function} fn - Agent function to inspect
 * @returns {Object|undefined} Agent metadata or undefined if not a Seren agent
 *
 * @example
 * ```javascript
 * import { getAgentMetadata } from 'seren-agent';
 *
 * const metadata = getAgentMetadata(run);
 * console.log(metadata.name);  // "Web Researcher"
 * console.log(metadata.price); // "0.05"
 * ```
 */
export function getAgentMetadata(fn) {
    if (typeof fn !== "function") {
        return undefined;
    }
    return fn[SEREN_AGENT_SYMBOL] || fn._seren_agent;
}

/**
 * Check if a function is a Seren agent.
 *
 * @param {function} fn - Function to check
 * @returns {boolean} True if the function is a Seren agent
 *
 * @example
 * ```javascript
 * import { isSerenAgent } from 'seren-agent';
 *
 * if (isSerenAgent(run)) {
 *   console.log("This is a Seren agent!");
 * }
 * ```
 */
export function isSerenAgent(fn) {
    return getAgentMetadata(fn) !== undefined;
}
