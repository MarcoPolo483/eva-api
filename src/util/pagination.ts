export type Pagination = { limit: number; offset: number };

export function parsePagination(params: URLSearchParams, defaults: Pagination = { limit: 50, offset: 0 }, max = 200): Pagination {
  const limit = clamp(intOrDefault(params.get("limit"), defaults.limit), 1, max);
  const offset = Math.max(0, intOrDefault(params.get("offset"), defaults.offset));
  return { limit, offset };
}

function intOrDefault(v: string | null, d: number): number {
  if (!v) return d;
  const n = Number(v);
  return Number.isFinite(n) ? Math.floor(n) : d;
}

function clamp(n: number, min: number, max: number) {
  return Math.max(min, Math.min(max, n));
}