# eva-api (Enterprise Edition)

Enhancements in this bundle
- Version negotiation: resolve API version from path (/api/v1/...) or header (x-api-version). Exposes ctx.state.apiVersion.
- Structured errors: consistent envelopes { error: { code, message, details? }, correlationId }.
- Request ID: generate and propagate x-request-id; include in logs.
- Security headers: baseline hardening headers.
- Timeouts: per-request timeout and client abort handling (504 on timeout).
- Validation: small runtime validator for bodies and queries (no external deps).
- Router with path params: routes like /api/:version/users/:id.
- Pagination helper: robust parsing and bounds.

APIM remains the front-door for JWT validation and rate limiting; this layer adds defense-in-depth and robust developer ergonomics.