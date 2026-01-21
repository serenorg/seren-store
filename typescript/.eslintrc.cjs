module.exports = {
  root: true,
  env: {
    node: true,
    es2022: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  plugins: ["@typescript-eslint"],
  extends: ["eslint:recommended"],
  ignorePatterns: ["dist/", "node_modules/"],
  rules: {
    // Keep lint lightweight; TypeScript already enforces unused checks via tsconfig.
    "no-unused-vars": "off",
    "@typescript-eslint/no-unused-vars": "off",
  },
};
