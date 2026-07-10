---
name: Protocol
description: Execution protocol for wdym — scan preference, classify, detect, load, select, rewrite, approve, run, record telemetry
type: reference
---

# Protocol

Emit no step markers. Visible output is limited to the Step 0.5 repair line (only
when something was healed/escalated) and the Step 6 enhanced-prompt block
(comprehensive mode only — the rewritten prompt, no original, no rationale).

## Step 0 — Resolve run mode

**Command flags first:** if the raw prompt carries a `/wdym` flag — `--init`,
`--help`, `--status` (alias `--stats`), or `--set-mode` — follow
`refs/commands.md` and terminate. Do not continue.

Otherwise resolve `run_mode` (`comprehensive` · `flash`):

1. **From the hook block** — a `run_mode:` line in `<prompt-detect>` is the
   pref already resolved; adopt it. No file read.
2. **Fallback** (no block or no `run_mode:` line) — read the pref file: local
   `$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json`, else `~/.claude/wdym/pref.json`
   (local overrides global; all pref writes target that resolved path). Missing
   or unparseable at both scopes → `comprehensive` (do **not** create the file;
   only `--init` does).

Inline directives override (anywhere in the text): `--flash` /
`--comprehensive` → set `run_mode` accordingly, persist `{"mode": "<target>"}`
to the resolved pref path, strip the flag, emit `Run mode: <target>
(persisted).`, continue. Cache `run_mode` for the session. `comprehensive` runs
the Step 6 gate; `flash` submits immediately at Step 7.

## Step 0.5 — Self-check

Once per session (cache `self_check_done`). The hook performs the file probe on
every prompt:

- Block present, no `selfcheck:` line, verdict ≠ `degraded` → **healthy, skip**
  (the normal path — nothing to read, nothing to emit).
- Block carries `selfcheck: <failures>`, or `verdict: degraded`, or **no block
  on a substantive prompt** → read `refs/heal.md` and follow it (sense → repair
  → escalate), then continue.

## Step 1 — Classify prompt

Block present ⇒ already substantive — skip to Step 2. This is the **no-hook
fallback** only: pass through unmodified (no output, terminate) when the prompt
(a) starts with `/`, (b) is ≤5 words, or (c) is a conversational follow-up
("thanks", "ok", "got it", "sounds good", "sure", "and", "also", "can you
elaborate", "what about", "go on", "continue").

## Step 2 — Detect prompt type

Produce `prompt_type` (`code` · `question` · `text-gen` · `none`) and `mode`
(`global` · `typed:<prompt_type>`). Cache both; emit nothing.

Adopt the hook verdict when present: `clear` → adopt `prompt_type`, `mode =
typed:<prompt_type>`. `global` → `prompt_type = none`, `mode = global`.
`ambiguous` → read `refs/detect.md`, adjudicate only among its `candidates`
(`scores:` is your prior). `degraded` → honour `global_flag: true`; otherwise
read `refs/detect.md` in full. No block, or a bare `--global` token in the text
→ read `refs/detect.md` (`--global` forces `mode = global` and is stripped
before the rewrite). The clear/global path never reads `detect.md` (~95% of
prompts).

## Step 3 — Load principles

`refs/principles/` splits by type: `principles-global.md` (always needed) +
`principles-<type>.md` per prompt_type. **Read each file at most once per
session** (session `loaded` set); rebuild `principles_list` per run from cached
parses:

1. Global base — parse the additive/subtractive tables into `(principle, type,
   when_to_apply, exemplar)` tuples; retain the worked examples as flat
   reference context.
2. Type section — only if `mode = typed:<prompt_type>` and the type is not in
   `missing_types`: parse its rows and append.

`mode = global` → global base only. Rebuilding per run keeps a
code→question→code session correct while reading each file once.

## Step 4 — Select top 2–3 principles

Score each entry against the prompt — **additive**: does the prompt lack what it
adds? **subtractive**: does it contain the noise it removes? Rank subtractive
above additive; a matching type-specific principle outranks a global one of
equal score; final tie-break = table order (impact-first), but never promote a
barely-applicable principle over a clearly-applicable one. Select the 2–3
highest-scoring → `selected_principles`.

## Step 5 — Rewrite prompt

Apply each selected principle; each effect must be visible in the rewrite. Use
row exemplars and worked examples as before→after patterns — adapt, never copy.
No filler. **Anti-fabrication invariant:** never introduce facts, numbers,
names, or constraints the prompt did not supply; surface gaps as placeholders
(`[your framework]`) instead. **Flash corollary:** flash runs immediately with
no gate to fill a placeholder — never emit placeholders; skip the principle or
apply it only as far as the prompt supports. Produce `enhanced_prompt`; the
selected principles and rationale stay internal.

## Step 6 — Present & gate

**Flash:** skip — go to Step 7 with `chosen_prompt = enhanced_prompt`.

**Comprehensive:** display `enhanced_prompt` in a blockquote alone (no label, no
original, no rationale), then call `AskUserQuestion` once:

| Option | `chosen_prompt` | `outcome` |
|--------|-----------------|-----------|
| Run enhanced prompt | `enhanced_prompt` | `run` |
| Run original prompt | `raw_prompt` | `run_original` |
| Edit enhanced prompt | the edited prompt | `edited` |

Cancel via "Other" → `outcome = terminated`; emit the hint below and skip to
Step 8 without running anything.

```
Want to automatically transform your prompts without approval? Set to flash mode instead by running "/wdym --set-mode --flash"
```

## Step 7 — Run

Submit `chosen_prompt` as the active prompt (flash: always `enhanced_prompt`,
immediately). Proceed to Step 8.

## Step 8 — Record telemetry

If the block carries `telemetry: logged`, the hook already wrote this run's
`src:"skill"` line (flash, deterministic outcome) — **skip entirely**.

Otherwise, after every run that reached Step 5 (including a Step 6 cancel),
append one line to `telemetry.jsonl` **in the directory of the Step 0 pref
file** (never the CWD) with a single atomic Bash append:

```bash
printf '%s\n' "{\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"src\":\"skill\",\"type\":\"<prompt_type>\",\"mode\":\"<mode>\",\"run_mode\":\"<run_mode>\",\"outcome\":\"<outcome>\"}" >> "<wdym_dir>/telemetry.jsonl"
```

`outcome` ∈ `run` · `run_original` · `edited` · `terminated`. Best-effort: on
failure, ignore and end normally. Passthrough exits (Step 1) are never logged —
the hook records those. Two `src`-tagged streams share the file (`hook` = one
line per submission; `skill` = one per substantive run); `/wdym --status` runs
`hooks/telemetry-stats.py` to aggregate both.
