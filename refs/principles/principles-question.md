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
