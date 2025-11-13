import type { IncomingMessage, ServerResponse } from "http";
import type { Socket } from "net";

export type Handler = (ctx: Context) => Promise<void> | void;
export type Middleware = (ctx: Context, next: () => Promise<void>) => Promise<void> | void;

export type UserIdentity = { id: string; roles: string[] };

export type Context = {
  req: IncomingMessage & { body?: unknown; ip?: string; socket: Socket };
  res: ServerResponse;
  params: Record<string, string>;
  query: URLSearchParams;
  state: {
    startTime: number;
    correlationId: string;
    requestId: string;
    apiVersion?: string;
    user?: UserIdentity | undefined;
    abortSignal?: AbortSignal;
  };
  send: (status: number, payload?: unknown, headers?: Record<string, string>) => void;
  json: (status: number, payload: unknown, headers?: Record<string, string>) => void;
  text: (status: number, payload: string, headers?: Record<string, string>) => void;
  notFound: () => void;
  unauthorized: (msg?: string) => void;
  forbidden: (msg?: string) => void;
  badRequest: (msg?: string) => void;
}