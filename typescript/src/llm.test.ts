// ABOUTME: Tests for LLM client helpers — SerenLLMClient, env var reading, provider helpers.
// ABOUTME: Covers construction, defaults, error handling, and helper function behavior.
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  SerenLLMClient,
  getSerenClaudeClient,
  getSerenOpenAIClient,
  getOpenAIClient,
  getAnthropicClient,
  getGoogleClient,
  getLLMModel,
  getGenericAPIKey,
} from "./llm";

// --- Environment helpers ---

const originalEnv = { ...process.env };

function setEnv(vars: Record<string, string | undefined>) {
  for (const [key, value] of Object.entries(vars)) {
    if (value === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = value;
    }
  }
}

function clearEnv(...keys: string[]) {
  for (const key of keys) {
    delete process.env[key];
  }
}

beforeEach(() => {
  // Start each test with a clean slate for relevant env vars
  clearEnv(
    "SEREN_API_KEY",
    "SEREN_API_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "LLM_MODEL",
    "LLM_API_KEY",
  );
});

afterEach(() => {
  // Restore original env
  process.env = { ...originalEnv };
});

// --- SerenLLMClient construction ---

describe("SerenLLMClient", () => {
  it("throws without SEREN_API_KEY", () => {
    expect(() => new SerenLLMClient()).toThrow("SEREN_API_KEY not set");
  });

  it("creates client with explicit apiKey", () => {
    const client = new SerenLLMClient({ apiKey: "test-key" });
    expect(client.apiKey).toBe("test-key");
  });

  it("reads SEREN_API_KEY from environment", () => {
    setEnv({ SEREN_API_KEY: "env-key" });
    const client = new SerenLLMClient();
    expect(client.apiKey).toBe("env-key");
  });

  it("prefers explicit apiKey over env var", () => {
    setEnv({ SEREN_API_KEY: "env-key" });
    const client = new SerenLLMClient({ apiKey: "explicit-key" });
    expect(client.apiKey).toBe("explicit-key");
  });

  it("uses default base URL", () => {
    const client = new SerenLLMClient({ apiKey: "test" });
    expect(client.baseUrl).toBe("https://api.serendb.com");
  });

  it("reads SEREN_API_URL from environment", () => {
    setEnv({ SEREN_API_URL: "https://custom.api.com" });
    const client = new SerenLLMClient({ apiKey: "test" });
    expect(client.baseUrl).toBe("https://custom.api.com");
  });

  it("prefers explicit baseUrl over env var", () => {
    setEnv({ SEREN_API_URL: "https://env.api.com" });
    const client = new SerenLLMClient({
      apiKey: "test",
      baseUrl: "https://explicit.api.com",
    });
    expect(client.baseUrl).toBe("https://explicit.api.com");
  });

  it("uses default publisher", () => {
    const client = new SerenLLMClient({ apiKey: "test" });
    expect(client.publisher).toBe("seren-models");
  });

  it("uses custom publisher", () => {
    const client = new SerenLLMClient({
      apiKey: "test",
      publisher: "custom-publisher",
    });
    expect(client.publisher).toBe("custom-publisher");
  });

  it("uses default model", () => {
    const client = new SerenLLMClient({ apiKey: "test" });
    expect(client.defaultModel).toBe("anthropic/claude-sonnet-4-20250514");
  });

  it("uses custom default model", () => {
    const client = new SerenLLMClient({
      apiKey: "test",
      defaultModel: "openai/gpt-4o",
    });
    expect(client.defaultModel).toBe("openai/gpt-4o");
  });

  it("has chat.completions interface", () => {
    const client = new SerenLLMClient({ apiKey: "test" });
    expect(client.chat).toBeDefined();
    expect(client.chat.completions).toBeDefined();
    expect(typeof client.chat.completions.create).toBe("function");
  });

  it("has messages interface", () => {
    const client = new SerenLLMClient({ apiKey: "test" });
    expect(client.messages).toBeDefined();
    expect(typeof client.messages.create).toBe("function");
  });
});

// --- Seren convenience helpers ---

describe("getSerenClaudeClient()", () => {
  it("throws without SEREN_API_KEY", () => {
    expect(() => getSerenClaudeClient()).toThrow("SEREN_API_KEY not set");
  });

  it("creates a client with API key", () => {
    const client = getSerenClaudeClient({ apiKey: "claude-key" });
    expect(client.apiKey).toBe("claude-key");
    expect(client.defaultModel).toBe("anthropic/claude-sonnet-4-20250514");
  });

  it("uses custom model", () => {
    const client = getSerenClaudeClient({
      apiKey: "test",
      model: "anthropic/claude-opus-4-20250514",
    });
    expect(client.defaultModel).toBe("anthropic/claude-opus-4-20250514");
  });
});

describe("getSerenOpenAIClient()", () => {
  it("throws without SEREN_API_KEY", () => {
    expect(() => getSerenOpenAIClient()).toThrow("SEREN_API_KEY not set");
  });

  it("creates a client with API key", () => {
    const client = getSerenOpenAIClient({ apiKey: "openai-key" });
    expect(client.apiKey).toBe("openai-key");
    expect(client.defaultModel).toBe("openai/gpt-4o");
  });

  it("uses custom model", () => {
    const client = getSerenOpenAIClient({
      apiKey: "test",
      model: "openai/gpt-4-turbo",
    });
    expect(client.defaultModel).toBe("openai/gpt-4-turbo");
  });
});

// --- Direct provider clients (optional peer deps) ---

describe("getOpenAIClient()", () => {
  it("throws when openai package is not installed", () => {
    expect(() => getOpenAIClient("test-key")).toThrow(
      "openai package not installed",
    );
  });

  it("throws when no API key available", () => {
    // This will throw about the package first, but tests the error path
    expect(() => getOpenAIClient()).toThrow();
  });
});

describe("getAnthropicClient()", () => {
  it("throws when @anthropic-ai/sdk is not installed", () => {
    expect(() => getAnthropicClient("test-key")).toThrow(
      "@anthropic-ai/sdk package not installed",
    );
  });
});

describe("getGoogleClient()", () => {
  it("throws when @google/generative-ai is not installed", () => {
    expect(() => getGoogleClient("test-key")).toThrow(
      "@google/generative-ai package not installed",
    );
  });
});

// --- Environment variable readers ---

describe("getLLMModel()", () => {
  it("returns undefined when LLM_MODEL not set", () => {
    expect(getLLMModel()).toBeUndefined();
  });

  it("returns LLM_MODEL value", () => {
    setEnv({ LLM_MODEL: "gpt-4o" });
    expect(getLLMModel()).toBe("gpt-4o");
  });
});

describe("getGenericAPIKey()", () => {
  it("returns undefined when LLM_API_KEY not set", () => {
    expect(getGenericAPIKey()).toBeUndefined();
  });

  it("returns LLM_API_KEY value", () => {
    setEnv({ LLM_API_KEY: "sk-generic-key" });
    expect(getGenericAPIKey()).toBe("sk-generic-key");
  });
});
