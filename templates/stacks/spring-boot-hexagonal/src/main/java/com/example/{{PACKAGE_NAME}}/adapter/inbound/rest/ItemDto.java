package com.example.{{PACKAGE_NAME}}.adapter.inbound.rest;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;

public class ItemDto {

    public record CreateItemRequest(
        @NotBlank(message = "Item name must not be blank")
        String name,

        @PositiveOrZero(message = "Item price must be positive or zero")
        double price
    ) {}

    public record ItemResponse(
        String id,
        String name,
        double price
    ) {}
}
