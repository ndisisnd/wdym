---
name: Prompt Detection Protocol
description: Routes a raw prompt into a prompt_type and resolves global vs typed mode for prompt-engineer
type: reference
---

# Prompt Detection Protocol

This protocol runs before principle selection. It inspects the raw prompt, decides
what the prompt is *about*, and stores the result in two variables consumed by the
rest of the flow:

| Variable | Values | Meaning |
|----------|--------|---------|
| `prompt_type` | `code` · `question` · `text-gen` · `none` | The detected domain, or `none` when no type is clear |
| `mode` | `global` · `typed:<prompt_type>` | Which principle pool to load (see protocol Step 3) |

The category taxonomy and all signal cues live in **`refs/categories.json`** — the
single source of truth shared with the deterministic hook scorer. The tables below
mirror it for reading; if they ever disagree, `categories.json` wins.

## Step 0 — Consume the deterministic pre-scorer (preferred)

A `UserPromptSubmit` hook (`hooks/prompt-detect.py`) scores the prompt against
`refs/categories.json` and injects a `<prompt-detect source="hook">` block into
context. **When that block is present, trust it instead of re-scoring:**

- `verdict: clear` → adopt its `prompt_type` and `mode` verbatim. Done.
- `verdict: global` → `prompt_type = none`, `mode = global`. Done.
- `verdict: ambiguous` → the scorer found no clear winner. Adjudicate **only among
  its `candidates`** (or all types if `candidates: none`) using the manual algorithm
  below. The scorer's `scores:` line is your prior.

If no hook block is present (hook disabled or failed), run the full manual protocol
below from scratch. The hook is deterministic and free; the manual path is the
LLM fallback that also reads intent the keyword scorer can miss.

## Flag handling — `--global`

Check the raw prompt for a `--global` token (anywhere in the text).

- **Present** → set `prompt_type = none`, `mode = global`. **Skip detection entirely.**
  Strip the `--global` token from the prompt before it reaches the rewrite step.
- **Absent** → run detection below.

`--global` is the escape hatch: it forces the universal, academically-proven base and
ignores any domain signals. Use it when the user wants generic prompt hygiene only.

## Type taxonomy

| `prompt_type` | Intent | Signal cues (any match scores +1) |
|---------------|--------|-----------------------------------|
| `code` | Produce, modify, or debug software | Fenced code, file paths, extensions (`.py` `.ts` `.rs` `.go`), `function` `class` `bug` `stack trace` `compile` `regex` `api` `refactor` `implement`; language names (Python, Rust, TypeScript…); framework names (React, Django, Next…) |
| `question` | Answer a factual or explanatory question | Leading interrogatives `what` `why` `how` `who` `which`; `explain`, `difference between`, `is it true`, definitional asks — and **no** creation verb present |
| `text-gen` | Transform or generate natural-language text | `summarize` `translate` `rewrite` `paraphrase` `proofread` `draft` `email` `essay` `blog post` `caption` `shorten` `expand` |

## Resolution algorithm

1. For each type, count the number of **distinct** signal cues matched in the raw prompt → `score[type]`.
2. Let `winner` be the highest-scoring type and `runner_up` the second-highest.
3. A type is **clear** when:
   - `score[winner] >= 2`, **and**
   - `score[winner] - score[runner_up] >= 1` (a strict lead, no ties).
4. If clear → `prompt_type = winner`, `mode = typed:<winner>`.
   Otherwise → `prompt_type = none`, `mode = global`.

Ties and weak signals always fall back to `global`. Never guess a type on a single cue.

## Tie-breakers for overlapping signals

- A fenced code block or a concrete file path forces `code`, regardless of other cues.
- A creation verb (`write`, `draft`, `generate`, `compose`) downgrades `question`: an
  interrogative phrasing that also asks to *produce* text is `text-gen`, not `question`.

## Output

Emit one line before handing back to the protocol:

```
Detected: prompt_type=<type> · mode=<mode>
```

Then proceed to protocol Step 3 with `mode` resolved.
