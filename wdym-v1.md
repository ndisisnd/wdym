# wdym v1 — Token-Efficiency Implementation Plan

Goal: cut the skill's runtime token footprint ~75% (≈55k → ≈14k per 10-prompt session)
with zero behavior change. Ordered by savings; each step is independently shippable
unless a dependency is noted. All edits happen in this repo; **Step 9 (reinstall) is
required before any change takes effect**, because the live copy is `~/.claude/skills/wdym`.

Baseline sizes (chars ≈ tokens×4): SKILL.md 16,444 · protocol.md 22,555 ·
detect.md 5,746 · principles-global.md 12,569 · manifest.json 3,491 · description ~1,600.

---

## Step 1 — Rewrite SKILL.md body as a thin dispatcher

**Saves ~3,300 tokens × every substantive prompt** (body is re-injected on each Skill invocation).

1. Keep, verbatim or lightly trimmed:
   - `## Usage` — trigger line only (hook fires on UserPromptSubmit; block-present ⇒ invoke).
   - Run-mode table (comprehensive gate vs flash immediate) + pref resolution order
     (local `.claude/wdym/pref.json` → global `~/.claude/wdym/pref.json`).
   - One-line flag list: `--global`, `--flash`, `--comprehensive`, `--set-mode`,
     `--init`, `--status/--stats`, `--help` — one line each, no sub-explanations.
   - The dispatch line: "Follow `refs/protocol.md` end-to-end. Command flags
     (`--init/--help/--status/--set-mode`) → `refs/commands.md` instead" (dep: Step 5).
   - Output discipline line: no step markers; visible output = self-check repair line +
     Step 6 block (comprehensive only).
