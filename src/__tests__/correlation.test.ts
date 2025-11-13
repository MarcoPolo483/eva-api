import { describe, it, expect } from "vitest";
import { getOrCreateCorrelationId, generateId } from "../util/correlation.js";

describe("correlation", () => {
  it("getOrCreateCorrelationId returns existing header value", () => {
    const id = "existing-correlation-id";
    const result = getOrCreateCorrelationId({ "x-correlation-id": id });
    expect(result).toBe(id);
  });

  it("getOrCreateCorrelationId returns first value from array", () => {
    const result = getOrCreateCorrelationId({ "x-correlation-id": ["id1", "id2"] });
    expect(result).toBe("id1");
  });

  it("getOrCreateCorrelationId generates new ID when not present", () => {
    const result = getOrCreateCorrelationId({});
    expect(result).toBeTruthy();
    expect(typeof result).toBe("string");
  });

  it("generateId creates unique IDs", () => {
    const id1 = generateId();
    const id2 = generateId();
    expect(id1).toBeTruthy();
    expect(id2).toBeTruthy();
    expect(id1).not.toBe(id2);
  });
});
