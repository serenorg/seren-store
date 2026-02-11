// ABOUTME: Tests for tool calling utilities — defineTool, ToolRegistry, format conversion.
// ABOUTME: Covers registration, lookup, execution, executeSafe, OpenAI/Anthropic format output.
import { describe, it, expect } from "vitest";
import { defineTool, ToolRegistry } from "./tools";
import type { ToolDefinition, OpenAITool, AnthropicTool } from "./tools";

// --- Test tools ---

const searchTool = defineTool({
  name: "web_search",
  description: "Search the web",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
    },
    required: ["query"],
  },
  execute: async (params: { query: string }) => ({
    results: [`Result for: ${params.query}`],
  }),
});

const calculatorTool = defineTool({
  name: "calculator",
  description: "Do math",
  parameters: {
    type: "object",
    properties: {
      a: { type: "number", description: "First operand" },
      b: { type: "number", description: "Second operand" },
      op: { type: "string", description: "Operator", enum: ["+", "-", "*", "/"] },
    },
    required: ["a", "b", "op"],
  },
  execute: async (params: { a: number; b: number; op: string }) => {
    const ops: Record<string, (a: number, b: number) => number> = {
      "+": (a, b) => a + b,
      "-": (a, b) => a - b,
      "*": (a, b) => a * b,
      "/": (a, b) => a / b,
    };
    return { result: ops[params.op]!(params.a, params.b) };
  },
});

const failingTool = defineTool({
  name: "fail",
  description: "Always fails",
  parameters: { type: "object", properties: {} },
  execute: async () => {
    throw new Error("intentional failure");
  },
});

// --- defineTool ---

describe("defineTool()", () => {
  it("returns the definition as-is", () => {
    const def = defineTool({
      name: "test",
      description: "test tool",
      parameters: { type: "object", properties: {} },
      execute: async () => ({}),
    });
    expect(def.name).toBe("test");
    expect(def.description).toBe("test tool");
    expect(typeof def.execute).toBe("function");
  });

  it("preserves parameter schema", () => {
    expect(searchTool.parameters.required).toEqual(["query"]);
    expect(searchTool.parameters.properties.query.type).toBe("string");
  });
});

// --- ToolRegistry construction ---

describe("ToolRegistry constructor", () => {
  it("creates an empty registry", () => {
    const registry = new ToolRegistry();
    expect(registry.names()).toEqual([]);
  });

  it("accepts initial tools", () => {
    const registry = new ToolRegistry([searchTool, calculatorTool]);
    expect(registry.names()).toEqual(["web_search", "calculator"]);
  });

  it("throws on duplicate tool names in constructor", () => {
    expect(() => new ToolRegistry([searchTool, searchTool])).toThrow(
      'Tool "web_search" is already registered',
    );
  });
});

// --- Registration ---

describe("ToolRegistry.register()", () => {
  it("registers a tool", () => {
    const registry = new ToolRegistry();
    registry.register(searchTool);
    expect(registry.has("web_search")).toBe(true);
  });

  it("throws on duplicate registration", () => {
    const registry = new ToolRegistry([searchTool]);
    expect(() => registry.register(searchTool)).toThrow(
      'Tool "web_search" is already registered',
    );
  });
});

// --- Lookup ---

describe("ToolRegistry.get()", () => {
  it("returns a registered tool", () => {
    const registry = new ToolRegistry([searchTool]);
    const tool = registry.get("web_search");
    expect(tool).toBeDefined();
    expect(tool!.name).toBe("web_search");
  });

  it("returns undefined for unknown tool", () => {
    const registry = new ToolRegistry();
    expect(registry.get("nonexistent")).toBeUndefined();
  });
});

describe("ToolRegistry.has()", () => {
  it("returns true for registered tool", () => {
    const registry = new ToolRegistry([searchTool]);
    expect(registry.has("web_search")).toBe(true);
  });

  it("returns false for unknown tool", () => {
    const registry = new ToolRegistry();
    expect(registry.has("nonexistent")).toBe(false);
  });
});

