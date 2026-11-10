package com.example.{{PACKAGE_NAME}}.config;

import com.example.{{PACKAGE_NAME}}.domain.port.outbound.ItemRepositoryPort;
import com.example.{{PACKAGE_NAME}}.domain.service.ItemService;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class HexagonalConfig {

    @Bean
    public ItemService itemService(ItemRepositoryPort repositoryPort) {
        return new ItemService(repositoryPort);
    }
}
