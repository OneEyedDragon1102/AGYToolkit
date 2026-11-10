import { FastifyInstance, FastifyPluginAsync } from "fastify";
import { itemService, CreateItemInputSchema } from "../services/item-service.js";

export const itemRoutes: FastifyPluginAsync = async (app: FastifyInstance) => {
  app.post("/items", async (request, reply) => {
    const parseResult = CreateItemInputSchema.safeParse(request.body);
    if (!parseResult.success) {
      return reply.status(400).send({
        error: "Validation failed",
        issues: parseResult.error.issues,
      });
    }

    const item = itemService.create(parseResult.data);
    return reply.status(201).send(item);
  });

  app.get("/items/:id", async (request, reply) => {
    const { id } = request.params as { id: string };
    const item = itemService.findById(id);
    if (!item) {
      return reply.status(404).send({ error: "Item not found" });
    }
    return reply.status(200).send(item);
  });

  app.get("/items", async (_request, reply) => {
    const items = itemService.listAll();
    return reply.status(200).send(items);
  });
};
