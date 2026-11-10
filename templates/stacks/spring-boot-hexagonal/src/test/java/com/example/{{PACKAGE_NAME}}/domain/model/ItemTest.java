package com.example.{{PACKAGE_NAME}}.domain.model;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ItemTest {

    @Test
    @DisplayName("Should create item with valid inputs")
    void shouldCreateItemWithValidInputs() {
        Item item = Item.create("Widget", 29.99);

        assertNotNull(item.getId());
        assertEquals("Widget", item.getName());
        assertEquals(29.99, item.getPrice());
    }

    @Test
    @DisplayName("Should reject blank or null name")
    void shouldRejectBlankOrNullName() {
        assertThrows(IllegalArgumentException.class, () -> Item.create("", 10.0));
        assertThrows(IllegalArgumentException.class, () -> Item.create("   ", 10.0));
        assertThrows(IllegalArgumentException.class, () -> Item.create(null, 10.0));
    }

    @Test
    @DisplayName("Should reject negative price")
    void shouldRejectNegativePrice() {
        assertThrows(IllegalArgumentException.class, () -> Item.create("Gadget", -1.0));
    }
}
