package com.example.{{PACKAGE_NAME}}.adapter.inbound.rest;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;
import com.example.{{PACKAGE_NAME}}.domain.port.inbound.CreateItemUseCase;
import com.example.{{PACKAGE_NAME}}.domain.port.inbound.GetItemUseCase;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/items")
public class ItemController {

    private final CreateItemUseCase createItemUseCase;
    private final GetItemUseCase getItemUseCase;

    public ItemController(CreateItemUseCase createItemUseCase, GetItemUseCase getItemUseCase) {
        this.createItemUseCase = createItemUseCase;
        this.getItemUseCase = getItemUseCase;
    }

    @PostMapping
    public ResponseEntity<ItemDto.ItemResponse> createItem(@Valid @RequestBody ItemDto.CreateItemRequest request) {
        Item item = createItemUseCase.createItem(request.name(), request.price());
        return ResponseEntity.status(HttpStatus.CREATED).body(
            new ItemDto.ItemResponse(item.getId(), item.getName(), item.getPrice())
        );
    }

    @GetMapping("/{id}")
    public ResponseEntity<ItemDto.ItemResponse> getItem(@PathVariable String id) {
        return getItemUseCase.getItem(id)
            .map(item -> ResponseEntity.ok(new ItemDto.ItemResponse(item.getId(), item.getName(), item.getPrice())))
            .orElseGet(() -> ResponseEntity.notFound().build());
    }

    @GetMapping
    public ResponseEntity<List<ItemDto.ItemResponse>> listItems() {
        List<ItemDto.ItemResponse> items = getItemUseCase.listItems().stream()
            .map(item -> new ItemDto.ItemResponse(item.getId(), item.getName(), item.getPrice()))
            .toList();
        return ResponseEntity.ok(items);
    }
}
