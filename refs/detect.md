---
name: Prompt Detection Protocol
description: Routes a raw prompt into a prompt_type and resolves global vs typed mode for wdym
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
context. The hook **suppresses the block entirely for passthrough prompts**
(slash / ≤5 words / follow-up), so a present block always means a substantive
prompt. **When the block is present, trust it instead of re-scoring:**

- `verdict: clear` → adopt its `prompt_type` and `mode` verbatim. **Skip to Output.**
- `verdict: global` → `prompt_type = none`, `mode = global`. **Skip to Output.**
  The hook emits this both for the `--global` flag and for **zero-signal
  prompts** (all scores 0) — zero signal is itself a deterministic verdict.
- `verdict: ambiguous` → competing signals the scorer cannot separate.
  Adjudicate **only among its `candidates`** (or all types if
  `candidates: none`, emitted by older hook versions) using Step 2 below. The
  scorer's `scores:` line is your prior. **Skip Step 1.**
- `verdict: degraded` → the hook ran but its config (`categories.json`) is unusable,
  so it produced no scores. Honour `global_flag: true` (→ `mode = global`, skip to
  Output); otherwise run the full manual protocol (Steps 1–2) from scratch. The
  self-check (protocol Step 0.5) is responsible for healing the config — detection
  still proceeds normally here.

If no hook block is present (hook disabled or failed), run Steps 1–2 from scratch.
The hook is deterministic and free; the manual path is the LLM fallback that also
reads intent the keyword scorer can miss.

## Step 1 — Check for `--global` flag

Check the raw prompt for a `--global` token (anywhere in the text).

- **Present** → set `prompt_type = none`, `mode = global`. **Skip to Output.**
  Strip the `--global` token from the prompt before it reaches the rewrite step.
- **Absent** → continue to Step 2.

`--global` is the escape hatch: it forces the universal, academically-proven base and
ignores any domain signals. Use it when the user wants generic prompt hygiene only.

## Step 2 — Detect prompt type

### Type taxonomy

| `prompt_type` | Intent | Signal cues (any match scores +1) |
|---------------|--------|-----------------------------------|
| `code` | Produce, modify, or debug software | Fenced code, file paths, extensions (`.py` `.ts` `.rs` `.go`), `function` `class` `bug` `stack trace` `compile` `regex` `api` `refactor` `implement`; language names (Python, Rust, TypeScript…); framework names (React, Django, Next…) |
| `question` | Answer a factual or explanatory question | Leading interrogatives `what` `why` `how` `who` `which`; `explain`, `difference between`, `is it true`, definitional asks — and **no** creation verb present |
| `text-gen` | Transform or generate natural-language text | `summarize` `translate` `rewrite` `paraphrase` `proofread` `draft` `email` `essay` `blog post` `caption` `shorten` `expand` |

### Resolution algorithm

The thresholds live in `refs/categories.json` → `threshold` (`min_score`,
`min_lead`) — the values below are its defaults; if a user has edited the JSON,
the JSON wins (it is the single source of truth for hook and LLM path alike).

1. For each type, count the number of **distinct** signal cues matched in the raw prompt → `score[type]`.
2. Let `winner` be the highest-scoring type and `runner_up` the second-highest.
3. A type is **clear** when either:
   - `score[winner] >= min_score` (default 2) **and** `score[winner] - score[runner_up] >= min_lead` (default 1), **or**
   - `score[winner] >= 1` and every other type scored 0 — a single cue with **zero competitors** is unambiguous.
4. If clear → `prompt_type = winner`, `mode = typed:<winner>`.
   If every type scored 0 → `prompt_type = none`, `mode = global` (zero signal is deterministic).
   Otherwise (competing non-zero scores with no clear winner) → judge the tied leaders on intent; if still genuinely mixed, fall back to `prompt_type = none`, `mode = global`.

On the manual LLM path you may also read intent the keyword cues miss — a prompt that plainly asks for code is `code` even if no listed cue matches. Ties between competing signals fall back to `global` rather than guessing.

### Tie-breakers for overlapping signals

- A fenced code block or a concrete file path forces `code`, regardless of other cues.
- A creation verb (`write`, `draft`, `generate`, `compose`) downgrades `question`: an
  interrogative phrasing that also asks to *produce* text is `text-gen`, not `question`.

## Output

Cache `prompt_type` and `mode` for the session and proceed to protocol Step 3.
Do **not** emit a user-visible line — the happy path stays quiet (see the
protocol preamble: visible output is limited to the self-check repair line and
the Step 6 presentation block).
