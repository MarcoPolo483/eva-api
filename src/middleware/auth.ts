import type { Middleware } from "../types.js";

/**
 * Trusts APIM to validate JWT and forwards identity via headers:
 * - X-User-Id: user/object id
 * - X-Roles: comma-separated roles
 */
export function authFromHeaders(): Middleware {
  return async (ctx, next) => {
    const uid = header(ctx.req.headers, "x-user-id");
    const rolesRaw = header(ctx.req.headers, "x-roles");
    const roles = rolesRaw ? rolesRaw.split(",").map((s) => s.trim()).filter(Boolean) : [];
    if (uid) {
      ctx.state.user = { id: uid, roles };
    }
    await next();
  };
}

/** Require a role present in ctx.state.user.roles */
export function requireRole(role: string): Middleware {
  return async (ctx, next) => {
    const has = ctx.state.user?.roles.includes(role);
    if (!has) return ctx.unauthorized("Missing required role");
    await next();
  };
}

function header(headers: Record<string, string | string[] | undefined>, key: string): string | undefined {
  const v = headers[key] ?? headers[key.toLowerCase()];
  if (Array.isArray(v)) return v[0];
  return v;
}