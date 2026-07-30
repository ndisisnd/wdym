---
name: Prompt Engineering Principles — Coding
description: Type-specific principles loaded on top of the global base when prompt_type = code
type: reference
---

# Coding — `prompt_type = code`

Loaded **on top of** the global base when `prompt_type = code`. The `type` column
marks `additive`/`subtractive` for ranking against the global pool. Rows are
impact-ordered, highest first (tie-break only).

| Principle | Type | When to apply | Exemplar |
|-----------|------|---------------|----------|
| Existing-code context | additive | Prompt says "it"/"this"/"the project" without identifying the code — point at the file, function, or symptom (the agent reads the code itself; don't paste it) | `fix the bug in it` → `Fix the off-by-one in paginate() in api/list.py — it drops the last record when total isn't a multiple of page_size.` |
| Verification & done criteria | additive | A change is requested with no way to confirm it worked — state what done looks like (tests pass, behaviour observed) | `add retry logic to the fetcher` → `Add retry logic to the fetcher — exponential backoff, max 3 attempts. Done = existing tests pass, plus a new test showing a transient failure succeeds on retry.` |
| I/O contract | additive | Interface shape left open — state inputs, outputs, types, signature | `a function to sort users` → `Write def sort_users(users: list[User]) -> list[User], sorted by signup_date descending, None dates last; do not mutate the input.` |
| Edge cases & errors | additive | Prompt asks only for the happy path — require empty/invalid/boundary handling and failure behaviour | `parse the amount from the string` → `Parse "$1,299.00"-style strings into a Decimal; handle separators and negatives in parentheses, raise ValueError on anything unparseable.` |
| Language & version | additive | Language or runtime unstated — name them | `make a config loader` → `In Python 3.12, write a config loader using stdlib tomllib returning a frozen dataclass.` |
| Test request | additive | Correctness matters and no tests are requested — ask for unit tests or runnable examples | `write a slugify function` → `Write a slugify() function plus pytest tests covering unicode accents, leading/trailing spaces, and empty input.` |
| Dependency & style constraints | additive | Open-ended; risk of unwanted deps or off-style code — bound libraries and style | `fetch a URL and return the json` → `Fetch a URL and return parsed JSON using only the standard library — no requests/httpx; type hints, 5-second timeout.` |

**Combination pattern:** exemplars combine naturally — e.g. `fix the bug in it` →
show the actual code (Existing-code context) + name the exact symptom (Specificity)
+ state how to verify the fix (Verification & done criteria).
