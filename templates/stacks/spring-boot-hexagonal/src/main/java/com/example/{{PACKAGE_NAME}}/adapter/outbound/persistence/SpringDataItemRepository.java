package com.example.{{PACKAGE_NAME}}.adapter.outbound.persistence;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface SpringDataItemRepository extends JpaRepository<ItemEntity, String> {
}
