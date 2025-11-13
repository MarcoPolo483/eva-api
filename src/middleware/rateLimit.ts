import type { Middleware } from "../types.js";
import { errors } from "../util/errors.js";

type Bucket = { tokens: number; last: number; capacity: number; refillPerSec: number };

export function rateLimit(rps: number): Middleware {
  const buckets = new Map<string, Bucket>();
  const capacity = Math.max(1, rps);
  const refillPerSec = rps;

  function keyFrom(ctx: any): string {
    const hdr = ctx.req.headers["x-forwarded-for"];
    if (typeof hdr === "string" && hdr) return hdr.split(",")[0].trim();
    return ctx.req.socket.remoteAddress || "local";
  }

  function take(k: string): boolean {
    const now = Date.now();
    const b = buckets.get(k) ?? { tokens: capacity, last: now, capacity, refillPerSec };
    const elapsed = (now - b.last) / 1000;
    b.tokens = Math.min(b.capacity, b.tokens + elapsed * b.refillPerSec);
    b.last = now;
    if (b.tokens >= 1) {
      b.tokens -= 1;
      buckets.set(k, b);
      return true;
    }
    buckets.set(k, b);
    return false;
  }

  return async (ctx, next) => {
    const k = keyFrom(ctx);
    if (!take(k)) {
      ctx.res.setHeader("Retry-After", "1");
      throw errors.tooManyRequests();
    }
    await next();
  };
}