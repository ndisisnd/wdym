---
name: Prompt Engineering Principles — Language & text generation
description: Type-specific principles loaded on top of the global base when prompt_type = text-gen
type: reference
---

# Language & text generation — `prompt_type = text-gen`

Loaded **on top of** the global base (`refs/principles/principles-global.md`) when `refs/detect.md` resolves `prompt_type = text-gen`. The `type` column marks `additive` / `subtractive` for ranking against the global pool. Rows are **ordered by impact, highest first** — used only as a tie-break between equally-applicable principles (see the global base's selection guide).

| Principle | Type | Description | When to apply | Exemplar |
|-----------|------|-------------|---------------|----------|
| Audience & purpose | additive | State the reader and the goal/CTA the text must achieve. | Purpose or reader unclear | `write a blurb` → `Write a blurb that gets enterprise buyers to book a demo.` |
| Format & length | additive | Name the artifact and size (email, 200-word blurb, 5 bullets). | Output shape or length unstated | `write about our launch` → `Write a 5-bullet internal announcement of our launch.` |
| Source-text anchoring | additive | Quote or attach the exact text to operate on. | Prompt refers to text not actually included | `make this shorter` → `Shorten the text below: "…"` |
| Fidelity constraint | additive | For translate/summarise/rewrite, require meaning preserved and key facts kept. | Task transforms an existing text | `summarize this report` → `Summarize this report; keep every figure and date accurate.` |
| Tone & register | additive | Fix tone and formality for the channel. | Register undefined | `reply to this email` → `Reply in a warm but professional tone.` |

---

## Worked examples

Each worked example combines this file's principles (and the global base) on one prompt; the row **Exemplars** above show each alone. These **are parsed** at runtime: Step 3 keys each block to its principle (by the `###` heading) and attaches it as that principle's `worked_example`, used in Step 5 alongside the row Exemplar. Use them as patterns, not templates.

### Audience & purpose

**Before:** `write a blurb for our product`

**After:** `Write a homepage blurb that gets enterprise IT buyers to book a demo of our observability platform. Lead with the pain it removes, not the feature list.`

**Principles applied:** Audience & purpose (enterprise IT buyers, CTA = book a demo), Specificity (lead with the pain).

---

### Format & length

**Before:** `write about our launch`

**After:** `Write a 5-bullet internal Slack announcement of our v2 launch — what shipped, why it matters, and what teammates should do next.`

**Principles applied:** Format & length (5-bullet Slack post), Audience & purpose (internal teammates, action to take).

---

### Source-text anchoring

**Before:** `make this shorter`

**After:** `Shorten the paragraph below to under 50 words without losing the refund deadline or the contact email: "…"`

**Principles applied:** Source-text anchoring (the paragraph is attached), Fidelity constraint (keep the deadline and email).

---

### Fidelity constraint

**Before:** `summarize this report`

**After:** `Summarize the report below in 6 bullets. Keep every figure, date, and proper name accurate — don't round numbers or paraphrase quoted commitments.`

**Principles applied:** Fidelity constraint (figures, dates, names preserved; no rounding), Format & length (6 bullets).

---

### Tone & register

**Before:** `reply to this customer email`

**After:** `Reply to the customer email below in a warm but professional tone — acknowledge the delay, avoid corporate jargon, and end with a concrete next step: "…"`

**Principles applied:** Tone & register (warm-professional, no jargon), Source-text anchoring (the email is attached).