2. Delete entirely (rationale moves to ARCHITECTURE.md where not already there):
   - `## Modes` table (protocol Step 2 owns it), `## Install (--init)` prose
     (refs/init.md owns it), `## Inputs` / `## Outputs` tables (restate the protocol),
     `## Caching` (keep only one sentence in the dispatch section: "Read each ref file
     at most once per session; rebuild `principles_list` per run from cached parses"),
     `## Self-healing` (protocol Step 0.5 owns it), `## Telemetry` including the
     25-line sample report (protocol §Telemetry owns it), `## References` long
     descriptions → one line per path, ≤8 words each.
3. Target size: ≤3,500 chars (~850 tokens). Verify with `wc -c SKILL.md`.

## Step 2 — Cut the frontmatter `description` to 3 sentences

**Saves ~320 tokens in every session's system prompt, every project.**

Replace the current 24-line description with:

```yaml
description: >
  Prompt rewriter that fires automatically on UserPromptSubmit via a hook-injected
  <prompt-detect> block; skips slash commands, ≤5-word prompts, and follow-ups.
  Detects prompt type (code, question, text-gen) and rewrites using 2–3 matched
  principles; comprehensive mode gates the rewrite for approval, flash mode runs it
  immediately. Manage with /wdym --init, --status, --set-mode, --help.
```

Keep `allowed-tools` unchanged.

## Step 3 — Read `detect.md` only on `ambiguous`/no-block

**Saves ~1,400 tokens/session (~95% of sessions never read it).**

1. In `refs/protocol.md` Step 2, replace "Run `refs/detect.md` end-to-end" with the
   inline adoption rule:
   - Block present, `verdict: clear` → adopt `prompt_type`/`mode` verbatim.
   - Block present, `verdict: global` → `prompt_type = none`, `mode = global`.
   - Block present, `verdict: ambiguous` or `degraded`, **or no block** → read
     `refs/detect.md` and follow it (it retains the full manual path + `--global` handling).
   - `--global` token in the prompt → force `mode = global`, strip it (keep this inline
     too, so the flag works without reading detect.md).
2. `refs/detect.md`: delete its Step 0 hook-consumption section (now inlined) and the
   taxonomy mirror table — point to `refs/categories.json` as the cue source instead
   (it already declares categories.json wins on disagreement). Keep the resolution
   algorithm and tie-breakers. Target ≤3,000 chars.

## Step 4 — Self-check without loading `manifest.json`

**Saves ~900 tokens/session on the healthy path.**

1. In `refs/protocol.md` Step 0.5, inline the required-file list and replace the
   manifest Read with one Bash existence probe, e.g.:
   `ls <SKILL_DIR>/refs/categories.json <SKILL_DIR>/refs/principles/principles-global.md … 2>&1`
   (one command, non-zero/missing lines identify the wound).
2. Read `refs/manifest.json` **only when a check fails** and the repair policy/schema
   is needed. State this explicitly in Step 0.5.
3. Keep both repair invariants (restore-when-missing, escalate-when-invalid) as two
   sentences in Step 0.5; they no longer need to be quoted from the manifest up front.
4. Update `manifest.json`'s `required_files` for files added/removed in Steps 5–7.

## Step 5 — Split command paths out of `protocol.md`

**Saves ~3,000 tokens/session on the happy path.** (Dep: Step 1's dispatch line.)

1. Create `refs/commands.md`: move the full `--init` dispatch, `--help`, `--status/--stats`,
   and `--set-mode` handling out of protocol.md Step 0. Order: self-check first, then
   command, then terminate (unchanged semantics).
2. Create `refs/help.txt`: move the 35-line help block verbatim. `--help` becomes
   `cat <SKILL_DIR>/refs/help.txt` printed in a fenced block — the text never rides
   in context as protocol content.
3. `protocol.md` Step 0 shrinks to: resolve pref → if any `/wdym` command flag →
   follow `refs/commands.md`; else apply inline `--flash`/`--comprehensive` switches
   and continue.
4. Delete protocol.md's trailing `## Telemetry` section duplication: keep the two-stream
   table once (in protocol.md §Step 8 or §Telemetry — pick one location), and ensure
   SKILL.md (Step 1) no longer carries a copy.
5. Move explanatory asides to ARCHITECTURE.md: "Why per-type, not once-globally"
   (Step 3), the degradation-philosophy paragraph (Step 0.5 preamble).
6. Target: protocol.md ≤11,000 chars; commands.md ≈5,000; help.txt ≈1,400.

## Step 6 — Compact the hook block; skip redundant telemetry

**Saves ~240 tokens × every substantive prompt.**

1. `hooks/prompt-detect.py`: emit a minimal block —
   - Always: `verdict`, `prompt_type` (when clear), and the ACTION line.
   - Only on `ambiguous`: `scores:` and `candidates:` lines.
   - Only when true: `global_flag`. Drop `mode` (derivable) and `forced` (internal).
   - Keep the `degraded` self-report unchanged.
2. Update the block-format references in `refs/detect.md` and protocol.md Step 0.5
   Check 2 (they only key on block presence + `verdict`, so wording tweaks only).
3. Protocol Step 8: add the skip rule — **flash mode + hook verdict `clear`/`global`
   + outcome `run` → do not write a skill line** (the hook line already carries type;
   outcome is deterministic). Log skill lines only for: ambiguous adjudications,
   comprehensive-mode runs, and any outcome ≠ `run`.
4. `hooks/telemetry-stats.py`: count flash-clear transforms from the `hook` stream
   (substantive hook lines with no paired skill line in a flash context) so
   `Transformed` and `By Type` stay accurate. Guard against double-counting where a
   skill line does exist (pre-change logs).
5. `tests/detect_bench.py`: update expected block fixtures if it asserts on the full
   block text; re-run to confirm the 95% deterministic rate still holds.

## Step 7 — Slim `principles-global.md`

**Saves ~800 tokens/session.**

1. Move `## Adding custom principles` (authoring guide) to ARCHITECTURE.md (or a new
   `refs/authoring.md`, never loaded at runtime). Add a one-line pointer in each
   principles file footer.
2. Trim `## Selection guide` to the two rules protocol Step 4 doesn't already state
   (subtractive-over-additive and type-over-global are duplicated — keep them in
   protocol.md only; keep the row-order-as-tie-break note here since it describes the
   tables themselves).
3. Keep all principle rows, exemplars, and worked examples untouched.

## Step 8 — Doc trims (no runtime effect)

1. `CLAUDE.md` (repo): reduce to one line — "`<prompt-detect>` block present ⇒ invoke
   the wdym skill first; no block ⇒ respond normally."
2. `README.md`: apply the earlier audit — merge Initialising into Installation (drop
   the duplicate `--init` block), point step 5 of "How it works" at the Modes table,
   merge the two mode-flag rows, collapse "Installing elsewhere" to a comment line,
   move step-level detail (passthrough examples, bench aside) to ARCHITECTURE.md.
3. `ARCHITECTURE.md`: absorb the moved rationale from Steps 1, 5, 7 (dedupe against
   what it already covers).

## Step 9 — Sync, verify, ship

1. `manifest.json`: add `refs/commands.md`, `refs/help.txt` (and `refs/authoring.md`
   if created) to `required_files` with restore policy; bump any version field.
2. Re-run `python3 tests/detect_bench.py` — must pass at the same deterministic rate.
3. Token audit: `wc -c SKILL.md refs/*.md` — confirm targets (SKILL.md ≤3.5k chars,
   protocol.md ≤11k, detect.md ≤3k chars).
4. Reinstall: `./install.sh` (updates `~/.claude/skills/wdym`). Confirm `install.sh`
   copies `refs/commands.md`/`refs/help.txt` (it copies whole dirs — verify, don't assume).
5. Smoke test in a fresh session: one substantive prompt (flash path, no gate, no
   step markers), `/wdym --help` (verbatim help), `/wdym --status` (report renders),
   one `ambiguous`-shaped prompt (detect.md gets read, skill line logged).

## Expected result

| Surface | Before | After |
|---|---|---|
| Frontmatter description (every session) | ~400 tok | ~80 tok |
| SKILL.md injection (× N prompts) | ~4,100 tok | ~850 tok |
| Hook block (× N prompts) | ~65 tok | ~25 tok |
| Refs read per session (happy path) | ~11,500 tok | ~6,000 tok |
| Telemetry Bash (× N prompts, flash-clear) | ~200 tok | 0 |
