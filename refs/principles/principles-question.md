---
name: Prompt Engineering Principles — Question answering
description: Type-specific principles loaded on top of the global base when prompt_type = question
type: reference
---

# Question answering — `prompt_type = question`

Loaded **on top of** the global base when `prompt_type = question`. The `type`
column marks `additive`/`subtractive` for ranking against the global pool. Rows
are impact-ordered, highest first (tie-break only).

| Principle | Type | When to apply | Exemplar |
|-----------|------|---------------|----------|
| Scope & timeframe | additive | Question is broad or time-sensitive — bound scope, region, or period | `what are the best electric cars?` → `Best-value electric cars for a UK buyer in 2026, under £40,000, mainly for a 60-mile daily commute?` |
| Depth calibration | additive | Ambiguous how thorough the answer should be — state depth and length | `tell me about the French Revolution` → `Give a 4-sentence overview of why the French Revolution began — main causes only, no event narrative.` |
| Reasoning elicitation | additive | **Display only:** the reader needs to check the steps — ask for the reasoning to be shown before the verdict (models already reason internally; this shapes the output, not its quality) | `is this a good argument?` → `Assess each premise for truth and relevance step by step, then state whether the conclusion follows and where it's weakest.` |
| Sourcing & citations | additive | Factual accuracy critical — ask for sources, permit "I don't know" over a guess | `when was the transistor invented?` → `When was the transistor invented, and by whom? Cite a source; if accounts differ, note the disagreement.` |
| Audience level | additive | Audience is non-default (novice or specialist) — set the reader's expertise | `explain inflation` → `Explain inflation to a 12-year-old using one everyday example, in about 4 sentences.` |
