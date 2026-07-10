---
name: Heal Protocol
description: Self-check repair detail for wdym — read ONLY when the hook block is absent/degraded or carries a selfcheck failure line; the healthy path never loads this file
type: reference
---

# Heal Protocol

Reached from protocol Step 0.5 when something is wounded: no `<prompt-detect>`
block, `verdict: degraded`, or a `selfcheck:` failure line in the block. Runs at
most once per session. Two governing rules: **a missing file with a restore
source is recreated** (non-destructive); **a present-but-invalid file that may
hold user edits is escalated, never clobbered**. Read `refs/manifest.json` when
you need the full repair policy or schemas. Every repair is idempotent.

**Check 1 — Pref integrity.** Pref file (local `.claude/wdym/pref.json`, else
`~/.claude/wdym/pref.json`) exists but is unparseable, or `mode` is not
`comprehensive`/`flash` → overwrite that path with `{"mode": "comprehensive"}`.
Record `pref restored`. No pref at either scope → not a wound (created only by
`--init`).

**Check 2 — Hook health.**
- Block present with `verdict: degraded` → hook ran but its config is broken; go
  to Check 3.
- **No block** → read the resolved settings file (local `settings.local.json`,
  else global `settings.json`) for a `hooks.UserPromptSubmit` entry whose command
  contains `prompt-detect.py`:
  - Entry present **and** script path exists → wired but silent (e.g. `python3`
    unavailable). Record `hook silent`; do not repair.
  - Entry present **but** script path missing → stale path (skill dir moved).
    Rewrite the command to `python3 "<SKILL_DIR>/hooks/prompt-detect.py"` using
    the running skill's absolute root (merge rules: `refs/init.md` Step I4).
    Record `hook rewired`.
  - No matching entry → not installed. Escalate: hint `/wdym --init`.
  - Settings unparseable → escalate, do not clobber.

**Check 3 — `categories.json` integrity.**
- Missing → restore from `refs/categories.default.json`. Record `categories
  restored`.
- Present but invalid (unparseable / missing required keys / empty `categories`)
  → escalate, do not clobber; hint to restore from the default. Detection
  continues via the LLM path (`refs/detect.md`) this run.

**Check 4 — Principle files.**
- `refs/principles/principles-global.md` missing → escalate (core dependency).
- A per-type file missing → add its type to the session `missing_types` set
  (Step 3 falls back to the global base for that type). Record once.

**Check 5 — Telemetry tooling.**
- `hooks/telemetry-stats.py` missing → escalate (`/wdym --stats` can't
  aggregate). The data file `telemetry.jsonl` is excluded from healing —
  append-only, created lazily; absence is normal. Never restore, never escalate.

**Output.** One compact line, then continue the protocol:

```
Self-check: <repaired items>; <warnings/escalations>
```
