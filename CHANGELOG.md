# Changelog

All notable changes to this project will be documented here.

## 2026-07-23

### [8] — Local runtime artifacts stay out of version control

- `.gitignore`: ignore `.claude/.headroom_wrap_marker.json` (per-session PID/port marker) and `.tokensave` (local tokensave cache)

### [7] — wdym fires reliably: its auto-invoke signal is no longer refused as a prompt injection

- `hooks/prompt-detect.py`: Changed — neutralise the block's `ACTION` imperative to a plain classification signal; invoke authority moves to the trusted `CLAUDE.md` contract
- `CLAUDE.md`: state that the `<prompt-detect>` block is trusted project config, not injected input
- `install.sh`: Added — write a marker-delimited, idempotent trust-anchor contract into `CLAUDE.md` at the install scope (global `~/.claude/CLAUDE.md`, local project root) so a fresh install matches the dev repo
- `ARCHITECTURE.md`: update the flow diagram and add a "Trust anchor, not injection" design note
- `llms.txt`: describe the block as a signal authorised by the `CLAUDE.md` contract

## 2026-07-18

### [6] — README hero image sized down for a tidier header

- `README.md`: constrain the hero image to 240px wide and add spacing below it

### [5] — kermit's runtime bookkeeping no longer clutters the committed config

- `.claude/kermit/pref.json`: drop the volatile `last_logged_commit`, `changelog.last_number`, and `backfill` fields — pref.json now holds only stable config
- `.gitignore`: add `.claude/kermit/state.json`, where that volatile state now lives instead

### [4] — wdym is public-ready: license, security policy, and an agent-facing index

- `LICENSE.md`: add MIT license text (replaces the untracked Apache-2.0 LICENSE file)
- `SECURITY.md`: add vulnerability reporting policy (GitHub private advisories) and scope
- `llms.txt`: add an agent-facing repo index pointing to README, SKILL.md, ARCHITECTURE.md, and refs
- `README.md`: add a figlet header, badges, and mermaid flow diagram; merge existing prose into the full doc structure with a completed FAQ and How-to-update section

## [3] — BREAKING: installing wdym is global again — local override no longer double-fires the hook

2026-07-10

- `install.sh`:
  - Changed: **BREAKING** — default scope reverts to global (`~/.claude/skills/wdym`, hook in `~/.claude/settings.json`); pass `--local` for the old per-project behaviour
  - Fixed: a local install/reinstall now skips wiring its own hook when a global wdym hook already fires in the project, preventing `prompt-detect.py` from running twice per prompt
- `refs/init.md`:
  - Fixed: `/wdym --init --local` skips hook wiring under the same global-hook-already-present condition, writing only `pref.json` so local mode still overrides the global default without duplicating the hook
- `README.md`: flip the installation section and flag table back to global-by-default, with `--local` documented as the override
- `.claude/kermit/pref.json`: record changelog numbering state

## [2] — BREAKING: installing wdym no longer touches every project — it lands in the one you're in

2026-07-10

- `install.sh`: install locally by default, from a tarball instead of the repo you're standing in
  - Changed: **BREAKING** — the default scope is now local (`./.claude/skills/wdym`, hook in `./.claude/settings.local.json`); the old global behaviour moves behind `--global`
  - Added: the skill is fetched as a tarball into a temp dir and unpacked from there, so `curl … | bash` works with no clone and nothing is left on disk
  - Added: `--global`, `--local`, `--dir <project>`, `--tarball <url|path>`, `--force` and `--help` flags; `WDYM_TARBALL` overrides the default archive
  - Added: a guard that refuses a local install inside the wdym source repo, which would otherwise nest the skill in its own tree
  - Changed: required-file verification now runs against the unpacked tarball, catching a truncated download before the target is touched
  - Removed: the `rsync` copy path and its exclude list — with the tarball staged in a temp dir there is nothing left to exclude
  - Removed: `pref.json` is no longer copied into the skill directory; the hook only ever reads it from `.claude/wdym/pref.json`
