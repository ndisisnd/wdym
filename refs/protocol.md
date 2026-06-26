---
name: Protocol
description: Execution protocol for wdym — scan preference, classify, detect, load, select, rewrite, approve, run, record telemetry
type: reference
---

# Protocol

Emit `Step X/8 — <title>` at the start of each step, unconditionally.

## Step 0 — Scan preference `[model: haiku]`

**Always run this first, before anything else.**

The persistent run mode lives in a **pref file** that `--init` installs at one of two scopes. Resolve "the pref file" by checking, in order:

1. **Local:** `$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json` (or `./.claude/wdym/pref.json`).
2. **Global:** `~/.claude/wdym/pref.json`.

Use the first that exists — a local pref overrides a global one. Throughout this protocol, "the pref file" means whichever was resolved; writes (set-mode, flag switches) target that same resolved path.

First, check the raw prompt for the **`--init`** directive (anywhere in the text): if present, run `refs/init.md` end-to-end to bootstrap the skill (it asks the user for local vs. global scope), then **terminate** — do not continue to Step 1, do not enhance any prompt.

Next, check for the **`--status`** directive (alias **`--stats`**, anywhere in the text): if present, run `python3 "<SKILL_DIR>/hooks/telemetry-stats.py"` (the script resolves the active-scope `wdym/telemetry.jsonl` itself), print its output **verbatim inside a fenced code block** so the table alignment and any ANSI styling survive, then **terminate** — do not continue to Step 1, do not enhance any prompt. The script renders a styled report (totals, transform-rate meter, ranked "By Type" table) and prints `No telemetry recorded yet.` when the log is missing or empty. See the **Telemetry** section below for what the two streams contain.

Otherwise, read the resolved pref file and parse its `mode` key into `run_mode` (`comprehensive` · `flash`). This persistent run mode is distinct from the principle-pool `mode` (`global` / `typed:…`) resolved in Step 2.

- If no pref file exists at either scope, or it is unparseable → default `run_mode = comprehensive` (do **not** create it here; it is created only by `--init`, which keeps the install scoped and explicit).

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

This step is the preference scan and does not count toward the `Step X/8` numbering.

## Step 0.5 — Self-check `[model: haiku]`

**Runs once per session, immediately after Step 0, before Step 1.** Cache a session flag `self_check_done`; if it is already set, skip this step entirely (the skill is verified for the session). This keeps the check nearly free — it touches disk only on the first substantive prompt.

The skill **degrades gracefully** when wounded (a dead hook falls back to LLM detection, a missing pref defaults to comprehensive). Self-check adds the missing half: it **senses** those wounds, **repairs** what it safely can, and **escalates** the rest — so the skill recovers instead of running degraded forever and silently.

Load `refs/manifest.json` (the known-good definition). Run the checks below in order. The two governing rules, taken from `manifest.json`:

- **A missing file with a `restore_from` source is recreated** (non-destructive — nothing to lose).
- **A present-but-invalid file that may hold user edits is escalated, never clobbered** — same posture as init's "unparseable settings → report, don't clobber".

Every repair is idempotent. Track outcomes in a local `heal` summary.

**Check 1 — Pref integrity.** Step 0 already resolved and read the pref file.
- Resolved file existed but was **unparseable** (or `mode` not in `comprehensive`/`flash`) → overwrite the resolved path with `{"mode": "comprehensive"}` (the corrupt content held no recoverable preference). Record `pref restored`.
- No pref file at either scope → do nothing (it is created only by `--init`; preserve that invariant). Not a wound.

