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
- **When to apply** — one observable trigger condition plus what the principle
  adds or removes (≤25 words)
- **Exemplar** — a compact `before → after` showing the principle's effect in isolation

Type files also carry a **Type** column (`additive` / `subtractive`) used to rank
against the global pool. Keep exemplars rich enough to stand alone — there is no
per-principle worked-example section; the global file keeps only two combination
patterns under **Worked examples**, loaded as flat reference context by Step 3.
