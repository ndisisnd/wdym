---
name: Command Protocol
description: Handles /wdym command flags — --init, --help, --status/--stats, --set-mode — reached from protocol Step 0 when a command flag is present
type: reference
---

# Command Protocol

Reached from `refs/protocol.md` Step 0 when the raw prompt carries a `/wdym`
command flag. Each command executes and then **terminates** — never continue to
Step 1, never enhance a prompt.

**Command prefix:** `/wdym` on Claude Code, `$wdym` on Codex. Recognise either
form on input; use the running host's form in anything shown to the user. This
document writes `/wdym`.

**Self-check ordering:** for `--help`, `--status`, and `--set-mode`, probe the
install first (slash commands get no hook block, so the hook's probe didn't run):
`ls` the five required files (`refs/categories.json`, `refs/categories.default.json`,
`refs/principles/principles-global.md`, `hooks/prompt-detect.py`,
`hooks/telemetry-stats.py`); on any failure read `refs/heal.md` and follow it.
Then execute the command. `--init` is the installer itself — no self-check; it
runs `refs/init.md`.

Dispatch on the first flag present, in this order:

## `--init`

Run `refs/init.md` end-to-end, then terminate. Do not run the self-check. It asks
two questions — scope (local vs. global) and activation (hook vs. on-demand) —
writes `pref.json`, wires or unwires the `UserPromptSubmit` hook to match, and
installs the trust-anchor contract in the host's instruction file (`CLAUDE.md` on
Claude Code, `AGENTS.md` on Codex — `refs/init.md` resolves which).

Both questions go through the **ask step** in `refs/protocol.md`, so they work on
a host without an `AskUserQuestion` tool.

This is the completion step for any install that delivered only the skill files
(`npx skills add`, a manual copy, a dev checkout) — those set up none of the
three.

Shortcut flags skip the matching question: `--local` / `--global` for scope,
`--hook` / `--on-demand` for activation. `--init` is also the *reconfiguration*
path — re-running it with `--hook` or `--on-demand` toggles activation in place,
preserving the existing `mode`.

## `--help`

Print `refs/help.txt` **verbatim inside a fenced code block**:

```bash
cat "<SKILL_DIR>/refs/help.txt"
```

Wrap its output in a fence so alignment survives, then terminate.

## `--status` (alias `--stats`)

Run the renderer (it resolves the active-scope `wdym/telemetry.jsonl` itself):

```bash
python3 "<SKILL_DIR>/hooks/telemetry-stats.py"
```

Print its output **verbatim inside a fenced code block** so table alignment and any
ANSI styling survive, then terminate. The script prints
`No telemetry recorded yet.` when the log is missing or empty.

## `--set-mode`

Explicit mode-management (e.g. `/wdym --set-mode --flash`). Read the target from the
accompanying `--flash` or `--comprehensive` token, set `mode` to it in the pref file
resolved in Step 0, emit `Run mode set to <target>.`, and terminate.

**Update the `mode` key in place — never replace the file's whole contents.** The
pref also carries `activation`; rewriting the file as `{"mode": "<target>"}` would
silently drop it and revert the user to on-demand. Read, set one key, write back.

If neither `--flash` nor `--comprehensive` accompanies `--set-mode`, emit the current
`run_mode` and ask the user which mode to set, then terminate.
