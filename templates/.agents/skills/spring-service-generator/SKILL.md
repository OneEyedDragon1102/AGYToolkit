---
name: spring-service-generator
description: Generates clean, production-ready Spring Boot service slices following Hexagonal Architecture and Domain-Driven Design (DDD).
---

# Spring Service Generator Skill

## Overview
This skill provides automated scaffolding and architectural guidelines for generating Spring Boot business services. It enforces Hexagonal Architecture (Ports and Adapters), ensuring domain models remain decoupled from infrastructure, framework, and database concerns.

## Operational Protocol

1. **Package Layout Structure**:
   - `domain.model`: Core entities, value objects, domain events (Java records, zero Spring annotations).
   - `domain.port.in`: Inbound use case interfaces (e.g., `CreateOrderUseCase`).
   - `domain.port.out`: Outbound SPI interfaces (e.g., `OrderRepositoryPort`, `PaymentGatewayPort`).
   - `domain.service`: Use case implementations coordinating domain models and outbound ports.
   - `adapter.in.web`: REST controllers, DTOs, request mappers.
   - `adapter.out.persistence`: JPA repositories, database entities, persistence mappers.

2. **DTO & Entity Mapping**:
   - Map inbound request DTOs to domain objects explicitly via mappers or static factory methods.
   - Never expose JPA entities or database IDs directly to HTTP clients.

3. **Exception Handling**:
   - Throw domain-specific exceptions (e.g., `EntityNotFoundException`, `BusinessRuleViolationException`).
   - Map domain exceptions to HTTP status codes in a centralized `@RestControllerAdvice`.

4. **Transaction Demarcation**:
   - Annotate service use case methods with `@Transactional(readOnly = true)` by default, explicitly marking mutating methods as `@Transactional`.

## Quality Gate & Verification Checklist
- [ ] Domain core contains zero Spring Boot or JPA annotations.
- [ ] REST DTOs decoupled from persistence entities.
- [ ] Centralized `@RestControllerAdvice` handles all custom domain exceptions.
- [ ] File sizes remain under 300 lines per class.
- [ ] Zero emojis in source code.
