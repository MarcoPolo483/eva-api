import type { Middleware } from "../types.js";

export function securityHeaders(): Middleware {
  return async (ctx, next) => {
    ctx.res.setHeader("X-Content-Type-Options", "nosniff");
    ctx.res.setHeader("X-Frame-Options", "DENY");
    ctx.res.setHeader("Referrer-Policy", "no-referrer");
    ctx.res.setHeader("Permissions-Policy", "geolocation=(), microphone=(), camera=()");
    // CSP minimal default; adjust behind APIM if needed
    ctx.res.setHeader("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'");
    await next();
  };
}