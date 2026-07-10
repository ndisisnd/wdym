---
name: Prompt Engineering Principles — Language & text generation
description: Type-specific principles loaded on top of the global base when prompt_type = text-gen
type: reference
---

# Language & text generation — `prompt_type = text-gen`

Loaded **on top of** the global base when `prompt_type = text-gen`. The `type`
column marks `additive`/`subtractive` for ranking against the global pool. Rows
are impact-ordered, highest first (tie-break only).

| Principle | Type | When to apply | Exemplar |
|-----------|------|---------------|----------|
| Audience & purpose | additive | Purpose or reader unclear — state who reads it and the goal/CTA | `write a blurb for our product` → `Write a homepage blurb that gets enterprise IT buyers to book a demo — lead with the pain it removes, not the feature list.` |
| Format & length | additive | Output shape or length unstated — name the artifact and size | `write about our launch` → `Write a 5-bullet internal Slack announcement of our v2 launch — what shipped, why it matters, what to do next.` |
| Source-text anchoring | additive | Prompt refers to text not actually included — quote or attach it | `make this shorter` → `Shorten the paragraph below to under 50 words without losing the refund deadline or contact email: "…"` |
| Fidelity constraint | additive | Task transforms an existing text — require meaning and key facts preserved | `summarize this report` → `Summarize the report below in 6 bullets; keep every figure, date, and name accurate — no rounding or paraphrased quotes.` |
| Tone & register | additive | Register undefined — fix tone and formality for the channel | `reply to this customer email` → `Reply in a warm but professional tone — acknowledge the delay, no corporate jargon, end with a concrete next step: "…"` |
