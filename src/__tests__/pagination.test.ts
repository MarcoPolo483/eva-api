import { describe, it, expect } from "vitest";
import { parsePagination } from "../util/pagination.js";

describe("pagination", () => {
  it("parses limit and offset from query params", () => {
    const query = new URLSearchParams("limit=50&offset=100");
    const result = parsePagination(query);
    expect(result.limit).toBe(50);
    expect(result.offset).toBe(100);
  });

  it("uses default limit when not provided", () => {
    const query = new URLSearchParams("offset=10");
    const result = parsePagination(query);
    expect(result.limit).toBe(50); // default limit
    expect(result.offset).toBe(10);
  });

  it("uses default offset when not provided", () => {
    const query = new URLSearchParams("limit=30");
    const result = parsePagination(query);
    expect(result.limit).toBe(30);
    expect(result.offset).toBe(0);
  });

  it("caps limit at 200", () => {
    const query = new URLSearchParams("limit=300");
    const result = parsePagination(query);
    expect(result.limit).toBe(200); // max limit
  });

  it("enforces minimum limit of 1", () => {
    const query = new URLSearchParams("limit=0");
    const result = parsePagination(query);
    expect(result.limit).toBe(1);
  });

  it("enforces minimum offset of 0", () => {
    const query = new URLSearchParams("offset=-5");
    const result = parsePagination(query);
    expect(result.offset).toBe(0);
  });

  it("handles invalid numbers gracefully", () => {
    const query = new URLSearchParams("limit=abc&offset=xyz");
    const result = parsePagination(query);
    expect(result.limit).toBe(50); // falls back to default
    expect(result.offset).toBe(0);
  });
});
