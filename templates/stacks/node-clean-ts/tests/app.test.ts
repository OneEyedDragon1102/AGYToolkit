import { describe, it, expect, beforeEach } from "vitest";
import { buildApp } from "../src/app.js";
import { itemService } from "../src/services/item-service.js";

describe("Application API", () => {
  const app = buildApp();

  beforeEach(() => {
    itemService.clear();
  });

  it("GET /health returns 200 and healthy status", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/health",
    });

    expect(res.statusCode).toBe(200);
    const body = JSON.parse(res.payload);
    expect(body.status).toBe("ok");
    expect(typeof body.uptime).toBe("number");
  });

  it("POST /api/v1/items creates a valid item", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/items",
      payload: {
        name: "Test Item",
        price: 25.5,
      },
    });

    expect(res.statusCode).toBe(201);
    const body = JSON.parse(res.payload);
    expect(body.name).toBe("Test Item");
    expect(body.price).toBe(25.5);
    expect(body.id).toBeDefined();
  });

  it("POST /api/v1/items rejects invalid payload", async () => {
    const res = await app.inject({
      method: "POST",
      url: "/api/v1/items",
      payload: {
        name: "",
        price: -5,
      },
    });

    expect(res.statusCode).toBe(400);
    const body = JSON.parse(res.payload);
    expect(body.error).toBe("Validation failed");
  });

  it("GET /api/v1/items/:id returns 404 for missing item", async () => {
    const res = await app.inject({
      method: "GET",
      url: "/api/v1/items/00000000-0000-0000-0000-000000000000",
    });

    expect(res.statusCode).toBe(404);
  });
});
