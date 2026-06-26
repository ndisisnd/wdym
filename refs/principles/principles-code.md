---
name: Prompt Engineering Principles — Coding
description: Type-specific principles loaded on top of the global base when prompt_type = code
type: reference
---

# Coding — `prompt_type = code`

Loaded **on top of** the global base (`refs/principles/principles-global.md`) when `refs/detect.md` resolves `prompt_type = code`. The `type` column marks `additive` / `subtractive` for ranking against the global pool. Rows are **ordered by impact, highest first** — used only as a tie-break between equally-applicable principles (see the global base's selection guide).

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Existing-code context | additive | Reference the surrounding code, framework, or file the change must fit. | Prompt says "it"/"this"/"the project" without showing the code | `fix the bug in it` → `Fix the off-by-one in the paginate() function below: …` |
| I/O contract | additive | State inputs, outputs, types, and the function/CLI signature. | Shape of the interface is left open | `a function to sort users` → `def sort_users(users: list[User]) -> list[User] — sorted by signup date.` |
| Edge cases & errors | additive | Require handling of empty/invalid/boundary inputs and the failure behaviour. | Prompt asks only for the happy path | `divide two numbers` → `Divide two numbers; raise ValueError on divide-by-zero and non-numeric input.` |
| Language & version | additive | Name the language and runtime/version the code must target. | Language or version is unstated or implied | `parse a date` → `In Python 3.11, parse an ISO-8601 date string.` |
| Test request | additive | Ask for unit tests or runnable usage examples alongside the code. | Correctness matters and no tests are requested | `write a slugify function` → `Write a slugify function plus pytest unit tests covering unicode and empty input.` |
| Dependency & style constraints | additive | Bound allowed libraries, style guide, and "no new dependencies" where relevant. | Open-ended; risk of pulling unwanted deps or off-house-style code | `fetch a URL` → `Fetch a URL using only the standard library — no new dependencies.` |
