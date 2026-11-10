package com.example.{{PACKAGE_NAME}}.domain.port.outbound;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;

import java.util.List;
import java.util.Optional;

public interface ItemRepositoryPort {
    Item save(Item item);
    Optional<Item> findById(String id);
    List<Item> findAll();
}
