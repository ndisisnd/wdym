---
name: Prompt Engineering Principles — Question answering
description: Type-specific principles loaded on top of the global base when prompt_type = question
type: reference
---

# Question answering — `prompt_type = question`

Loaded **on top of** the global base (`refs/principles/principles-global.md`) when `refs/detect.md` resolves `prompt_type = question`. The `type` column marks `additive` / `subtractive` for ranking against the global pool. Rows are **ordered by impact, highest first** — used only as a tie-break between equally-applicable principles (see the global base's selection guide).

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Scope & timeframe | additive | Bound the question's scope, region, or time period. | Question is broad or time-sensitive | `best phones?` → `Best flagship phones released in 2025, UK market.` |
| Depth calibration | additive | State desired depth and length (one line vs deep dive). | Ambiguous how thorough the answer should be | `tell me about Rome` → `Give a 3-sentence overview of why Rome fell.` |
| Reasoning elicitation | additive | Ask for step-by-step reasoning before the verdict on multi-step questions. | Answer depends on a chain of inference | `is this argument valid?` → `Assess each premise step by step, then judge if the argument holds.` |
| Sourcing & citations | additive | Ask for sources, or permit "I don't know" over a guess. | Factual accuracy is critical | `what year did this happen?` → `…Cite a source, or say if you're unsure.` |
| Audience level | additive | Set the reader's expertise to calibrate vocabulary and depth. | Audience is non-default (novice or specialist) | `explain inflation` → `Explain inflation to a 12-year-old.` |

---

## Worked examples

Each worked example combines this file's principles (and the global base) on one prompt; the row **Exemplars** above show each alone. These **are parsed** at runtime: Step 3 keys each block to its principle (by the `###` heading) and attaches it as that principle's `worked_example`, used in Step 5 alongside the row Exemplar. Use them as patterns, not templates.

### Scope & timeframe

**Before:** `what are the best electric cars?`

**After:** `What are the best-value electric cars for a UK buyer in 2026, priced under £40,000, used mainly for a 60-mile daily commute?`

**Principles applied:** Scope & timeframe (UK, 2026, price cap), Specificity (use case — daily commute).

---

### Depth calibration

**Before:** `tell me about the French Revolution`

**After:** `Give me a 4-sentence overview of why the French Revolution began — just the main causes, no narrative of events.`

**Principles applied:** Depth calibration (4 sentences, overview not narrative), Constraint injection (causes only, exclude the event-by-event story).

---

### Reasoning elicitation

**Before:** `is this a good argument?`

**After:** `Here's an argument: "…". Assess each premise for truth and relevance step by step, then state whether the conclusion follows and where it's weakest.`

**Principles applied:** Reasoning elicitation (premise-by-premise before the verdict), Goal specification (verdict + weakest point).

---

### Sourcing & citations

**Before:** `when was the transistor invented?`

**After:** `When was the transistor invented, and by whom? Cite a reputable source. If accounts differ, note the disagreement rather than picking one.`

**Principles applied:** Sourcing & citations (cite a source), Uncertainty escape hatch (note disagreement instead of forcing a single answer).

---

### Audience level

**Before:** `explain inflation`

**After:** `Explain inflation to a 12-year-old using one everyday example, in about 4 sentences.`

**Principles applied:** Audience level (12-year-old), Depth calibration (one example, ~4 sentences).
