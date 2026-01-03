import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    globals: true,
    include: ["**/*.test.{ts,tsx}"],
    setupFiles: ["./test-setup.ts"],
  },
  resolve: {
    alias: {
      // Map source imports to the actual source directory
      "@common": path.resolve(__dirname, "../../src/trellis/platforms/common/client/src"),
      // Use local node_modules for React (source files import react directly)
      "react": path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      "react-aria": path.resolve(__dirname, "node_modules/react-aria"),
    },
  },
});