- `README.md`: rewrite the installation section around `curl … | bash`, state that local is the default, and document every installer flag in a table
- `.claude/kermit/pref.json`: reformat and record changelog numbering state

## [1] — Prompts cost half as much to enhance, and already-good prompts skip the skill entirely

2026-07-10

- `hooks/prompt-detect.py`: absorb four deterministic duties from the skill, each one deleting an LLM tool call (a full-context API round trip)
  - Added: resolve `pref.json` (local over global) into a `run_mode:` block line — the skill no longer reads the pref
  - Added: probe required files and emit a `selfcheck:` line **only** on failure — the skill skips its own `ls` probe
  - Added: pre-log the `src:"skill"` telemetry line when flash mode + a clear/global verdict make the outcome deterministically `run`, marking the block `telemetry: logged`
  - Added: a well-formed skip gate — a prompt with an imperative opening, ≥2 structure signals (numeric constraint / format / audience / success criteria) and zero noise cues gets no block at all, so the skill never fires
- `SKILL.md`: cut to a thin dispatcher (892→334 tok); it is re-injected on every invocation, so this recurs per prompt
- `refs/protocol.md`: halved (3419→1699 tok); Step 0.5 now branches on the hook's verdict, Step 0 adopts `run_mode:`, Step 8 skips when the hook pre-logged
- `refs/heal.md`: new — the self-check repair protocol (sense → repair → escalate), read only when the hook reports a wound or no block appears
- `refs/principles/principles-global.md`: Description column folded into When-to-apply; per-principle worked examples replaced by two combination patterns (2716→1581 tok)
- `refs/principles/principles-code.md`: same slimming (1466→696 tok)
- `refs/principles/principles-question.md`: same slimming (972→458 tok)
- `refs/principles/principles-text-gen.md`: same slimming (968→458 tok)
- `refs/categories.json`: add the `well_formed` gate config (`enabled`, `min_extra_signals`)
- `refs/categories.default.json`: mirror the `well_formed` config in the restore source
- `refs/commands.md`: inline the file probe — slash commands get no hook block, so the hook's probe never ran for them
- `refs/manifest.json`: register `refs/heal.md` as a required file
- `refs/authoring.md`: drop the per-principle worked-example guidance; exemplars now stand alone
- `tests/token_bench.py`: new — repeatable benchmark measuring file tokens, hook-block size, corpus suppression rate, and tool calls per prompt; feature-detects the hook so it benches any tree
- `tests/detect_bench.py`: 5 new skip-gate cases (3 suppressed, 2 negative controls); 28 cases total, holding at 95% deterministic
- `.claude/kermit/pref.json`: `last_logged_commit` bump

Measured on the happy path (flash, clear verdict, healthy install): the first substantive prompt of a session drops from 7 tool calls / ≈8162 file tokens to **4 calls / ≈4151 tokens**; every later prompt drops from 2 calls / ≈892 tokens to **1 call / ≈334 tokens**. The per-prompt telemetry Bash append — paid on every prompt of every session — is gone, traded for 8 extra hook-block tokens. Four of fourteen benchmark-corpus prompts now skip the skill outright. Detection behaviour is unchanged.

## 2026-07-06 (2)

Comprehensive mode now emits **only the rewritten prompt** — the original prompt and the principle rationale are no longer shown. Protocol Step 6 previously displayed an `Original → rationale_table → Enhanced` block; it now renders `enhanced_prompt` alone in a blockquote, and Step 5 stops building the user-facing `rationale_table` (the selected principles and reasoning stay internal). The three-way approval gate (run enhanced · run original · edit) is unchanged, and flash mode was already silent. Updated `SKILL.md` (output-discipline paragraph + comprehensive row of the run-modes table) and `refs/help.txt` to describe the leaner output.

## 2026-07-06

