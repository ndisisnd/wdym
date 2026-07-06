---
name: Prompt Detection Protocol
description: Manual (LLM) type-detection path for wdym — read only when the hook verdict is ambiguous, degraded, or absent
type: reference
---

# Prompt Detection Protocol

This is the **manual fallback**. Protocol Step 2 adopts the hook's `<prompt-detect>`
verdict directly on the common `clear`/`global` path and reads this file **only** when
the verdict is `ambiguous`/`degraded` or no block is present. It resolves two variables:

| Variable | Values | Meaning |
|----------|--------|---------|
| `prompt_type` | `code` · `question` · `text-gen` · `none` | Detected domain, or `none` |
| `mode` | `global` · `typed:<prompt_type>` | Which principle pool to load (Step 3) |

The taxonomy and all signal cues are the single source of truth in
**`refs/categories.json`** (shared with the hook scorer). Do not restate them here — read
that file if you need the exact cue lists; the algorithm below operates on its
`categories` and `threshold`.

## Step 1 — `--global` flag

Check the raw prompt for a `--global` token (anywhere).
- **Present** → `prompt_type = none`, `mode = global`; strip the token before the
  rewrite. **Skip to Output.**
- **Absent** → continue.

`--global` forces the universal base and ignores domain signals — generic prompt
hygiene only.

## Step 2 — Detect prompt type

Score the prompt against every category in `refs/categories.json`. Intent summary:
- `code` — produce, modify, or debug software.
- `question` — answer a factual/explanatory question (interrogative, **no** creation verb).
- `text-gen` — transform or generate natural-language text (summarize, translate, draft…).

### Resolution algorithm

Thresholds come from `categories.json` → `threshold` (`min_score`, `min_lead`;
defaults 2 and 1). If the JSON was edited, the JSON wins.

1. For each type, count **distinct** signal cues matched → `score[type]`.
2. `winner` = highest-scoring type, `runner_up` = second.
3. A type is **clear** when either:
   - `score[winner] ≥ min_score` **and** `score[winner] − score[runner_up] ≥ min_lead`, or
   - `score[winner] ≥ 1` and every other type scored 0 (single cue, zero competitors).
4. Clear → `prompt_type = winner`, `mode = typed:<winner>`.
   All types 0 → `prompt_type = none`, `mode = global`.
   Otherwise (competing non-zero scores) → judge the tied leaders on intent; if still
   genuinely mixed, fall back to `prompt_type = none`, `mode = global`.

On this manual path you may also read intent the keyword cues miss — a prompt that
plainly asks for code is `code` even if no listed cue matches.

### Tie-breakers

- A fenced code block or a concrete file path forces `code`.
- A creation verb (`write`, `draft`, `generate`, `compose`) downgrades `question`: an
  interrogative that also asks to *produce* text is `text-gen`.

## Output

Cache `prompt_type` and `mode`; proceed to protocol Step 3. Emit no user-visible line.
