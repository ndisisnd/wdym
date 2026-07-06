---
name: Authoring custom principles
description: How to add your own principles to the wdym principle files — not loaded at runtime
type: reference
---

# Adding custom principles

Not loaded during a run — reference only. Add rows to the appropriate file: global
principles to `principles-global.md`, domain principles to the matching
`principles-<type>.md`. Follow the column format:

- **Principle** — short noun phrase (≤4 words)
- **Description** — what the principle adds to (or removes from) the prompt (≤20 words)
- **When to apply** — one observable trigger condition (≤15 words)
- **Exemplar** — a compact `before → after` showing the principle's effect in isolation

Type files also carry a **Type** column (`additive` / `subtractive`) used to rank
against the global pool. When you add a principle, you may also append a matching
worked example to that file's **Worked examples** section — keyed by the principle
name (a `###` heading), combining it with 1–2 companions. Step 3 parses each worked
example and attaches it to its principle for use in Step 5.
