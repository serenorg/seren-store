import { defineConfig } from "tsup";

export default defineConfig({
  entry: ["src/index.ts", "src/llm.ts", "src/tools.ts"],
  format: ["cjs", "esm"],
  dts: true,
  splitting: false,
  sourcemap: true,
  clean: true,
  treeshake: true,
  minify: false,
  external: ["openai", "@anthropic-ai/sdk", "@google/generative-ai"],
});
