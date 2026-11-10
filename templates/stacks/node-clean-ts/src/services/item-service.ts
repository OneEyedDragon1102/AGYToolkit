import { z } from "zod";
import crypto from "crypto";

export const ItemSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, "Name must not be empty"),
  price: z.number().nonnegative("Price must be non-negative"),
  createdAt: z.string().datetime(),
});

export const CreateItemInputSchema = z.object({
  name: z.string().min(1, "Name must not be empty"),
  price: z.number().nonnegative("Price must be non-negative"),
});

export type Item = z.infer<typeof ItemSchema>;
export type CreateItemInput = z.infer<typeof CreateItemInputSchema>;

export class ItemService {
  private readonly items: Map<string, Item> = new Map();

  create(input: CreateItemInput): Item {
    const validated = CreateItemInputSchema.parse(input);
    const item: Item = {
      id: crypto.randomUUID(),
      name: validated.name.trim(),
      price: validated.price,
      createdAt: new Date().toISOString(),
    };
    this.items.set(item.id, item);
    return item;
  }

  findById(id: string): Item | undefined {
    return this.items.get(id);
  }

  listAll(): Item[] {
    return Array.from(this.items.values());
  }

  clear(): void {
    this.items.clear();
  }
}

export const itemService = new ItemService();
