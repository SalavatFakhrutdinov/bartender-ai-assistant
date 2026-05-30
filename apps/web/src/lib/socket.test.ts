import { describe, it, expect } from "vitest";
import { getSocket } from "./socket";

describe("socket client", () => {
  it("returns a socket instance", () => {
    const socket = getSocket();
    expect(socket).toBeDefined();
  });
});
