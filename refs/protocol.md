---
name: Protocol
description: Six-step execution protocol for prompt-engineer — classify, load, select, rewrite, approve, run
type: reference
---

# Protocol

Emit `Step X/6 — <title>` at the start of each step, unconditionally.

## Step 1 — Classify prompt `[model: haiku]`

Read the raw prompt from the `UserPromptSubmit` payload. Check three passthrough conditions in order:
- (a) Prompt starts with `/`
- (b) Word count is ≤5
- (c) Prompt matches a conversational follow-up pattern: starts with or equals "thanks", "thank you", "ok", "got it", "sounds good", "sure", "and", "also", or contains only "can you elaborate", "what about", "go on", "continue"

If any condition matches, pass the prompt through unmodified. Produce no output. Terminate.

## Step 2 — Load principles `[model: haiku]`

Read `refs/principles.md`. Parse both tables — additive principles and subtractive principles — into one list of `(principle, type, description, when_to_apply)` tuples, where `type` is `additive` or `subtractive`. Cache the list for the session. Produce `principles_list`.

## Step 3 — Select top 2–3 principles `[model: sonnet]`

Score each entry in `principles_list` against the prompt:
- **Additive**: does the prompt lack what it adds (specificity, goal, format, role, examples)?
- **Subtractive**: does the prompt contain the noise it removes (politeness, threats, manipulation, magic phrases, bribes, flattery, hedging)?

Rank subtractive matches above additive matches — remove noise before adding structure. Select the 2–3 highest-scoring principles. Never select all principles at once. Produce `selected_principles` (ordered list, highest relevance first).

## Step 4 — Rewrite prompt `[model: sonnet]`

Apply each principle in `selected_principles` to the raw prompt. Each principle's effect must be visible in the rewrite. Do not add filler. Produce:
- `enhanced_prompt` — the rewritten prompt as plain text
- `rationale_table` — one row per principle: `Principle | Why applied`

## Step 5 — Present for approval `[model: haiku]`

Display to the user in this order:
1. `**Original:**` followed by the raw prompt in a blockquote
2. `rationale_table` (markdown table)
3. `**Enhanced:**` followed by `enhanced_prompt` in a blockquote

Call `AskUserQuestion` with options: `Approve`, `Reject`.
On `Reject` → terminate.
On `Approve` → proceed to Step 6.

## Step 6 — Ask to run or terminate `[model: haiku]`

Call `AskUserQuestion` with options: `Run enhanced prompt`, `Terminate session`.
On `Terminate session` → exit.
On `Run enhanced prompt` → submit `enhanced_prompt` as the active prompt. Terminate.
