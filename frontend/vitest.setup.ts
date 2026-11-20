import { afterEach } from "vitest";

// Pembersihan DOM untuk tes komponen (jsdom) tanpa bergantung pada globals vitest.
afterEach(async () => {
  if (typeof document !== "undefined" && "body" in document) {
    const { cleanup } = await import("@testing-library/react");
    cleanup();
  }
});
