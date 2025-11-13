export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: unknown
  ) {
    super(message);
  }
}

export const errors = {
  badRequest: (message = "Bad Request", details?: unknown) => new ApiError(400, "BAD_REQUEST", message, details),
  unauthorized: (message = "Unauthorized", details?: unknown) => new ApiError(401, "UNAUTHORIZED", message, details),
  forbidden: (message = "Forbidden", details?: unknown) => new ApiError(403, "FORBIDDEN", message, details),
  notFound: (message = "Not Found", details?: unknown) => new ApiError(404, "NOT_FOUND", message, details),
  tooManyRequests: (message = "Too Many Requests", details?: unknown) => new ApiError(429, "TOO_MANY_REQUESTS", message, details),
  timeout: (message = "Gateway Timeout", details?: unknown) => new ApiError(504, "GATEWAY_TIMEOUT", message, details),
  internal: (message = "Internal Server Error", details?: unknown) => new ApiError(500, "INTERNAL", message, details),
} as const;