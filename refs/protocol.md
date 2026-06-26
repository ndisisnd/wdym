---
name: Protocol
description: Execution protocol for prompt-engineer — scan preference, classify, detect, load, select, rewrite, approve, run
type: reference
---

# Protocol

Emit `Step X/7 — <title>` at the start of each step, unconditionally.

## Step 0 — Scan preference `[model: haiku]`

**Always run this first, before anything else.**

The persistent run mode lives in the **project-local pref file**: `$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json` (created by `--init`, see below). This is local to the directory the user is working in — never read or write a global `~/.claude` copy. Throughout this protocol, "the pref file" means this project-local path.

First, check the raw prompt for the **`--init`** directive (anywhere in the text): if present, run `refs/init.md` end-to-end to bootstrap the skill into the current directory, then **terminate** — do not continue to Step 1, do not enhance any prompt.

Otherwise, read the pref file and parse its `mode` key into `run_mode` (`comprehensive` · `flash`). This persistent run mode is distinct from the principle-pool `mode` (`global` / `typed:…`) resolved in Step 2.

- If the pref file is missing or unparseable → default `run_mode = comprehensive` (do **not** create it here; it is created only by `--init`, which keeps the install scoped and explicit).

Then check the raw prompt for mode directives (anywhere in the text):

- **`--set-mode` present** → this is an explicit mode-management command (e.g. `/wdym --set-mode --flash`). Read the target from the accompanying `--flash` or `--comprehensive` token, write `{"mode": "<target>"}` to the pref file, emit `Run mode set to <target>.`, and **terminate immediately** — do not continue to Step 1, do not enhance any prompt. If neither `--flash` nor `--comprehensive` accompanies `--set-mode`, emit the current `run_mode` and ask the user which mode to set, then terminate.
- **`--flash` present (without `--set-mode`)** → set `run_mode = flash`, **persist** it by writing `{"mode": "flash"}` to the pref file, strip the flag, and continue.
- **`--comprehensive` present (without `--set-mode`)** → set `run_mode = comprehensive`, **persist** it by writing `{"mode": "comprehensive"}` to the pref file, strip the flag, and continue.
- **None present** → keep the `run_mode` read from the pref file.

A switch directive changes the stored preference permanently — every subsequent run uses it until switched again. Cache `run_mode` for the session. Emit `Run mode: <run_mode>` then continue to Step 1.

| `run_mode` | Behaviour |
|------------|-----------|
| `comprehensive` (default) | Runs Steps 6 and 7: presents the enhanced prompt for approval, then asks whether to run it. |
| `flash` | Skips the approval gate (Step 6) and the run/terminate gate (Step 7): rewrites and immediately submits the enhanced prompt. |

This step is the preference scan and does not count toward the `Step X/7` numbering.

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

It first checks for a `<prompt-detect source="hook">` block (the deterministic pre-scorer) and adopts its verdict when `clear`/`global`, adjudicating only when `ambiguous`. Produce two variables: `prompt_type` (`code` · `question` · `text-gen` · `none`) and `mode` (`global` · `typed:<prompt_type>`). Emit the `Detected: …` line defined by the protocol. Cache both for the session.

## Step 3 — Load principles `[model: haiku]`

Read `refs/principles.md`. Always parse the **Global base** — additive and subtractive tables — into `(principle, type, description, when_to_apply)` tuples.

- If `mode = global` → `principles_list` is the global base only.
- If `mode = typed:<prompt_type>` → also parse the matching **Type-specific** section for `<prompt_type>` and append its rows (tagged with their `type` column) to `principles_list`.

Load **only** the one matching type section, never all of them. Cache `principles_list` for the session.

## Step 4 — Select top 2–3 principles `[model: sonnet]`

Score each entry in `principles_list` against the prompt:
- **Additive**: does the prompt lack what it adds (specificity, goal, format, role, examples, or the domain-specific gap)?
- **Subtractive**: does the prompt contain the noise it removes (politeness, threats, manipulation, magic phrases, bribes, flattery, hedging, verbosity)?

Rank subtractive matches above additive matches — remove noise before adding structure. When a type section is loaded, a matching type-specific principle outranks a global principle of equal score. Select the 2–3 highest-scoring principles. Never select all principles at once. Produce `selected_principles` (ordered list, highest relevance first).

## Step 5 — Rewrite prompt `[model: sonnet]`

Apply each principle in `selected_principles` to the raw prompt. Each principle's effect must be visible in the rewrite. Do not add filler. Produce:
- `enhanced_prompt` — the rewritten prompt as plain text
- `rationale_table` — one row per principle: `Principle | Why applied`

## Step 6 — Present for approval `[model: haiku]`

**Flash mode (`run_mode = flash`):** skip this step entirely — produce no approval gate — and go straight to Step 7.

**Comprehensive mode (`run_mode = comprehensive`):** display to the user in this order:
1. `**Original:**` followed by the raw prompt in a blockquote
2. `rationale_table` (markdown table)
3. `**Enhanced:**` followed by `enhanced_prompt` in a blockquote

Call `AskUserQuestion` with options: `Approve`, `Reject`.
On `Reject` → emit the **flash-mode hint** (see Step 7), then terminate.
On `Approve` → proceed to Step 7.

## Step 7 — Run `[model: haiku]`

**Flash mode (`run_mode = flash`):** submit `enhanced_prompt` as the active prompt immediately — no `AskUserQuestion`. Terminate.

**Comprehensive mode (`run_mode = comprehensive`):** call `AskUserQuestion` with options: `Run enhanced prompt`, `Terminate session`.
On `Terminate session` → emit the flash-mode hint (below), then exit.
On `Run enhanced prompt` → submit `enhanced_prompt` as the active prompt. Terminate.

### Flash-mode hint (comprehensive mode only)

Whenever a `comprehensive`-mode session ends in **terminate** (a `Reject` at Step 6 or a `Terminate session` at Step 7), emit this line to the terminal before exiting, verbatim:

```
Want to automatically transform your prompts without approval? Set to flash mode instead by running "/wdym --set-mode --flash"
```

Emit it only on terminate, only in comprehensive mode — never in flash mode, and never when the user chose to run the enhanced prompt.
