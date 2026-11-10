package com.example.{{PACKAGE_NAME}}.adapter.inbound.rest;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;
import com.example.{{PACKAGE_NAME}}.domain.port.inbound.CreateItemUseCase;
import com.example.{{PACKAGE_NAME}}.domain.port.inbound.GetItemUseCase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;
import java.util.Optional;

import static org.mockito.ArgumentMatchers.anyDouble;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(ItemController.class)
class ItemControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CreateItemUseCase createItemUseCase;

    @MockBean
    private GetItemUseCase getItemUseCase;

    @Test
    @DisplayName("POST /api/v1/items should return 201 Created")
    void shouldCreateItem() throws Exception {
        Item item = new Item("item-123", "Test Item", 49.99);
        when(createItemUseCase.createItem(anyString(), anyDouble())).thenReturn(item);

        String payload = """
            {
                "name": "Test Item",
                "price": 49.99
            }
            """;

        mockMvc.perform(post("/api/v1/items")
                .contentType(MediaType.APPLICATION_JSON)
                .content(payload))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").value("item-123"))
            .andExpect(jsonPath("$.name").value("Test Item"))
            .andExpect(jsonPath("$.price").value(49.99));
    }

    @Test
    @DisplayName("GET /api/v1/items/{id} should return 200 when found")
    void shouldGetItemById() throws Exception {
        Item item = new Item("item-123", "Found Item", 15.0);
        when(getItemUseCase.getItem("item-123")).thenReturn(Optional.of(item));

        mockMvc.perform(get("/api/v1/items/item-123"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value("item-123"))
            .andExpect(jsonPath("$.name").value("Found Item"));
    }

    @Test
    @DisplayName("GET /api/v1/items/{id} should return 404 when missing")
    void shouldReturn404WhenMissing() throws Exception {
        when(getItemUseCase.getItem("missing")).thenReturn(Optional.empty());

        mockMvc.perform(get("/api/v1/items/missing"))
            .andExpect(status().isNotFound());
    }

    @Test
    @DisplayName("GET /api/v1/items should list items")
    void shouldListItems() throws Exception {
        Item item = new Item("item-1", "First", 10.0);
        when(getItemUseCase.listItems()).thenReturn(List.of(item));

        mockMvc.perform(get("/api/v1/items"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].name").value("First"));
    }
}
