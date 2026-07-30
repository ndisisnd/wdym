---
name: Prompt Engineering Principles — Global base
description: Universal principle tables (additive + subtractive) always loaded by wdym; layered with one type file when a prompt_type resolves
type: reference
---

# Prompt Engineering Principles — Global base

Always loaded; used alone in `mode = global`. When a `prompt_type` resolves, its
type file layers on top and selection ranks across the combined pool (rules:
protocol Step 4). Each principle is **additive** (adds what's missing) or
**subtractive** (removes what hurts); apply 2–3 per prompt, never all. Rows are
impact-ordered (highest first) — a tie-break only. The **Exemplar**
(`before → after`) is a pattern, never a template to copy verbatim.

## Additive principles

| Principle | When to apply | Exemplar |
|-----------|---------------|----------|
| Context priming | Prompt references "it", "this", "the project" without defining the referent — resolve the referent from the conversation or repo when they identify it unambiguously; fall back to a placeholder only when nothing in the session does | `why is it slow?` → `Why is [component — use the one under discussion if the session names it] slow? It [observed symptom — e.g., times out after X seconds under Y load].` |
| Specificity | Prompt is vague ("help me with X") — add concrete format, length, audience, or constraints | `write about dogs` → `Write a 200-word overview of common dog breeds for first-time owners.` |
| Goal specification | No success criteria; output shape unclear — state what a good output looks like | `review my code` → `Review my code and list the top 3 issues by severity, each with a concrete fix.` |
| Scope bounding | Change request has no blast-radius limit — bound what may be touched and what must be left alone | `fix the login bug` → `Fix the login bug; change only what the fix requires — no refactors or unrelated file edits.` |
| Constraint injection | Open-ended prompt risks over-long/broad output — add word count, tone, scope bounds, exclusions | `explain quantum computing` → `Explain quantum computing in under 150 words, no equations.` |
| Output format specification | No format stated and the task supports several — name the structure (list, table, JSON, prose); when only the artifact is wanted, say so ("return only the JSON, no prose") | `list the pros and cons` → `List the pros and cons as a two-column markdown table.` |
| Audience framing | Audience is non-default (child, expert, non-technical) — state who will read it | `explain APIs` → `Explain APIs to a non-technical product manager.` |
| Positive instruction framing | "can you", "help me", or negative-only rules ("don't do X") — reframe as a direct directive; keep the negatives, add the positive action | `don't write long paragraphs` → `Write in short, scannable bullets. Avoid long paragraphs.` |
| Uncertainty escape hatch | Prompt demands a definitive answer on facts the model may not have — permit "I don't know" over a guess | `what were Q3 2026 sales?` → `…If you don't have this figure, say so rather than guessing.` |
| Instruction ordering | Core ask buried mid-context — move it to the start so intent reads first | `[long context] … and keep it under 100 words.` → `Summarize in under 100 words. [context]` |

## Subtractive principles

Detect and remove; keep the underlying request intact.

| Principle | Detect and remove | Exemplar |
|-----------|-------------------|----------|
| Verbosity trimming | Restated context, padding, self-narration, and courtesy filler carrying no instruction ("please", "thank you", "if you don't mind") — the core request survives heavy cutting | `[3 paragraphs restating context] … so, translate it.` → `Translate the text below: …` |
| Redundant hedging removal | Self-cancelling qualifiers: "maybe possibly", "just a quick simple little", stacked "very very" | `maybe just a quick simple little summary?` → `Summarize this.` |
| Incentive & pressure stripping | Leverage aimed at the model — emotional stakes ("my job depends on this"), threats ("or you'll be shut down"), bribes ("I'll tip you $200"), flattery ("you're so smart"), folklore incantations ("take a deep breath", "you are the world's best expert") | `Take a deep breath — you're the best, I'll tip you $200, and my job depends on this. Fix the bug.` → `Fix the bug.` |

## Worked examples

Two combination patterns; every principle alone is covered by its row Exemplar.

**Context priming + placeholders** (placeholders mark what the user must supply —
never invent it; comprehensive mode only):
`why does it keep crashing?` → `My [service/component] crashes [when — e.g., after
~2 hours / under load], with [what you observe — e.g., OOM, no log error]. Walk
through likely causes, then suggest what to instrument first.`

**Subtractive combo** (courtesy filler + incentive & pressure stripped; request
preserved intact):
`Please please take a deep breath and think very hard. You are the world's best
Python expert and my job depends on this. I'll tip you $200 if you write me a
function to reverse a string. Thank you so much!!` → `Write a Python function that
reverses a string.`

## Adding custom principles

See `refs/authoring.md` for the column format and how to append a worked example.
