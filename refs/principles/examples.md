---
name: Prompt Engineering Principles — Worked examples & authoring guide
description: Documentation-only companion to the principle files — worked multi-principle rewrites and the format for adding custom principles. Not read during a run.
type: reference
---

# Worked examples & authoring guide

This file is **documentation only**. The skill never reads it during a run — Step 3 loads only `principles-global.md` plus the one matching type file. Read this when editing principles or learning how rewrites combine.

## Worked examples

These show 2–3 principles combined on one prompt — the row-level Exemplars in the principle files show each principle alone.

### Specificity

**Before:** `write me a function to parse dates`

**After:** `Write a Python function that parses date strings in ISO 8601 format (YYYY-MM-DD) and returns a datetime object. Raise ValueError with a descriptive message for invalid inputs. Include type hints and a docstring.`

**Principles applied:** Specificity (language, format, error handling), Output format specification (function with docstring).

---

### Positive instruction framing — negative-only prompt

**Before:** `don't make it sound robotic and don't use jargon`

**After:** `Write in a warm, conversational voice that a layperson can follow. Avoid robotic phrasing and jargon.`

**Principles applied:** Positive instruction framing (the negative rules are preserved, but a positive directive — *what to do* — is added in front), Audience framing (layperson).

---

### Few-shot examples

**Before:** `classify these support tickets by urgency`

**After:**
```
Classify each support ticket as Critical, High, Medium, or Low urgency.

Examples:
- "System is down, users cannot log in" → Critical
- "Export to CSV is slow" → Medium

Tickets to classify:
1. "Dashboard graphs are not loading"
2. "Billing shows wrong amount"
```

**Principles applied:** Few-shot examples (two labelled instances), Output format specification (four-level taxonomy).

---

### Chain-of-thought elicitation

**Before:** `should we use PostgreSQL or MongoDB for this project?`

**After:** `We are building a multi-tenant SaaS app with structured user profiles and frequent complex joins. Think through the trade-offs between PostgreSQL and MongoDB — consider schema flexibility, query patterns, and operational complexity — then give a recommendation with a one-sentence rationale.`

**Principles applied:** Context priming (project type), Chain-of-thought elicitation (think through trade-offs first), Goal specification (recommendation + rationale).

---

### Subtractive — noise removal

**Before:** `Please please take a deep breath and think very hard. You are the world's best Python expert and my job depends on this. I'll tip you $200 if you write me a function to reverse a string. Thank you so much!!`

**After:** `Write a Python function that reverses a string.`

**Principles applied:** Politeness stripping ("please", "thank you"), Magic-phrase removal ("take a deep breath", "world's best expert", "think very hard"), Manipulation removal ("my job depends on this"), Bribe removal ("I'll tip you $200"). The underlying request — reverse a string — is preserved intact.

---

## Adding custom principles

Add rows to the appropriate file — global principles to `principles-global.md`, domain principles to the matching `principles-<type>.md`. Follow the column format:
- **Principle**: short noun phrase (≤4 words)
- **Description**: what the principle adds to (or removes from) the prompt (≤20 words)
- **When to apply**: one observable trigger condition (≤15 words)
- **Exemplar**: a compact `before → after` showing the principle's effect in isolation

Type files also carry a **Type** column (`additive` / `subtractive`) used to rank against the global pool.
