package com.example.{{PACKAGE_NAME}}.adapter.outbound.persistence;

import com.example.{{PACKAGE_NAME}}.domain.model.Item;
import com.example.{{PACKAGE_NAME}}.domain.port.outbound.ItemRepositoryPort;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@Component
public class ItemPersistenceAdapter implements ItemRepositoryPort {

    private final SpringDataItemRepository repository;

    public ItemPersistenceAdapter(SpringDataItemRepository repository) {
        this.repository = repository;
    }

    @Override
    public Item save(Item item) {
        ItemEntity entity = new ItemEntity(item.getId(), item.getName(), item.getPrice());
        ItemEntity saved = repository.save(entity);
        return new Item(saved.getId(), saved.getName(), saved.getPrice());
    }

    @Override
    public Optional<Item> findById(String id) {
        return repository.findById(id)
            .map(entity -> new Item(entity.getId(), entity.getName(), entity.getPrice()));
    }

    @Override
    public List<Item> findAll() {
        return repository.findAll().stream()
            .map(entity -> new Item(entity.getId(), entity.getName(), entity.getPrice()))
            .toList();
    }
}
