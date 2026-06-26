---
name: Init Protocol
description: One-time local bootstrap for the prompt-engineer (wdym) skill — installs pref.json and wires the UserPromptSubmit hook, scoped to the current directory only
type: reference
---

# Init Protocol

Triggered by `--init` (e.g. `/wdym --init`) from protocol Step 0. Bootstraps the
skill into the directory the user is running it from so it fires automatically on
every prompt. **Local scope only** — everything is written under the current
directory's `.claude/`. Never touch the global `~/.claude` or any settings outside
the target directory.

Idempotent: re-running `--init` never overwrites an existing `pref.json` and never
duplicates the hook. After finishing, terminate — do not enhance any prompt.

## Step I1 — Resolve paths

- `SKILL_DIR` — the absolute path of this skill's root (the directory containing
  `SKILL.md` and `hooks/prompt-detect.py`). Resolve it from the running skill's own
  location. The hook script finds its own `refs/categories.json` relative to
  `__file__`, so only this absolute path is needed.
- `TARGET_DIR` — the directory the user ran `--init` in: `$CLAUDE_PROJECT_DIR`
  (fall back to the current working directory). This is the **only** place writes
  are allowed.

Confirm `SKILL_DIR/hooks/prompt-detect.py` exists before proceeding. If it does not,
report the problem and terminate without writing anything.

## Step I2 — Install the local pref file

Path: `TARGET_DIR/.claude/wdym/pref.json`.

- Create the `TARGET_DIR/.claude/wdym/` directory if needed.
- If `pref.json` already exists → leave it untouched (preserve the user's mode);
  note it as "already present".
- Otherwise → write the default `{"mode": "comprehensive"}`.

This is the file protocol Step 0 reads on every run.

## Step I3 — Wire the UserPromptSubmit hook (local settings)

Target file: `TARGET_DIR/.claude/settings.local.json` — the personal, project-local
settings file (not committed), which keeps the install scoped to this user and this
directory.

The hook entry to install (note the **absolute** `SKILL_DIR` path so it resolves no
matter what directory Claude runs from):

```json
{
  "type": "command",
  "command": "python3 \"<SKILL_DIR>/hooks/prompt-detect.py\""
}
```

Merge rules:

- If `settings.local.json` does not exist → create it with:
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

## Step I4 — Confirm

Emit a short summary listing exactly what was created vs. left untouched, e.g.:

```
Initialised wdym in <TARGET_DIR> (local scope):
  • .claude/wdym/pref.json        — created (mode: comprehensive)
  • .claude/settings.local.json   — hook added (UserPromptSubmit → prompt-detect.py)
The skill now fires automatically on your prompts. Switch modes with
"/wdym --set-mode --flash".
```

Then terminate.