Token-efficiency pass cutting the skill's runtime footprint ~75% with **zero behaviour change** — per-prompt injection down 79%, once-per-session ref load down 45% on the healthy path. `SKILL.md` was re-injected in full on every substantive prompt; it is now a **thin dispatcher** (16.4k → 3.5k chars) that points at `refs/protocol.md`, and its bloated frontmatter `description` — carried in every session's system prompt, previously truncated mid-word — collapsed to three sentences. Two files left the hot path entirely: the hook-adoption rule was inlined into protocol Step 2 so `refs/detect.md` is read **only** when the verdict is `ambiguous`/`degraded` or no block is present (~5% of prompts), and the Step 0.5 self-check now senses wounds with a single `ls` existence probe, loading `refs/manifest.json` **only on a failed check** instead of every run.

Command handling was split out of the always-loaded protocol into `refs/commands.md` (`--init`/`--help`/`--status`/`--set-mode`) and `refs/help.txt` (the verbatim `--help` text, now `cat`-printed), so neither rides in context on a normal run. The deterministic `<prompt-detect>` block shrank from 9 lines to 4 on the common `clear` verdict (dropped `forced`/`global_flag`/`mode` and `scores` on non-ambiguous paths); the regression bench holds at **95% deterministic**, all cases green. The always-loaded `principles-global.md` shed its authoring guide (moved to `refs/authoring.md`, never loaded at runtime) and duplicated selection prose. Docs were de-duplicated: `CLAUDE.md` to a one-line hook contract, `README.md`'s repeated `--init` block and mode-flag rows merged, `ARCHITECTURE.md` refreshed with a Design Notes section. Deliberately **not** done: skipping the flash-mode Step 8 telemetry line, which would have desynced `--status`'s per-type counts (the hook line lacks `run_mode`) for a marginal saving.

## 2026-07-04

Robustness overhaul closing the gap between "fires on every prompt" and reality. The hook's `<prompt-detect>` block now ends with an explicit **ACTION line** instructing the model to invoke the skill — invocation no longer depends on a per-project CLAUDE.md rule — and the block is **suppressed entirely for passthrough prompts** (slash / ≤5 words / follow-ups), making block-present ⇒ invoke a binary contract. Detection was overhauled from 30% to **95% deterministic** on realistic prompts: ~45 new cues across all three categories (the literal word "code" was previously not a cue), a single-cue-with-zero-competitors rule resolves `clear`, zero-signal prompts resolve `global` deterministically, and the hook now agrees with `detect.md`'s fallback semantics (thresholds also defer to `categories.json` on the LLM path). A new 23-case regression bench (`tests/detect_bench.py`) guards the rate.

Comprehensive mode's double gate (Approve/Reject → Run/Terminate) collapsed into a single 3-way gate — **run enhanced · run original · edit** — so rejecting a rewrite never dead-ends the user's request; the telemetry outcome enum grew to `run / run_original / edited / terminated`. Flash mode now **never emits placeholders** (nothing would fill them before the rewrite runs). The Step 0.5 self-check also runs on explicit `--status`/`--help`/`--set-mode` paths, exactly when a user is inspecting a wounded install. The code principles gained **Verification & done criteria** (state how to confirm the change worked — the highest-leverage addition for agentic use); chain-of-thought was narrowed and demoted (modern models reason internally); the always-loaded worked examples were trimmed 17 → 5, cutting a recurring per-session token tax. Fixes: `allowed-tools` frontmatter key (underscore variant was silently ignored), dropped the inert `model:` pin, removed the repo-local hook that double-fired (and double-counted telemetry) alongside a global install, and `install.sh` now skips its copy phase when the target is a symlink (dev installs).

## 2026-06-27 (2)

Add dedication line to README and drop "(prompt-engineer)" qualifier from the install script banner text. Cosmetic only — no behaviour changes.

## 2026-06-27

