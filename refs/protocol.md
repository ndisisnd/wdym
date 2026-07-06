---
name: Protocol
description: Execution protocol for wdym — scan preference, classify, detect, load, select, rewrite, approve, run, record telemetry
type: reference
---

# Protocol

Emit no step markers during normal operation. Visible output is limited to the
Step 0.5 self-check repair line (only when something was healed or escalated) and
the Step 6 enhanced-prompt block (the rewritten prompt only — no original, no
rationale).

## Step 0 — Scan preference

**Always run first.** Resolve "the pref file" by checking, in order:

1. **Local:** `$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json` (or `./.claude/wdym/pref.json`).
2. **Global:** `~/.claude/wdym/pref.json`.

Use the first that exists — local overrides global. All pref writes target that same
resolved path.

**Command flags.** If the raw prompt carries a `/wdym` command flag — `--init`,
`--help`, `--status` (alias `--stats`), or `--set-mode` — **follow `refs/commands.md`**
and terminate. Do not continue to Step 1.

Otherwise, read the resolved pref file and parse `mode` → `run_mode`
(`comprehensive` · `flash`). This is distinct from the principle-pool `mode`
(`global` / `typed:…`) resolved in Step 2. If no pref file exists at either scope, or
it is unparseable → default `run_mode = comprehensive` (do **not** create it here; the
file is created only by `--init`).

Then check for inline mode directives (anywhere in the text):

- **`--flash`** → set `run_mode = flash`, persist `{"mode": "flash"}` to the pref file,
  strip the flag, emit `Run mode: flash (persisted).`, continue.
- **`--comprehensive`** → set `run_mode = comprehensive`, persist `{"mode": "comprehensive"}`,
  strip the flag, emit `Run mode: comprehensive (persisted).`, continue.
- **None** → keep the `run_mode` read from the pref file.

Cache `run_mode` for the session. `comprehensive` runs the Step 6 gate; `flash` skips
it and submits immediately at Step 7. This step does not count toward the `Step X/8`
numbering.

## Step 0.5 — Self-check

**Runs once per session, immediately after Step 0.** Cache a session flag
`self_check_done`; if set, skip entirely. The skill degrades gracefully when wounded
(dead hook → LLM detection, missing pref → comprehensive, missing principle file →
global base); self-check adds the missing half — **sense → repair → escalate** — so
the skill recovers instead of running degraded forever.

Two governing rules: **a missing file with a restore source is recreated**
(non-destructive); **a present-but-invalid file that may hold user edits is escalated,
never clobbered**.

First, probe required files with a single existence check (no need to load
`manifest.json` on the healthy path):

```bash
ls "<SKILL_DIR>"/refs/categories.json \
   "<SKILL_DIR>"/refs/categories.default.json \
   "<SKILL_DIR>"/refs/principles/principles-global.md \
   "<SKILL_DIR>"/hooks/prompt-detect.py \
   "<SKILL_DIR>"/hooks/telemetry-stats.py 2>&1
```

If every file lists cleanly and the checks below pass, **emit nothing**. Read
`refs/manifest.json` **only when a check fails** and you need its repair policy or
schemas. Track outcomes in a local `heal` summary; every repair is idempotent.

**Check 1 — Pref integrity.** Step 0 already read the pref file.
- Existed but **unparseable** (or `mode` not `comprehensive`/`flash`) → overwrite the
  resolved path with `{"mode": "comprehensive"}`. Record `pref restored`.
- No pref at either scope → do nothing (created only by `--init`). Not a wound.

**Check 2 — Hook health.** Inspect this turn's context for the `<prompt-detect …>` block:
- Present, `verdict` ≠ `degraded` → healthy. Skip to Check 4.
- Present, `verdict: degraded` → hook ran but config is broken; go to Check 3.
- **No block** → read the resolved `SETTINGS_PATH` (local `settings.local.json`, else
  global `settings.json`) for a `hooks.UserPromptSubmit` entry whose command contains
  `prompt-detect.py`:
  - Entry present **and** its script path exists → wired but silent (e.g. `python3`
    unavailable, or passthrough). Record `hook silent`; do not repair.
  - Entry present **but** script path missing → **stale path** (skill dir moved).
    Rewrite that command to `python3 "<SKILL_DIR>/hooks/prompt-detect.py"` using the
    running skill's absolute root (reuse `refs/init.md` Step I4 merge rules). Record
    `hook rewired`.
  - No matching entry → not installed. **Escalate:** hint to run `/wdym --init`.
  - `SETTINGS_PATH` unparseable → **escalate**, do not clobber.

