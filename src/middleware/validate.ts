import type { Middleware } from "../types.js";
import { errors } from "../util/errors.js";

type PrimitiveType = "string" | "number" | "boolean";
type FieldSchema =
  | { type: PrimitiveType; required?: boolean; min?: number; max?: number; enum?: (string | number | boolean)[] }
  | { type: "object"; required?: boolean; properties: Record<string, FieldSchema> }
  | { type: "array"; required?: boolean; items: FieldSchema; minLength?: number; maxLength?: number };

export type Schema = { type: "object"; properties: Record<string, FieldSchema> };

export function validateBody(schema: Schema): Middleware {
  return async (ctx, next) => {
    const body = ctx.req.body;
    const errs = validate(body, schema);
    if (errs.length > 0) {
      throw errors.badRequest("Validation failed", { errors: errs });
    }
    await next();
  };
}

export function validateQuery(schema: Schema): Middleware {
  return async (ctx, next) => {
    const obj: Record<string, unknown> = {};
    ctx.query.forEach((v, k) => {
      obj[k] = v;
    });
    const errs = validate(obj, schema);
    if (errs.length > 0) {
      throw errors.badRequest("Validation failed", { errors: errs });
    }
    await next();
  };
}

function validate(value: unknown, schema: Schema | FieldSchema, path = "$"): string[] {
  const errs: string[] = [];
  if ((schema as any).type === "object" && (schema as any).properties) {
    if (value == null || typeof value !== "object" || Array.isArray(value)) {
      errs.push(`${path} should be object`);
      return errs;
    }
    const props = (schema as any).properties as Record<string, FieldSchema>;
    for (const [k, prop] of Object.entries(props)) {
      const v = (value as any)[k];
      const p = `${path}.${k}`;
      const req = (prop as any).required === true;
      if (v === undefined || v === null) {
        if (req) errs.push(`${p} is required`);
        continue;
      }
      errs.push(...validate(v, prop, p));
    }
    return errs;
  }
  if (schema.type === "array") {
    if (!Array.isArray(value)) {
      errs.push(`${path} should be array`);
      return errs;
    }
    if (schema.minLength != null && value.length < schema.minLength) errs.push(`${path} minLength ${schema.minLength}`);
    if (schema.maxLength != null && value.length > schema.maxLength) errs.push(`${path} maxLength ${schema.maxLength}`);
    value.forEach((v, i) => errs.push(...validate(v, schema.items, `${path}[${i}]`)));
    return errs;
  }
  // primitive
  if (schema.type === "string") {
    if (typeof value !== "string") errs.push(`${path} should be string`);
    if (schema.enum && !schema.enum.includes(value as any)) errs.push(`${path} must be one of ${schema.enum.join(",")}`);
    if (schema.min != null && (value as any)?.length < schema.min) errs.push(`${path} min length ${schema.min}`);
    if (schema.max != null && (value as any)?.length > schema.max) errs.push(`${path} max length ${schema.max}`);
  } else if (schema.type === "number") {
    if (typeof value !== "number" || !Number.isFinite(value)) errs.push(`${path} should be number`);
    if (schema.min != null && (value as number) < schema.min) errs.push(`${path} min ${schema.min}`);
    if (schema.max != null && (value as number) > schema.max) errs.push(`${path} max ${schema.max}`);
  } else if (schema.type === "boolean") {
    if (typeof value !== "boolean") errs.push(`${path} should be boolean`);
  }
  return errs;
}