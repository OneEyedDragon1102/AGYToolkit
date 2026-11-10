package com.example.{{PACKAGE_NAME}}.domain.port.inbound;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;

import java.util.List;
import java.util.Optional;

public interface GetItemUseCase {
    Optional<Item> getItem(String id);
    List<Item> listItems();
}
