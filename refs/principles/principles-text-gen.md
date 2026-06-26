---
name: Prompt Engineering Principles — Language & text generation
description: Type-specific principles loaded on top of the global base when prompt_type = text-gen
type: reference
---

# Language & text generation — `prompt_type = text-gen`

Loaded **on top of** the global base (`refs/principles/principles-global.md`) when `refs/detect.md` resolves `prompt_type = text-gen`. The `type` column marks `additive` / `subtractive` for ranking against the global pool.

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Format & length | additive | Name the artifact and size (email, 200-word blurb, 5 bullets). | Output shape or length unstated | `write about our launch` → `Write a 5-bullet internal announcement of our launch.` |
| Tone & register | additive | Fix tone and formality for the channel. | Register undefined | `reply to this email` → `Reply in a warm but professional tone.` |
| Audience & purpose | additive | State the reader and the goal/CTA the text must achieve. | Purpose or reader unclear | `write a blurb` → `Write a blurb that gets enterprise buyers to book a demo.` |
| Fidelity constraint | additive | For translate/summarise/rewrite, require meaning preserved and key facts kept. | Task transforms an existing text | `summarize this report` → `Summarize this report; keep every figure and date accurate.` |
| Source-text anchoring | additive | Quote or attach the exact text to operate on. | Prompt refers to text not actually included | `make this shorter` → `Shorten the text below: "…"` |
