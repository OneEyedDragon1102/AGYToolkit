package com.example.{{PACKAGE_NAME}}.domain.port.inbound;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;

public interface CreateItemUseCase {
    Item createItem(String name, double price);
}
