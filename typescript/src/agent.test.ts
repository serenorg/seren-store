// ABOUTME: Tests for the agent decorator, metadata extraction, and detection utilities.
// ABOUTME: Covers agent(), getAgentMetadata(), isSerenAgent(), sync/async wrapping.
import { describe, it, expect } from "vitest";
import { agent, getAgentMetadata, isSerenAgent } from "./agent";
import type { AgentInput, AgentOutput } from "./types";

// --- Test agents ---

const echoAgent = agent(
  { name: "Echo", price: "0.01" },
  (input: AgentInput): AgentOutput => ({ echo: input.message }),
);

const asyncAgent = agent(
  { name: "Async Echo", price: "0.05", description: "Echoes asynchronously" },
  async (input: AgentInput): Promise<AgentOutput> => ({ echo: input.message }),
);

const fullConfigAgent = agent(
  {
    name: "Full Config",
    price: "1.00",
    description: "Has every config field",
    computeBackend: "daytona",
  },
  async (input: AgentInput): Promise<AgentOutput> => ({ ok: true }),
);

// --- Tests ---

describe("agent()", () => {
  it("wraps a sync function and returns a result", async () => {
    const result = await echoAgent({ message: "hello" });
    expect(result).toEqual({ echo: "hello" });
  });

  it("wraps an async function and returns a result", async () => {
    const result = await asyncAgent({ message: "async hello" });
    expect(result).toEqual({ echo: "async hello" });
  });

  it("attaches _seren_agent metadata", () => {
    expect(echoAgent._seren_agent).toBeDefined();
    expect(echoAgent._seren_agent.name).toBe("Echo");
    expect(echoAgent._seren_agent.price).toBe("0.01");
  });

  it("defaults description to empty string", () => {
    expect(echoAgent._seren_agent.description).toBe("");
  });

  it("stores description when provided", () => {
    expect(asyncAgent._seren_agent.description).toBe(
      "Echoes asynchronously",
    );
  });

  it("stores computeBackend when provided", () => {
    expect(fullConfigAgent._seren_agent.computeBackend).toBe("daytona");
  });

  it("leaves computeBackend undefined when not provided", () => {
    expect(echoAgent._seren_agent.computeBackend).toBeUndefined();
  });

  it("returns a function", () => {
    expect(typeof echoAgent).toBe("function");
  });

  it("always returns a promise (even for sync functions)", () => {
    const result = echoAgent({ message: "test" });
    expect(result).toBeInstanceOf(Promise);
  });
});

describe("getAgentMetadata()", () => {
  it("extracts metadata from an agent function", () => {
    const meta = getAgentMetadata(echoAgent);
    expect(meta).toBeDefined();
    expect(meta!.name).toBe("Echo");
    expect(meta!.price).toBe("0.01");
  });

  it("returns all metadata fields", () => {
    const meta = getAgentMetadata(fullConfigAgent);
    expect(meta).toEqual({
      name: "Full Config",
      description: "Has every config field",
      price: "1.00",
      computeBackend: "daytona",
    });
  });

  it("returns undefined for a plain function", () => {
    const plainFn = () => ({});
    expect(getAgentMetadata(plainFn)).toBeUndefined();
  });

  it("returns undefined for a non-function", () => {
    expect(getAgentMetadata("not a function")).toBeUndefined();
    expect(getAgentMetadata(42)).toBeUndefined();
    expect(getAgentMetadata(null)).toBeUndefined();
    expect(getAgentMetadata(undefined)).toBeUndefined();
  });

  it("returns undefined for an object", () => {
    expect(getAgentMetadata({ _seren_agent: { name: "fake" } })).toBeUndefined();
  });
});

describe("isSerenAgent()", () => {
  it("returns true for agent-wrapped functions", () => {
    expect(isSerenAgent(echoAgent)).toBe(true);
    expect(isSerenAgent(asyncAgent)).toBe(true);
    expect(isSerenAgent(fullConfigAgent)).toBe(true);
  });

  it("returns false for plain functions", () => {
    expect(isSerenAgent(() => ({}))).toBe(false);
    expect(isSerenAgent(function named() {})).toBe(false);
  });

  it("returns false for non-functions", () => {
    expect(isSerenAgent("string")).toBe(false);
    expect(isSerenAgent(123)).toBe(false);
    expect(isSerenAgent(null)).toBe(false);
    expect(isSerenAgent(undefined)).toBe(false);
    expect(isSerenAgent({})).toBe(false);
  });
});
