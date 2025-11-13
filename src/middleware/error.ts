import type { Middleware } from "../types.js";
import { ApiError, errors } from "../util/errors.js";

export function errorHandler(): Middleware {
  return async (ctx, next) => {
    try {
      await next();
    } catch (e: any) {
      const aerr: ApiError = e instanceof ApiError ? e : errors.internal(e?.message || "Internal");
      const body = {
        error: {
          code: aerr.code,
          message: aerr.message,
          ...(aerr.details ? { details: aerr.details } : {})
        },
        correlationId: ctx.state.correlationId
      };
      ctx.json(aerr.status, body);
    }
  };
}