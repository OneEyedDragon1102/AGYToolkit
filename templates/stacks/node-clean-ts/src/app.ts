import fastify, { FastifyInstance } from "fastify";
import { healthRoutes } from "./routes/health.js";
import { itemRoutes } from "./routes/items.js";

export function buildApp(): FastifyInstance {
  const app = fastify({
    logger: process.env.NODE_ENV !== "test",
  });

  app.register(healthRoutes);
  app.register(itemRoutes, { prefix: "/api/v1" });

  return app;
}
