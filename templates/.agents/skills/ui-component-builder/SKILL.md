---
name: ui-component-builder
description: Builds accessible, responsive, and themeable UI components using React, TypeScript, Tailwind CSS, and headless primitives.
---

# UI Component Builder Skill

## Overview
This skill operationalizes the creation of production-grade frontend components. It enforces component modularity, accessibility (WCAG 2.1 AA), responsive layouts, and typed prop interfaces across React, Next.js, and modern web application stacks.

## Operational Protocol

1. **Component Interface Definition**:
   - Define strict TypeScript interfaces for all component props (`interface ButtonProps { ... }`).
   - Extend native HTML attributes using `React.ComponentPropsWithoutRef<T>` where applicable.
   - Forbid `any` or untyped callback parameters.

2. **Atomic Decomposition**:
   - Maintain pure presentation: Presentational components should render state passed via props and trigger callbacks.
   - Extract state management and network calls into custom hooks (e.g., `useUserData()`).
   - Keep component source files under 250 lines.

3. **Accessibility (a11y) Implementation**:
   - Use semantic HTML elements (`<button>`, `<nav>`, `<main>`, `<dialog>`) over generic `<div>` tags.
   - Provide explicit ARIA labels (`aria-label`, `aria-expanded`, `aria-describedby`) for interactive widgets.
   - Ensure complete keyboard operability (Tab, Enter, Space, Escape).

4. **Responsive Styling**:
   - Apply utility-first styling (Tailwind CSS) with mobile-first breakpoints (`sm:`, `md:`, `lg:`).
   - Ensure clean rendering across 320px mobile up to 4K ultra-wide screens.

## Quality Gate & Verification Checklist
- [ ] TypeScript compiles cleanly with zero type errors.
- [ ] Component unit tests verify rendering, user interaction, and accessibility attributes.
- [ ] All interactive elements focusable via keyboard navigation.
- [ ] Zero emojis in source code, class names, or comments.
