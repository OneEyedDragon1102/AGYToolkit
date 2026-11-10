package com.example.{{PACKAGE_NAME}}.domain.service;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;
import com.example.{{PACKAGE_NAME}}.domain.port.inbound.CreateItemUseCase;
import com.example.{{PACKAGE_NAME}}.domain.port.inbound.GetItemUseCase;
import com.example.{{PACKAGE_NAME}}.domain.port.outbound.ItemRepositoryPort;

import java.util.List;
import java.util.Optional;

public class ItemService implements CreateItemUseCase, GetItemUseCase {

    private final ItemRepositoryPort repositoryPort;

    public ItemService(ItemRepositoryPort repositoryPort) {
        this.repositoryPort = repositoryPort;
    }

    @Override
    public Item createItem(String name, double price) {
        Item item = Item.create(name, price);
        return repositoryPort.save(item);
    }

    @Override
    public Optional<Item> getItem(String id) {
        return repositoryPort.findById(id);
    }

    @Override
    public List<Item> listItems() {
        return repositoryPort.findAll();
    }
}