**Check 3 — `categories.json` integrity.**
- **Missing** → restore from `refs/categories.default.json`. Record `categories restored`.
- **Present but invalid** (unparseable / missing required keys / empty `categories`) →
  **escalate**, do not clobber; hint to restore from `refs/categories.default.json`.
  Detection continues via the LLM path this run.

**Check 4 — Principle files.**
- `principles-global.md` missing → **escalate** (core dependency).
- A per-type file missing → add its type to a session `missing_types` set (Step 3
  falls back to the global base for that type). Record once.

**Check 5 — Telemetry tooling.**
- `hooks/telemetry-stats.py` missing → **escalate** (`/wdym --stats` can't aggregate).
- The data file `telemetry.jsonl` is **excluded from healing** — append-only,
  best-effort, created lazily. Its absence is normal; never restore, never escalate.

**Output.** All clean → emit nothing. Otherwise one compact line, then continue:

```
Self-check: <repaired items>; <warnings/escalations>
```

This step does not count toward the `Step X/8` numbering.

## Step 1 — Classify prompt

When a `<prompt-detect>` block is present the prompt is already substantive — skip to
Step 2. This step is the **no-hook fallback** (hook disabled or failed). Read the raw
prompt and check three passthrough conditions:
- (a) starts with `/`
- (b) word count ≤5
- (c) conversational follow-up: starts with / equals "thanks", "thank you", "ok",
  "got it", "sounds good", "sure", "and", "also", or is exactly "can you elaborate",
  "what about", "go on", "continue"

If any match, pass through unmodified. Produce no output. Terminate.

## Step 2 — Detect prompt type

Produce `prompt_type` (`code` · `question` · `text-gen` · `none`) and `mode`
(`global` · `typed:<prompt_type>`). Cache both; emit nothing.

**Adopt the hook verdict** from the `<prompt-detect source="hook">` block when present:
- `verdict: clear` → adopt `prompt_type`; set `mode = typed:<prompt_type>`.
- `verdict: global` → `prompt_type = none`, `mode = global`.
- `verdict: ambiguous` → read `refs/detect.md` and adjudicate **only among its
  `candidates`** (its `scores:` line is your prior).
- `verdict: degraded` → honour `global_flag: true` (→ `mode = global`); otherwise read
  `refs/detect.md` and run its full manual protocol.

If **no block** is present, or the prompt carries a bare `--global` token, read
`refs/detect.md` and follow it (it handles `--global` and the manual scoring path).
A bare `--global` anywhere in the text forces `prompt_type = none`, `mode = global`,
and is stripped before the rewrite.

On the clear/global path `refs/detect.md` is **not read** — the deterministic verdict
is sufficient (~95% of prompts).

## Step 3 — Load principles

Principles live in `refs/principles/`, split by type:
- `principles-global.md` — global base (additive + subtractive). **Always needed.**
- `principles-code.md` · `principles-question.md` · `principles-text-gen.md` — one per
  `prompt_type`.

Each file carries a **Worked examples** section below its tables; parse them as flat
reference context for Step 5. (The authoring guide lives in `refs/authoring.md`, not
loaded at runtime.)

**Session cache — read each file at most once.** Maintain a session `loaded` set;
before any `Read`, skip files already in it. Assemble `principles_list` for **this**
run from the cached parses:

1. **Global base** — if `global` not in `loaded`, read `principles-global.md`, parse
   the additive/subtractive tables into `(principle, type, description, when_to_apply,
   exemplar)` tuples, retain the Worked examples, mark `global` loaded. Start
   `principles_list` from it.
2. **Type section** — only if `mode = typed:<prompt_type>` and the type is not in
   `missing_types`: if not in `loaded`, read `principles-<prompt_type>.md`, parse its
   rows (with their `type` column), retain its Worked examples, mark loaded. Append its
   rows to `principles_list`.

If `mode = global`, `principles_list` is the global base only. Rebuilding per run from
cache (not freezing one list) keeps a code→question→code session correct while still
reading each file only once.

## Step 4 — Select top 2–3 principles

Score each entry in `principles_list` against the prompt:
- **Additive**: does the prompt lack what it adds (specificity, goal, format, role,
  examples, or the domain gap)?
- **Subtractive**: does it contain the noise it removes (politeness, threats,
  manipulation, magic phrases, bribes, flattery, hedging, verbosity)?

Rank subtractive above additive. A matching type-specific principle outranks a global
one of equal score. Final tie-break: rows are impact-ordered (highest first) within
each table — prefer the earlier-listed of two otherwise-tied principles, but never
promote a barely-applicable principle over a clearly-applicable one. Select the 2–3
highest-scoring. Produce `selected_principles` (highest relevance first).

## Step 5 — Rewrite prompt

Apply each principle in `selected_principles` to the raw prompt; each effect must be
visible in the rewrite. Use the row **Exemplar** and the **Worked examples** context as
before→after patterns — adapt, never copy verbatim. No filler.

**Anti-fabrication invariant:** never introduce facts, numbers, names, frameworks, or
constraints the prompt did not supply. If a principle needs missing context, surface
the gap as a placeholder (`[your framework]`, `[describe the component]`) rather than
inventing it.

**Flash-mode corollary:** in flash mode the enhanced prompt runs immediately with no
gate to fill a placeholder, so **never emit placeholders** — skip a principle that
needs unsupplied context (pick the next-best), or apply it only as far as the prompt
supports. Placeholders are a comprehensive-mode device.

Produce `enhanced_prompt` (plain text). No rationale is surfaced to the user — the
selected principles and the reasoning behind the rewrite stay internal.

## Step 6 — Present & gate

**Flash mode:** skip entirely — go to Step 7 with `chosen_prompt = enhanced_prompt`.

**Comprehensive mode:** display only the rewritten prompt — `enhanced_prompt` in a
blockquote, with no `**Enhanced:**`/`**Original:**` label, no original prompt, and no
rationale. Never reveal which principles were selected or why.

Call `AskUserQuestion` **once** with three options:

| Option | `chosen_prompt` | `outcome` |
|--------|-----------------|-----------|
| Run enhanced prompt | `enhanced_prompt` | `run` |
| Run original prompt | `raw_prompt` | `run_original` |
| Edit enhanced prompt | the edited prompt | `edited` |

If the user cancels via "Other" → `outcome = terminated`, emit the flash-mode hint
below, and skip to Step 8 without running anything.

**Flash-mode hint** (comprehensive + `terminated` only — never in flash, never when
any prompt ran):

```
Want to automatically transform your prompts without approval? Set to flash mode instead by running "/wdym --set-mode --flash"
```

## Step 7 — Run

Submit `chosen_prompt` as the active prompt (in flash mode always `enhanced_prompt`,
immediately). Then proceed to Step 8.

## Step 8 — Record telemetry

The final action of every substantive run (one that reached Step 5). Fires at all
exits in both modes: after Step 7 submits, and after a Step 6 cancel. When a flash-mode
hint is emitted, log **after** it. Passthrough exits (Step 1) are **not** logged — the
hook records those.

This is the `skill` half of the hybrid stream. Append exactly one line to
`<wdym_dir>/telemetry.jsonl` (the directory of the Step 0 pref file) with a single
atomic Bash append:

```bash
printf '%s\n' "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"src\":\"skill\",\"type\":\"<prompt_type>\",\"mode\":\"<mode>\",\"run_mode\":\"<run_mode>\",\"outcome\":\"<outcome>\"}" >> "<wdym_dir>/telemetry.jsonl"
```

- `<prompt_type>` — `code` · `question` · `text-gen` · `none` (Step 2)
- `<mode>` — `global` · `typed:<prompt_type>` (Step 2); `global` is a **pure global run**
- `<run_mode>` — `comprehensive` · `flash` (Step 0)
- `<outcome>` — `run` · `run_original` · `edited` · `terminated`

Best-effort: if the directory is missing or the write fails, ignore it and end
normally — telemetry must never block or alter a run. Produce no user-facing output.

## Telemetry

Two append-only streams share `<wdym_dir>/telemetry.jsonl`, tagged by `src`:

| `src` | Written by | One line per | Carries |
|-------|------------|--------------|---------|
| `hook` | `hooks/prompt-detect.py` | every prompt submission | provisional `verdict`, `type`, `passthrough` |
| `skill` | Step 8 above | every substantive run | final `type`, `mode`, `run_mode`, `outcome` |

`/wdym --status` (Step 0 → `refs/commands.md`) runs `hooks/telemetry-stats.py`, which
aggregates both streams into a styled report (totals, transform-rate meter, ranked
By-Type table, outcome split). It emits ANSI color to a TTY, monochrome when captured.
The file is created lazily on first write (never by `--init`); both writers resolve it
at the active scope, local overriding global.
