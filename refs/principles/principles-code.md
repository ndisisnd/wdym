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

---

## Worked examples

Each worked example combines this file's principles (and the global base) on one prompt; the row **Exemplars** above show each alone. These **are parsed** at runtime: Step 3 keys each block to its principle (by the `###` heading) and attaches it as that principle's `worked_example`, used in Step 5 alongside the row Exemplar. Use them as patterns, not templates.

### Existing-code context

**Before:** `fix the bug in it`

**After:**
```
Fix the off-by-one in the paginate() function below — it drops the last record when total isn't a multiple of page_size:

def paginate(items, page, page_size):
    start = page * page_size
    return items[start:start + page_size]
```

**Principles applied:** Existing-code context (the actual function is shown), Specificity (names the exact symptom — last record dropped).

---

### I/O contract

**Before:** `a function to sort users`

**After:** `Write def sort_users(users: list[User]) -> list[User] that returns users sorted by signup_date descending, with None dates last. Do not mutate the input.`

**Principles applied:** I/O contract (signature, types, ordering, return), Edge cases & errors (None dates, no mutation).

---

### Edge cases & errors

**Before:** `parse the amount from the string`

**After:** `Write a function that parses a currency amount from a string like "$1,299.00" into a Decimal. Handle missing symbols, thousands separators, and negatives in parentheses; raise ValueError on anything unparseable.`

**Principles applied:** Edge cases & errors (separators, negatives, unparseable → ValueError), I/O contract (string in, Decimal out).

---

### Language & version

**Before:** `make a config loader`

**After:** `In Python 3.12, write a config loader that reads a TOML file with the stdlib tomllib and returns a frozen dataclass. No third-party libraries.`

**Principles applied:** Language & version (Python 3.12 — so tomllib is stdlib), Dependency & style constraints (no third-party libs).

---

### Test request

**Before:** `write a slugify function`

**After:** `Write a slugify() function that lowercases, strips punctuation, and joins words with hyphens. Add pytest tests covering unicode accents, leading/trailing spaces, and empty input.`

**Principles applied:** Test request (pytest cases named), Edge cases & errors (unicode, spaces, empty input).

---

### Dependency & style constraints

**Before:** `fetch a URL and return the json`

**After:** `Fetch a URL and return the parsed JSON using only the standard library — no requests or httpx. Follow PEP 8, add type hints, and time out after 5 seconds.`

**Principles applied:** Dependency & style constraints (stdlib only, PEP 8, type hints), Edge cases & errors (5-second timeout).
