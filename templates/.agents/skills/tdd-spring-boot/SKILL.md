---
name: tdd-spring-boot
description: Executes Red-Green-Refactor test-driven development for Java 23 and Spring Boot services using JUnit 5, Mockito, and AssertJ.
---

# TDD Spring Boot Skill

## Overview
This skill guides the implementation of Java 23 and Spring Boot backend components using rigorous Test-Driven Development (TDD). It enforces writing failing tests before application code, verifying mock interactions, and maintaining 80%+ branch coverage.

## Operational Protocol

1. **Phase 1: Red (Failing Test First)**:
   - Create unit test class in `src/test/java/...` using JUnit 5 and AssertJ.
   - Mock external dependencies using Mockito (`@Mock`, `@InjectMocks`).
   - Define expected behavior for happy path and edge cases (null inputs, exceptions, empty collections).
   - Execute test target (`mvn test -Dtest=ClassNameTest`) and confirm it fails for the expected reason (compile error or assertion failure).

2. **Phase 2: Green (Minimal Implementation)**:
   - Write the simplest possible code in `src/main/java/...` to make the test pass.
   - Adhere strictly to hexagonal architecture (domain core isolated from web/persistence adapters).
   - Re-run test and confirm green status.

3. **Phase 3: Refactor (Hygiene & Optimization)**:
   - Eliminate code duplication, improve naming, and enforce immutability (`record`, `final`).
   - Re-run test suite to guarantee regression freedom.

4. **Integration Verification**:
   - For repository or controller testing, use `@DataJpaTest` or `@WebMvcTest` with `@AutoConfigureMockMvc`.
   - Never load the entire Spring ApplicationContext (`@SpringBootTest`) for pure unit tests.

## Quality Gate & Verification Checklist
- [ ] Test written and verified failing prior to production code implementation.
- [ ] Unit tests run in under 2 seconds without full application context initialization.
- [ ] Line and branch coverage meets or exceeds 80%.
- [ ] Zero emojis in test descriptions or code.
