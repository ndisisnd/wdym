---
name: wdym
description: >
  Prompt rewriter that fires automatically on UserPromptSubmit via a hook-injected
  <prompt-detect> block; skips slash commands, ≤5-word prompts, and follow-ups.
  Detects prompt type (code, question, text-gen) and rewrites using 2–3 matched
  principles; comprehensive mode gates the rewrite for approval, flash mode runs it
  immediately. Manage with /wdym --init, --status, --set-mode, --help.
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Bash
---

# wdym

Fires automatically on `UserPromptSubmit` — no slash command needed. The hook
injects a `<prompt-detect>` block for substantive prompts only; **block present ⇒
invoke this skill, block absent ⇒ respond normally**. Also triggers on "improve /
enhance / rewrite this prompt".

## Execution

**Follow `refs/protocol.md` end-to-end.** It defines Step 0 (scan pref), Step 0.5
(self-check), and Steps 1–8 (classify · detect · load principles · select 2–3 ·
rewrite · gate · run · record telemetry).

If the prompt carries a `/wdym` command flag — `--init`, `--help`, `--status`
(alias `--stats`), or `--set-mode` — **follow `refs/commands.md` instead** (run the
self-check first, execute the command, terminate; do not enhance a prompt). Inline
`--flash` / `--comprehensive` / `--global` flags are handled within protocol Step 0/2.

**Output discipline:** emit no step markers. Visible output is limited to the
self-check repair line (Step 0.5, only when something was healed) and the rewritten
prompt alone (Step 6, comprehensive mode only) — never the original prompt or the
principles/rationale behind the rewrite. Flash mode emits nothing extra.

## Run modes

The persistent run mode lives in `pref.json`, resolved local-first: 
`$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json`, else `~/.claude/wdym/pref.json`. A
local pref overrides a global one. Missing/unparseable → default `comprehensive`.

| Run mode | Behaviour |
|----------|-----------|
| `comprehensive` (default) | Presents only the rewritten prompt (no original, no rationale), then one gate: run enhanced · run original · edit. The request is never dead-ended. |
| `flash` | Rewrites and runs immediately — no gate, no placeholders. |

Switch permanently with `/wdym --set-mode --flash` (or `--comprehensive`), or an
inline `--flash` / `--comprehensive` flag that also runs the current prompt.

## Principle caching

Principle files under `refs/principles/` load lazily. Read each file **at most once
per session**; rebuild `principles_list` per run from cached parses (`global base ∪
this run's type`). See protocol Step 3.

## References

- `refs/protocol.md` — execution protocol (Steps 0–8)
- `refs/commands.md` — `--init` / `--help` / `--status` / `--set-mode` handling
- `refs/detect.md` — type detection (read only when the hook verdict is ambiguous/absent)
- `refs/categories.json` — type taxonomy + signal cues (source of truth, user-editable)
- `refs/categories.default.json` — pristine restore source for categories.json
- `refs/manifest.json` — self-check install definition (read only on a failed check)
- `refs/init.md` — `--init` bootstrap detail (local vs global scope)
- `refs/help.txt` — verbatim `--help` text (printed via `cat`)
- `refs/authoring.md` — how to add custom principles
- `refs/principles/` — `principles-global.md` (always) + `principles-code/question/text-gen.md`
- `hooks/prompt-detect.py` — deterministic pre-scorer + `src:"hook"` telemetry
- `hooks/telemetry-stats.py` — `--status` report renderer
