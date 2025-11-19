import type { Middleware } from "../types.js";
import { errors } from "../util/errors.js";

export function withTimeout(ms: number): Middleware {
  return async (ctx, next) => {
    const ac = new AbortController();
    ctx.state.abortSignal = ac.signal;

    const onClose = () => ac.abort();
    ctx.req.on("close", onClose);

    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      ac.abort();
      if (!ctx.res.headersSent) {
        const body = { error: { code: "GATEWAY_TIMEOUT", message: "Request timed out" }, correlationId: ctx.state.correlationId };
        ctx.json(504, body);
      }
    }, ms);

    try {
      await next();
      if (timedOut) return;
    } finally {
      clearTimeout(timer);
      ctx.req.off("close", onClose);
    }
  };
}