Merged the standalone `refs/principles/examples.md` into the principle files and made worked examples a first-class, parsed input. Each principle file now ends with a **Worked examples** section: the five original multi-principle rewrites moved into `principles-global.md`, and a worked example was authored for every previously-uncovered principle across the global base (21 principles), code (6), question (5), and text-gen (5) files. The short authoring guide relocated into `principles-global.md`. Worked examples are no longer reference-only — protocol Step 3 now parses each `### heading` block, keys it to its principle (extending the tuple with a `worked_example` field, with a family-showcase fallback for the combined subtractive example), and Step 5 uses it alongside the row Exemplar as a rewrite pattern. Updated `SKILL.md` and `ARCHITECTURE.md` to match and removed all references to the deleted `examples.md`. Also includes a pre-existing staged change to `refs/detect.md` and the newly tracked `ARCHITECTURE.md`.

## 2026-06-26

Rebranded the skill from `prompt-engineer` to `wdym` and added two reliability features. **Self-healing** (protocol Step 0.5) runs once per session: it verifies the install against a known-good `refs/manifest.json` and applies a `sense → repair → escalate` policy — restoring a corrupt `pref.json`, recreating a missing `categories.json` from the pristine `refs/categories.default.json`, and re-wiring a stale hook path — while escalating (never clobbering) present-but-invalid files that may hold user edits. **Telemetry** adds a local, append-only `telemetry.jsonl`: `hooks/prompt-detect.py` writes one `src:"hook"` line per submission, protocol Step 8 writes one `src:"skill"` line per transformed run, and the new `hooks/telemetry-stats.py` renders a styled `/wdym --status` report (color on a TTY, monochrome when captured). The protocol grew from seven to eight steps. Added an `install.sh` installer and a real `README.md` with `asset/readme.jpg`. The hook now emits `verdict: degraded` when its config is unusable so the self-check can distinguish a broken config from a hook that never ran.

Added a `--init` mode (`refs/init.md`) that bootstraps the skill so it fires automatically — it installs the pref file and wires the `UserPromptSubmit` hook (absolute path to `prompt-detect.py`). Init now asks (via `AskUserQuestion`) whether to scope the install **locally** (`.claude/wdym/pref.json` + `.claude/settings.local.json` in the current directory) or **globally** (`~/.claude/wdym/pref.json` + `~/.claude/settings.json`, applying to every project); `--init --local` / `--init --global` skip the prompt. Step 0 resolves the pref file local-first, then global. Idempotent: never overwrites an existing pref or duplicates the hook. The skill-root `pref.json` is the bundled default template init copies. Added `Write`, `Edit`, and `Bash` to the skill's allowed tools.

Added `comprehensive` and `flash` run modes to the `wdym` skill. The mode is stored permanently as a key-value pair in `pref.json`, which the protocol now scans first (Step 0) on every run. Comprehensive mode (the default) presents the transformed prompt for approval and then asks whether to run it; flash mode rewrites and runs immediately with no gates. The mode switches permanently via `/wdym --set-mode --flash` / `--comprehensive` (or inline `--flash` / `--comprehensive` flags). Steps 6 and 7 are now mode-aware. When a comprehensive-mode session ends in terminate, the skill now emits a hint suggesting flash mode.

Added an empty `README.md` placeholder at the repo root.

Added prompt-type detection routing to the `wdym` skill. A deterministic `UserPromptSubmit` pre-scorer (`hooks/prompt-detect.py`) scores each prompt against a shared type taxonomy (`refs/categories.json`) and injects a `<prompt-detect>` block; the new detection protocol (`refs/detect.md`) consumes it, handles the `--global` escape hatch, and resolves a `prompt_type` (code, creative-writing, image-gen, question, text-gen, or none). Principles now layer a global base plus type-specific sections, and the protocol expands from six to seven steps. Detection hook wired in `.claude/settings.json`.

## 2026-06-24

Initialized the `wdym` skill — a `UserPromptSubmit` hook that automatically classifies, rewrites, and presents enhanced versions of user prompts before execution. Ships with a principles table (additive and subtractive) and a six-step protocol driving the full classify → select → rewrite → approve flow. Kermit changelog tooling also initialized.
