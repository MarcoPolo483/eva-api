import type { Handler, Middleware, Context } from "./types.js";
import { attachResponders } from "./util/response.js";

type Route = { method: string; path: string; handler: Handler; keys: string[]; regex: RegExp };

function compile(path: string): { regex: RegExp; keys: string[] } {
  // Very small param compiler: /api/:version/users/:id -> ^/api/([^/]+)/users/([^/]+)$
  const keys: string[] = [];
  const pattern = path
    .split("/")
    .map((seg) => {
      if (seg.startsWith(":")) {
        keys.push(seg.slice(1));
        return "([^/]+)";
      }
      return seg.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    })
    .join("/");
  const regex = new RegExp(`^${pattern}$`);
  return { regex, keys };
}

export class App {
  private middlewares: Middleware[] = [];
  private routes: Route[] = [];

  use(mw: Middleware) {
    this.middlewares.push(mw);
    return this;
  }

  route(method: string, path: string, handler: Handler) {
    const { regex, keys } = compile(path);
    this.routes.push({ method: method.toUpperCase(), path, handler, keys, regex });
    return this;
  }

  private match(method: string, url: URL): { handler: Handler; params: Record<string, string> } | undefined {
    const path = url.pathname;
    for (const r of this.routes) {
      if (r.method !== method) continue;
      const m = r.regex.exec(path);
      if (m) {
        const params: Record<string, string> = {};
        r.keys.forEach((k, i) => (params[k] = decodeURIComponent(m[i + 1] || "")));
        return { handler: r.handler, params };
      }
    }
    return undefined;
  }

  compose(): (req: any, res: any) => Promise<void> {
    const stack = this.middlewares;

    return async (req, res) => {
      const url = new URL(req.url, `http://${req.headers.host || "local"}`);
      const match = this.match(req.method, url);
      const ctx: Context = {
        req,
        res,
        params: match?.params ?? {},
        query: url.searchParams,
        state: { startTime: Date.now(), correlationId: "", requestId: "" },
        send: () => {},
        json: () => {},
        text: () => {},
        notFound: () => {},
        unauthorized: () => {},
        forbidden: () => {},
        badRequest: () => {}
      };

      attachResponders(ctx);

      let idx = -1;
      const dispatch = async (i: number): Promise<void> => {
        if (i <= idx) throw new Error("next() called multiple times");
        idx = i;
        const fn = i === stack.length ? (match ? match.handler : this.notFoundHandler) : stack[i];
        if (!fn) return;
        if (i === stack.length) {
          return (fn as Handler)(ctx) as any;
        }
        return (fn as Middleware)(ctx, () => dispatch(i + 1)) as any;
      };

      await dispatch(0);
      if (!match) this.notFoundHandler(ctx);
    };
  }

  private notFoundHandler: Handler = (ctx) => ctx.notFound();
}