---
name: Protocol
description: Seven-step execution protocol for prompt-engineer — classify, detect, load, select, rewrite, approve, run
type: reference
---

# Protocol

Emit `Step X/7 — <title>` at the start of each step, unconditionally.

## Step 1 — Classify prompt `[model: haiku]`

Read the raw prompt from the `UserPromptSubmit` payload. Check three passthrough conditions in order:
- (a) Prompt starts with `/`
- (b) Word count is ≤5
- (c) Prompt matches a conversational follow-up pattern: starts with or equals "thanks", "thank you", "ok", "got it", "sounds good", "sure", "and", "also", or contains only "can you elaborate", "what about", "go on", "continue"

If any condition matches, pass the prompt through unmodified. Produce no output. Terminate.

## Step 2 — Detect prompt type `[model: haiku]`

Run `refs/detect.md` end-to-end against the raw prompt. It:
- handles the `--global` flag (forces `mode = global`, strips the flag), and otherwise
- scores the type taxonomy and resolves a clear winner or falls back to `none`.

It first checks for a `<prompt-detect source="hook">` block (the deterministic pre-scorer) and adopts its verdict when `clear`/`global`, adjudicating only when `ambiguous`. Produce two variables: `prompt_type` (`code` · `creative-writing` · `image-gen` · `question` · `text-gen` · `none`) and `mode` (`global` · `typed:<prompt_type>`). Emit the `Detected: …` line defined by the protocol. Cache both for the session.

## Step 3 — Load principles `[model: haiku]`

Read `refs/principles.md`. Always parse the **Global base** — additive and subtractive tables — into `(principle, type, description, when_to_apply)` tuples.

- If `mode = global` → `principles_list` is the global base only.
- If `mode = typed:<prompt_type>` → also parse the matching **Type-specific** section for `<prompt_type>` and append its rows (tagged with their `type` column) to `principles_list`.

Load **only** the one matching type section, never all of them. Cache `principles_list` for the session.

## Step 4 — Select top 2–3 principles `[model: sonnet]`

Score each entry in `principles_list` against the prompt:
- **Additive**: does the prompt lack what it adds (specificity, goal, format, role, examples, or the domain-specific gap)?
- **Subtractive**: does the prompt contain the noise it removes (politeness, threats, manipulation, magic phrases, bribes, flattery, hedging, over-direction, conversational image phrasing)?

Rank subtractive matches above additive matches — remove noise before adding structure. When a type section is loaded, a matching type-specific principle outranks a global principle of equal score. Select the 2–3 highest-scoring principles. Never select all principles at once. Produce `selected_principles` (ordered list, highest relevance first).

## Step 5 — Rewrite prompt `[model: sonnet]`

Apply each principle in `selected_principles` to the raw prompt. Each principle's effect must be visible in the rewrite. Do not add filler. Produce:
- `enhanced_prompt` — the rewritten prompt as plain text
- `rationale_table` — one row per principle: `Principle | Why applied`

## Step 6 — Present for approval `[model: haiku]`

Display to the user in this order:
1. `**Original:**` followed by the raw prompt in a blockquote
2. `rationale_table` (markdown table)
3. `**Enhanced:**` followed by `enhanced_prompt` in a blockquote

Call `AskUserQuestion` with options: `Approve`, `Reject`.
On `Reject` → terminate.
On `Approve` → proceed to Step 7.

## Step 7 — Ask to run or terminate `[model: haiku]`

Call `AskUserQuestion` with options: `Run enhanced prompt`, `Terminate session`.
On `Terminate session` → exit.
On `Run enhanced prompt` → submit `enhanced_prompt` as the active prompt. Terminate.
