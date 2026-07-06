---
name: Command Protocol
description: Handles /wdym command flags — --init, --help, --status/--stats, --set-mode — reached from protocol Step 0 when a command flag is present
type: reference
---

# Command Protocol

Reached from `refs/protocol.md` Step 0 when the raw prompt carries a `/wdym`
command flag. Each command executes and then **terminates** — never continue to
Step 1, never enhance a prompt.

**Self-check ordering:** for `--help`, `--status`, and `--set-mode`, run the
**Step 0.5 self-check first** (an explicit `/wdym` command is exactly when a wounded
install should be sensed and reported), then execute the command. `--init` is the
installer itself — it does **not** run the self-check; it runs `refs/init.md`.

Dispatch on the first flag present, in this order:

## `--init`

Run `refs/init.md` end-to-end (it asks local vs. global scope, writes the pref file,
and wires the `UserPromptSubmit` hook), then terminate. Do not run the self-check.

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
accompanying `--flash` or `--comprehensive` token, write `{"mode": "<target>"}` to
the pref file resolved in Step 0, emit `Run mode set to <target>.`, and terminate.

If neither `--flash` nor `--comprehensive` accompanies `--set-mode`, emit the current
`run_mode` and ask the user which mode to set, then terminate.
