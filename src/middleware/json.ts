import type { Middleware } from "../types.js";
import { errors } from "../util/errors.js";

export function jsonBodyParser(limitBytes: number): Middleware {
  return async (ctx, next) => {
    const req = ctx.req;
    const method = (req.method || "GET").toUpperCase();
    if (method === "GET" || method === "HEAD" || method === "OPTIONS") return next();

    const contentType = String(req.headers["content-type"] || "");
    if (!contentType.includes("application/json")) {
      return next();
    }

    let total = 0;
    const chunks: Uint8Array[] = [];

    await new Promise<void>((resolve, reject) => {
      req.on("data", (chunk: Buffer) => {
        total += chunk.length;
        if (total > limitBytes) {
          req.pause(); // Stop reading more data
          reject(errors.badRequest("Payload too large"));
          return;
        }
        chunks.push(new Uint8Array(chunk));
      });
      req.on("end", resolve);
      req.on("error", reject);
      req.on("close", () => resolve()); // client aborted
    });

    if (chunks.length > 0) {
      const buf = Buffer.concat(chunks as any);
      try {
        ctx.req.body = JSON.parse(buf.toString("utf8"));
      } catch {
        throw errors.badRequest("Invalid JSON");
      }
    }

    await next();
  };
}
