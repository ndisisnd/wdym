---
name: Protocol
description: Execution protocol for wdym — scan preference, classify, detect, load, select, rewrite, approve, run, record telemetry
type: reference
---

# Protocol

Emit no step markers. Visible output is limited to the Step 0.5 repair line (only
when something was healed/escalated) and the Step 6 enhanced-prompt block
(comprehensive mode only — the rewritten prompt, no original, no rationale).

## Ask step — present options and stop

wdym asks the user a question in exactly two places: the Step 6 approval gate and
`refs/init.md`'s scope and activation questions. Both use this one step, so the
question reads the same whichever host is running.

**Pick the implementation by tool availability, never by guessing the host.**
Check your own available tools for `AskUserQuestion`:

- **Available** → call it once with the options as given. Unchanged behaviour.
- **Not available** (Codex, and any host without it) → emit the options as plain
  text in the shape below, then **end the turn**. Do not choose an option
  yourself, do not act on any option, and do not continue past the step. Read the
  user's next message as the answer.

Plain-text shape — a one-line question, the options numbered in the order given
with a short consequence each, and one closing line:

```
<question>

1. <Option label> — <what it does>
2. <Option label> — <what it does>
3. <Option label> — <what it does>

Reply with a number or the label.
```

Reading the reply: a number, an option label, or an unambiguous paraphrase of one
selects that option. Anything else — a different instruction, a question back, a
refusal — counts as the "Other" branch that the calling step defines (Step 6
treats it as cancel). Never guess between two options; if the reply genuinely
fits neither, ask once more with the same shape.

## Step 0 — Resolve run mode

**Command flags first:** if the raw prompt carries a `/wdym` flag — `--init`,
`--help`, `--status` (alias `--stats`), or `--set-mode` — follow
`refs/commands.md` and terminate. Do not continue.

Otherwise resolve `run_mode` (`comprehensive` · `flash`):

1. **From the hook block** — a `run_mode:` line in `<prompt-detect>` is the
   pref already resolved; adopt it. No file read.
2. **Fallback** (no block or no `run_mode:` line) — read the first
   `wdym/pref.json` that exists, in the same order the hook uses (nearest scope
   wins; all pref writes target that resolved path):

   1. `$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json` — when the host sets that
      variable (Claude Code does; Codex does not).
   2. `.claude/wdym/pref.json` in the current directory, then in each parent up
      to the repo root — this is what finds a repo-local install when the
      session started in a subdirectory.
   3. `~/.claude/wdym/pref.json` — the canonical global install on either host.
   4. `$CODEX_HOME/wdym/pref.json` — only when `CODEX_HOME` is set.

   Missing or unparseable at every scope → `comprehensive` (do **not** create the
   file; only `--init` does).

The same pref carries `activation` (`hook` · `on-demand`) — *when* the skill
fires, as opposed to `mode`'s *how it behaves once it does*. It needs no
resolution on this path: reaching the protocol at all means the skill is already
running. It matters only to Step 0.5, which reads it to tell an expected silence
apart from a broken hook. Absent key → `on-demand`. Change it with
`/wdym --init`, never by editing the pref alone — the hook wiring has to move
with it.

Inline directives override (anywhere in the text): `--flash` /
`--comprehensive` → set `run_mode` accordingly, persist it to the resolved pref
path by **updating the `mode` key in place** (read, set one key, write back —
never rewrite the file as `{"mode": "<target>"}`, which would drop `activation`
and silently revert the user to on-demand), strip the flag, emit `Run mode:
<target> (persisted).`, continue. Cache `run_mode` for the session. `comprehensive` runs
the Step 6 gate; `flash` submits immediately at Step 7.

## Step 0.5 — Self-check

Once per session (cache `self_check_done`). Under `activation: hook` the hook
performs the file probe on every prompt; under `on-demand` nothing probes, so
there is nothing to diagnose.

- Block present, no `selfcheck:` line, verdict ≠ `degraded` → **healthy, skip**
  (the normal path — nothing to read, nothing to emit).
- **No block** → read `activation` (Step 0): `on-demand` → **healthy, skip**;
  block absence is the expected state, not a wound. `hook` on a substantive
  prompt → the hook should have spoken and did not; read `refs/heal.md`.
- Block carries `selfcheck: <failures>` or `verdict: degraded` → read
  `refs/heal.md` and follow it (sense → repair → escalate), then continue.

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
original, no rationale), then run the **ask step** (above) once with the question
"Run this prompt?" and these options:

| Option | `chosen_prompt` | `outcome` |
|--------|-----------------|-----------|
| Run enhanced prompt | `enhanced_prompt` | `run` |
| Run original prompt | `raw_prompt` | `run_original` |
| Edit enhanced prompt | the edited prompt | `edited` |

On the text-fallback path the whole turn is the blockquote followed by the
question block — nothing else, and nothing runs until the user replies.

Cancel — "Other" on the tool path, any reply matching no option on the text path
— → `outcome = terminated`; emit the hint below and skip to Step 8 without
running anything. A reply that supplies replacement wording is *Edit enhanced
prompt*, not a cancel.

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
