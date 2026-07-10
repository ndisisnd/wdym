---
name: Init Protocol
description: One-time bootstrap for the wdym skill — installs pref.json and wires the UserPromptSubmit hook, at local (this directory) or global (~/.claude) scope
type: reference
---

# Init Protocol

Triggered by `--init` (e.g. `/wdym --init`) from protocol Step 0. Bootstraps the
skill so it fires automatically on every prompt, at a scope the user chooses:

- **Local** — writes under the current directory's `.claude/`; applies only here.
- **Global** — writes under `~/.claude/`; applies to every project for this user.

Idempotent: re-running `--init` never overwrites an existing `pref.json` and never
duplicates the hook. After finishing, terminate — do not enhance any prompt.

## Step I1 — Resolve paths

- `SKILL_DIR` — the absolute path of this skill's root (the directory containing
  `SKILL.md` and `hooks/prompt-detect.py`). Resolve it from the running skill's own
  location. The hook script finds its own `refs/categories.json` relative to
  `__file__`, so only this absolute path is needed.

Confirm `SKILL_DIR/hooks/prompt-detect.py` exists before proceeding. If it does not,
report the problem and terminate without writing anything.

## Step I2 — Choose install scope

Call `AskUserQuestion` with these options:

- **Local (this directory)** — installs into `$CLAUDE_PROJECT_DIR/.claude/` (fall
  back to the current working directory). Fires only in this directory.
- **Global (all projects)** — installs into `~/.claude/`. Fires in every project for
  this user.

If the user shortcut the choice in their prompt — `--init --global` (or "globally")
→ Global; `--init --local` → Local — honour it and skip the question.

Resolve the chosen scope into:

| Variable | Local scope | Global scope |
|----------|-------------|--------------|
| `BASE_DIR` | `$CLAUDE_PROJECT_DIR/.claude` (or `./.claude`) | `~/.claude` |
| `PREF_PATH` | `BASE_DIR/wdym/pref.json` | `BASE_DIR/wdym/pref.json` |
| `SETTINGS_PATH` | `BASE_DIR/settings.local.json` (personal, not committed) | `BASE_DIR/settings.json` (global user settings) |

Writes are allowed **only** under the chosen `BASE_DIR`. Never write to the other
scope's location.

## Step I3 — Install the pref file

Path: `PREF_PATH`.

- Create the `BASE_DIR/wdym/` directory if needed.
- If `pref.json` already exists → leave it untouched (preserve the user's mode);
  note it as "already present".
- Otherwise → write the default `{"mode": "comprehensive"}`.

This is the file protocol Step 0 reads on every run.

## Step I4 — Wire the UserPromptSubmit hook

Target file: `SETTINGS_PATH` (`settings.local.json` for local scope,
`settings.json` for global scope).

**Local scope only — check the global settings file first.** Read
`~/.claude/settings.json` (or `$CLAUDE_CONFIG_DIR/settings.json`). If any
`hooks.UserPromptSubmit[].hooks[].command` there matches
`python3 ".*/hooks/prompt-detect\.py"` (any wdym install, not just this
`SKILL_DIR`), a wdym hook already fires in every project on this machine —
including this one. Skip hook wiring entirely: go straight to reporting
`pref.json` in Step I5 as the only local artifact. Local scope exists to
override the **pref** (`mode`), not to add a second hook — the global hook
already fires here, and protocol Step 0's local-overrides-global pref
resolution means the local `pref.json` alone is enough to change behaviour in
this project. Wiring a second hook would fire prompt-detect.py twice per
prompt (once from each settings file — Claude Code merges hook lists across
scopes, it does not dedupe by command string across files).

If no global hook is found (or scope is global), wire normally. The hook
entry to install (note the **absolute** `SKILL_DIR` path so it resolves no
matter what directory Claude runs from):

```json
{
  "type": "command",
  "command": "python3 \"<SKILL_DIR>/hooks/prompt-detect.py\""
}
```

Merge rules:

- If the settings file does not exist → create it with:
  ```json
  {
    "hooks": {
      "UserPromptSubmit": [
        { "hooks": [ { "type": "command", "command": "python3 \"<SKILL_DIR>/hooks/prompt-detect.py\"" } ] }
      ]
    }
  }
  ```
- If it exists → parse it, preserve every existing key, and append the hook entry
  under `hooks.UserPromptSubmit`. **Skip if an entry with the same
  `prompt-detect.py` command is already present** (idempotent — never duplicate).
- Write valid JSON only; if the existing file is unparseable, report it and stop
  rather than clobbering it.

## Step I5 — Confirm

Emit a short summary listing the scope and exactly what was created vs. left
untouched, e.g.:

```
Initialised wdym (global scope) in ~/.claude:
  • wdym/pref.json        — created (mode: comprehensive)
  • settings.json         — hook added (UserPromptSubmit → prompt-detect.py)
The skill now fires automatically on your prompts. Switch modes with
"/wdym --set-mode --flash".
```

When Step I4 skipped hook wiring because a global hook already covers this
project, say so explicitly instead of claiming a hook was added, e.g.:

```
Initialised wdym (local scope) in ./.claude:
  • wdym/pref.json        — created (mode: flash)
  • settings.local.json   — hook not added (already fires here via the global install)
This project now runs in flash mode; every other project keeps the global default.
```

Then terminate.
