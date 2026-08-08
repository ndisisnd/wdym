---
name: Heal Protocol
description: Self-check repair detail for wdym — read ONLY when the hook block is absent/degraded or carries a selfcheck failure line; the healthy path never loads this file
type: reference
---

# Heal Protocol

Reached from protocol Step 0.5 when something is wounded: `verdict: degraded`, a
`selfcheck:` failure line in the block, or no `<prompt-detect>` block **while
`activation` is `hook`**. A missing block under `activation: on-demand` is the
expected state and never reaches this file. Runs at most once per session. Two governing rules: **a missing file with a restore
source is recreated** (non-destructive); **a present-but-invalid file that may
hold user edits is escalated, never clobbered**. Read `refs/manifest.json` when
you need the full repair policy or schemas. Every repair is idempotent.

**Check 1 — Pref integrity.** Pref file (local `.claude/wdym/pref.json`, else
`~/.claude/wdym/pref.json`) exists but is unparseable, or `mode` is not
`comprehensive`/`flash` → rewrite that path with `mode: "comprehensive"`,
preserving a valid `activation`. If `activation` is present but not
`hook`/`on-demand` → set it to `on-demand` (the inert setting; never escalate a
user into an automatic hook they did not choose). Record `pref restored`. A
**missing** `activation` key is not a wound — it predates the key and correctly
means on-demand. No pref at either scope → not a wound (created only by
`--init`).

**Check 2 — Hook health.** Assessed **only when `activation` is `hook`**. Under
`on-demand` the hook is meant to be absent or silent, so no finding here is a
wound: record nothing, escalate nothing, and skip to Check 3. This gate is what
keeps a deliberately manual install from being diagnosed as a broken automatic
one.

- Block present with `verdict: degraded` → hook ran but its config is broken; go
  to Check 3.
- **No block** (and `activation: hook`) → read the host's resolved hook file
  (`refs/init.md` Step I1 names it per host: Claude Code local
  `settings.local.json` else global `settings.json`; Codex `~/.codex/hooks.json`)
  for a `UserPromptSubmit` entry whose command contains `prompt-detect.py`:
  - Entry present **and** script path exists → wired but silent (e.g. `python3`
    unavailable; on Codex, most often an unapproved hook — it trusts hooks by
    file contents, so any reinstall revokes approval and it fails silently).
    Record `hook silent`; do not repair. On Codex, hint `/hooks` to approve it.
  - Entry present **but** script path missing → stale path (skill dir moved).
    Rewrite the command to `python3 "<SKILL_DIR>/hooks/prompt-detect.py"` using
    the running skill's absolute root (merge rules: `refs/init.md` Step I5).
    Record `hook rewired`.
  - No matching entry → pref says `hook` but nothing is wired: the two halves of
    the setting disagree. Escalate: hint `/wdym --init --hook` to wire it, or
    `/wdym --init --on-demand` to make the pref match reality.
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