**Check 2 — Hook health.** Inspect this turn's context for the `<prompt-detect …>` block the hook injects:
- Block present, `verdict` ≠ `degraded` → hook is healthy. Skip to Check 4.
- Block present, `verdict: degraded` → hook ran but its config is broken; go to Check 3 (it will heal `categories.json`).
- **No block present** → the hook did not run. Diagnose by reading the resolved `SETTINGS_PATH` (local `settings.local.json`, else global `settings.json`) for a `hooks.UserPromptSubmit` entry whose command contains `prompt-detect.py`:
  - Entry present **and** its script path exists on disk → wired correctly but produced nothing (e.g. `python3` unavailable, or a passthrough prompt). Record `hook silent` as a warning; do not repair.
  - Entry present **but** the script path does **not** exist → **stale path** (skill dir moved/renamed). Rewrite that command's path to `python3 "<SKILL_DIR>/hooks/prompt-detect.py"` using the running skill's own absolute root, preserving every other key (reuse `refs/init.md` Step I4 merge rules). Record `hook rewired`.
  - No matching entry → hook not installed. **Escalate:** the deterministic scorer is off; emit a one-line hint to run `/wdym --init`. Do not auto-init (scope is the user's choice).
  - `SETTINGS_PATH` unparseable → **escalate**, do not clobber.

**Check 3 — `categories.json` integrity.** Validate against `manifest.json`'s `categories_schema`:
- File **missing** → restore from `refs/categories.default.json` (its `restore_from`). Record `categories restored`.
- File **present but invalid** (unparseable, or missing required keys, or empty `categories`) → **escalate**, do not clobber (it may hold user customisations): emit a one-line hint to restore from `refs/categories.default.json`. Detection continues via the LLM manual path this run.

**Check 4 — Principle files.** Confirm the files in `manifest.json` `required_files` exist:
- `principles-global.md` missing → **escalate** (core dependency; the rewrite quality drops without it).
- A per-type file missing → add its type to a session `missing_types` set (Step 3 falls back to the global base for that type). Record once.

**Check 5 — Telemetry tooling.** The two telemetry writers/readers are install state and are healed like any other code file:
- `hooks/telemetry-stats.py` missing → **escalate** (`/wdym --stats` cannot aggregate without it). `hooks/prompt-detect.py` is already covered by Check 2.
- The data file `telemetry.jsonl` is **excluded from healing** (`manifest.json` `data_files`): it is append-only, best-effort, and created lazily on first write. Its absence is normal (no runs yet) — **never** restore it and **never** escalate. A malformed line is tolerated by the `--stats` reader, not repaired here. Telemetry must never block or alter a run, and the self-check upholds that by leaving the stream alone.

**Output.** If every check passed clean, **emit nothing** — stay invisible and token-free. If anything was repaired or needs escalation, emit one compact line, then continue to Step 1:

```
Self-check: <repaired items>; <warnings/escalations>
```

This step does not count toward the `Step X/8` numbering.

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

Principles live in `refs/principles/`, split by type so each run reads only what it needs:

- `principles-global.md` — global base (additive + subtractive). **Always needed.**
- `principles-code.md` · `principles-question.md` · `principles-text-gen.md` — one file per `prompt_type`.
- `examples.md` — documentation only; **never read at runtime**.

**Session cache — read each file at most once per session.** Maintain a session-scoped `loaded` set of file keys already in context. Before any `Read`, check `loaded`; only read a file whose key is absent, then add the key. This means the global base is read on the **first** substantive prompt of the session and reused thereafter, and each type file is read **lazily** — only the first time that `prompt_type` actually appears.

Assemble `principles_list` for **this** run from the cached parses:

1. **Global base** — if `global` not in `loaded`, read `refs/principles/principles-global.md`, parse the additive and subtractive tables into `(principle, type, description, when_to_apply)` tuples, and mark `global` loaded. Start `principles_list` from the cached global base.
2. **Type section** — only if `mode = typed:<prompt_type>`: if `<prompt_type>` not in `loaded`, read `refs/principles/principles-<prompt_type>.md`, parse its rows (tagged with their `type` column), and mark `<prompt_type>` loaded. Append the cached rows for `<prompt_type>` to `principles_list`.

If `mode = global`, `principles_list` is the global base only — no type file is read.

**Why per-type, not once-globally:** a session's `prompt_type` changes between prompts (a code edit, then a conceptual question). Caching one fixed list would serve the wrong pool after a switch. Caching *per file* keeps every run correct — it rebuilds `principles_list = global base ∪ rows for this run's type` from cache — while still reading each file only once. A code→question→code session reads `global` once, `code` once, `question` once; the second code prompt reads nothing.

## Step 4 — Select top 2–3 principles `[model: sonnet]`

Score each entry in `principles_list` against the prompt:
- **Additive**: does the prompt lack what it adds (specificity, goal, format, role, examples, or the domain-specific gap)?
- **Subtractive**: does the prompt contain the noise it removes (politeness, threats, manipulation, magic phrases, bribes, flattery, hedging, verbosity)?

Rank subtractive matches above additive matches — remove noise before adding structure. When a type section is loaded, a matching type-specific principle outranks a global principle of equal score. **Final tie-break: rows are ordered by impact (highest first) within each table — when two applicable principles are otherwise tied, prefer the one listed earlier.** Row order is only a tie-break; never let it promote a barely-applicable principle over a clearly-applicable one. Select the 2–3 highest-scoring principles. Never select all principles at once. Produce `selected_principles` (ordered list, highest relevance first).

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

## Step 8 — Record telemetry `[model: haiku]`

The **final** action of every substantive run — one that reached the rewrite (Step 5). It fires at **all** exits in **both** modes: after Step 7 submits the enhanced prompt, after a Step 6 `Reject`, and after a Step 7 `Terminate session`. When a flash-mode hint is emitted, log telemetry **after** it. Passthrough exits (Step 1) are **not** logged here — the hook already records those deterministically, so logging them again would double-count.

This is the `skill` half of the hybrid telemetry stream (the hook writes the `src:"hook"` half). Append exactly one line to `<wdym_dir>/telemetry.jsonl`, where `<wdym_dir>` is the directory of the pref file resolved in Step 0 (local `.claude/wdym/`, else global `~/.claude/wdym/`). Use a single Bash append so it is one atomic write with no read-modify-write:

```bash
printf '%s\n' "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"src\":\"skill\",\"type\":\"<prompt_type>\",\"mode\":\"<mode>\",\"run_mode\":\"<run_mode>\",\"outcome\":\"<outcome>\"}" >> "<wdym_dir>/telemetry.jsonl"
```

Fill the placeholders from this run's cached variables:
- `<prompt_type>` — `code` · `question` · `text-gen` · `none` (Step 2)
- `<mode>` — `global` · `typed:<prompt_type>` (Step 2). A `global` row is a **pure global run** — the "exception" metric.
- `<run_mode>` — `comprehensive` · `flash` (Step 0)
- `<outcome>` — `run` (enhanced prompt submitted) · `terminated` (rejected/terminated before running)

The append is **best-effort**: if the directory is missing or the write fails, ignore it and end normally — telemetry must never block or alter a run. Produce no user-facing output beyond the `Step 8/8` marker.

## Telemetry

Two append-only streams share `<wdym_dir>/telemetry.jsonl`, distinguished by `src`:

| `src` | Written by | One line per | Carries |
|-------|------------|--------------|---------|
| `hook` | `hooks/prompt-detect.py` | **every** prompt submission (deterministic) | provisional `verdict`, `type`, `passthrough` flag |
| `skill` | Step 8 above | every **substantive run** the skill transformed | final resolved `type`, `mode`, `run_mode`, `outcome` |

`/wdym --status` (alias `--stats`, Step 0) runs `hooks/telemetry-stats.py`, which renders a styled report aggregating both streams: total prompts seen and passthrough share from the `hook` stream; transformed count, transform-rate meter, per-type breakdown, outcome split, and pure-global-run count from the `skill` stream. It emits ANSI color to a TTY and clean monochrome Unicode when captured. The file is created lazily on first write (never by `--init`); both writers resolve it at the active install scope, local overriding global.
