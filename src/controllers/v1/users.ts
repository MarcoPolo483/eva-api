import type { Handler } from "../../types.js";
import { errors } from "../../util/errors.js";

export const getUserById: Handler = (ctx) => {
  const id = ctx.params.id;
  if (!id) {
    throw errors.badRequest("User ID is required");
  }
  // Mock user data
  ctx.json(200, { id, name: `User ${id}`, email: `user${id}@example.com` });
};