describe("ToolRegistry.names()", () => {
  it("returns empty array for empty registry", () => {
    expect(new ToolRegistry().names()).toEqual([]);
  });

  it("returns all registered names", () => {
    const registry = new ToolRegistry([searchTool, calculatorTool]);
    expect(registry.names()).toContain("web_search");
    expect(registry.names()).toContain("calculator");
    expect(registry.names()).toHaveLength(2);
  });
});

// --- Format conversion ---

describe("ToolRegistry.getOpenAITools()", () => {
  it("returns empty array for empty registry", () => {
    expect(new ToolRegistry().getOpenAITools()).toEqual([]);
  });

  it("returns OpenAI-formatted tools", () => {
    const registry = new ToolRegistry([searchTool]);
    const tools = registry.getOpenAITools();
    expect(tools).toHaveLength(1);

    const tool = tools[0]!;
    expect(tool.type).toBe("function");
    expect(tool.function.name).toBe("web_search");
    expect(tool.function.description).toBe("Search the web");
    expect(tool.function.parameters).toEqual(searchTool.parameters);
  });

  it("converts multiple tools", () => {
    const registry = new ToolRegistry([searchTool, calculatorTool]);
    const tools = registry.getOpenAITools();
    expect(tools).toHaveLength(2);
    expect(tools.map((t) => t.function.name)).toEqual([
      "web_search",
      "calculator",
    ]);
  });
});

describe("ToolRegistry.getAnthropicTools()", () => {
  it("returns empty array for empty registry", () => {
    expect(new ToolRegistry().getAnthropicTools()).toEqual([]);
  });

  it("returns Anthropic-formatted tools", () => {
    const registry = new ToolRegistry([searchTool]);
    const tools = registry.getAnthropicTools();
    expect(tools).toHaveLength(1);

    const tool = tools[0]!;
    expect(tool.name).toBe("web_search");
    expect(tool.description).toBe("Search the web");
    expect(tool.input_schema).toEqual(searchTool.parameters);
  });
});

// --- Execution ---

describe("ToolRegistry.execute()", () => {
  it("executes a registered tool", async () => {
    const registry = new ToolRegistry([searchTool]);
    const result = await registry.execute("web_search", { query: "test" });
    expect(result).toEqual({ results: ["Result for: test"] });
  });

  it("executes calculator tool", async () => {
    const registry = new ToolRegistry([calculatorTool]);
    const result = await registry.execute("calculator", {
      a: 10,
      b: 3,
      op: "+",
    });
    expect(result).toEqual({ result: 13 });
  });

  it("throws for unknown tool", async () => {
    const registry = new ToolRegistry();
    await expect(registry.execute("missing", {})).rejects.toThrow(
      'Tool "missing" not found in registry',
    );
  });

  it("propagates tool errors", async () => {
    const registry = new ToolRegistry([failingTool]);
    await expect(registry.execute("fail", {})).rejects.toThrow(
      "intentional failure",
    );
  });
});

describe("ToolRegistry.executeSafe()", () => {
  it("returns success for a working tool", async () => {
    const registry = new ToolRegistry([searchTool]);
    const result = await registry.executeSafe("web_search", {
      query: "safe test",
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.result).toEqual({ results: ["Result for: safe test"] });
    }
  });

  it("returns error for a failing tool", async () => {
    const registry = new ToolRegistry([failingTool]);
    const result = await registry.executeSafe("fail", {});
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBe("intentional failure");
    }
  });

  it("returns error for unknown tool", async () => {
    const registry = new ToolRegistry();
    const result = await registry.executeSafe("missing", {});
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toContain("missing");
    }
  });

  it("handles non-Error thrown values", async () => {
    const throwStringTool = defineTool({
      name: "throw_string",
      description: "Throws a string",
      parameters: { type: "object", properties: {} },
      execute: async () => {
        throw "raw string error";
      },
    });
    const registry = new ToolRegistry([throwStringTool]);
    const result = await registry.executeSafe("throw_string", {});
    expect(result.success).toBe(false);
    if (!result.success) {
      expect(result.error).toBe("raw string error");
    }
  });
});
