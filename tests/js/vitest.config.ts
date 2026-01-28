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
      "@browser": path.resolve(__dirname, "../../src/trellis/platforms/browser/client/src"),
      // Mock the pre-built worker bundle for tests (must come before general @trellis/* aliases)
      "@trellis/trellis-browser/pyodide.worker-bundle": path.resolve(__dirname, "mocks/pyodide.worker-bundle.ts"),
      // @trellis/* aliases (matches esbuild build aliases)
      "@trellis/trellis-browser": path.resolve(__dirname, "../../src/trellis/platforms/browser"),
      "@trellis/trellis-core": path.resolve(__dirname, "../../src/trellis/platforms/common"),
      "@trellis/trellis-server": path.resolve(__dirname, "../../src/trellis/platforms/server"),
      "@trellis/trellis-desktop": path.resolve(__dirname, "../../src/trellis/platforms/desktop"),
      // Use local node_modules for packages (source files import directly)
      "react": path.resolve(__dirname, "node_modules/react"),
      "react-dom": path.resolve(__dirname, "node_modules/react-dom"),
      "react-aria": path.resolve(__dirname, "node_modules/react-aria"),
      "react-stately": path.resolve(__dirname, "node_modules/react-stately"),
      "lucide-react": path.resolve(__dirname, "node_modules/lucide-react"),
      "@msgpack/msgpack": path.resolve(__dirname, "node_modules/@msgpack/msgpack"),
      "recharts": path.resolve(__dirname, "node_modules/recharts"),
      "uplot": path.resolve(__dirname, "node_modules/uplot"),
    },
  },
});
