import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      // "server-only" melempar error bila diimpor di luar server Next; di tes cukup stub kosong.
      "server-only": fileURLToPath(new URL("./vitest.empty.ts", import.meta.url)),
    },
  },
  test: {
    environment: "node", // komponen yang butuh DOM memakai: // @vitest-environment jsdom
    include: ["src/**/*.test.{ts,tsx}"],
    setupFiles: ["./vitest.setup.ts"],
  },
});
