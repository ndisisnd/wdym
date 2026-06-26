---
name: prompt-engineer
description: >
  Fires on UserPromptSubmit. Skips slash commands, ≤5-word prompts, and
  conversational follow-ups. Always scans pref.json first for the persistent run
  mode (comprehensive or flash). For substantive prompts, routes through a
  prompt-detect protocol that sets prompt_type (code, question, text-gen, or none),
  loads the global base plus any matching type-specific
  principles, selects top 2–3, and rewrites the prompt. In comprehensive mode
  (default) it presents the enhanced version for approval before running; in flash
  mode it rewrites and runs immediately. Supports a --global flag that forces the
  universal base and skips detection, and --comprehensive / --flash flags (or
  the /wdym --set-mode command) that permanently switch the stored mode. On
  terminate in comprehensive mode, hints the user toward flash mode. A --init
  command installs the pref file and wires the UserPromptSubmit hook, asking
  whether to scope it locally (this directory) or globally (~/.claude).
model: claude-sonnet-4-6
allowed_tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Bash
---

## Usage

**Invoke**: Fires automatically on `UserPromptSubmit`. No slash command needed.

- Hook: `UserPromptSubmit` — fires on every user prompt submission
- Natural-language: "improve this prompt", "enhance my prompt", "rewrite this prompt"
- Context: any substantive user message submitted to Claude Code

## Modes

| Mode | Trigger | Principles loaded |
|------|---------|-------------------|
| `global` | `--global` flag, or detection finds no clear type | Global base only — universal, academically-grounded principles |
| `typed:<prompt_type>` | Detection resolves a clear `prompt_type` | Global base **+** the one matching type-specific section, layered |

`prompt_type` ∈ `code` · `question` · `text-gen` · `none`.

A `UserPromptSubmit` hook (`hooks/prompt-detect.py`) deterministically pre-scores the prompt against `refs/categories.json` and injects a `<prompt-detect>` block. The skill trusts a `clear`/`global` verdict and only adjudicates `ambiguous` cases — keeping the common path deterministic and token-free.

## Install (`--init`)

Run `/wdym --init` to install the skill. It asks (via `AskUserQuestion`) which **scope** to install at:

- **Local (this directory)** — writes `.claude/wdym/pref.json` and wires the hook into `.claude/settings.local.json`. Applies only in this directory.
- **Global (all projects)** — writes `~/.claude/wdym/pref.json` and wires the hook into `~/.claude/settings.json`. Applies to every project for this user.

You can skip the prompt with `/wdym --init --global` or `/wdym --init --local`. Either way init writes the chosen pref file (default `{"mode": "comprehensive"}`) and a `UserPromptSubmit` hook with an absolute path to `hooks/prompt-detect.py`, so the skill fires automatically on every prompt.

Init is idempotent: it never overwrites an existing `pref.json` and never duplicates the hook. See `refs/init.md` for the full bootstrap protocol.

## Run modes

The skill **scans the pref file first** (Step 0) to read the persistent run mode. It resolves the pref file by checking the **local** path (`$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json`) first, then the **global** path (`~/.claude/wdym/pref.json`) — a local pref overrides a global one. The mode controls the approval gates, not which principles are loaded.

| Run mode | Stored as | Behaviour |
|----------|-----------|-----------|
| `comprehensive` | `{"mode": "comprehensive"}` | **Default.** Presents the transformed prompt for approval, then asks again whether to run it (Steps 6 → 7). |
| `flash` | `{"mode": "flash"}` | Transforms the prompt and runs it immediately — no approval gate, no run prompt. |

The pref file persists the mode as a single key-value pair across sessions. Switch it permanently with:

- `/wdym --set-mode --flash` or `/wdym --set-mode --comprehensive` — explicit mode-management command; sets and persists the mode, confirms, and terminates without enhancing a prompt.
- An inline `--flash` / `--comprehensive` flag in any substantive prompt — sets and persists the mode, is stripped from the prompt, and the run continues normally.

If the pref file is missing or unparseable, the skill defaults to `comprehensive` for the run (the file is created only by `--init`). The skill-root `pref.json` is the bundled default template init copies.

When a comprehensive-mode session ends in **terminate** (Reject at Step 6 or Terminate at Step 7), the skill emits a one-line hint suggesting flash mode: `Want to automatically transform your prompts without approval? Set to flash mode instead by running "/wdym --set-mode --flash"`. The hint never fires in flash mode or when the user runs the enhanced prompt.

## Inputs

| Name | Format | Source |
|------|--------|--------|
| run_mode | `comprehensive` / `flash` | Pref file `mode` key — local `.claude/wdym/pref.json`, else global `~/.claude/wdym/pref.json` (scanned first, Step 0) |
| raw_prompt | Plain text string | `UserPromptSubmit` hook payload |
| detect | Markdown protocol | `refs/detect.md` |
| principles | Markdown tables, split by type | `refs/principles/` (global base + per-type files) |

## Outputs

| Name | Format | Destination |
|------|--------|-------------|
| run_mode | `comprehensive` / `flash` | Read from the local or global `wdym/pref.json` at Step 0; gates Steps 6–7 |
| prompt_type | Enum string | Cached; routes principle loading |
| mode | `global` / `typed:<prompt_type>` | Cached; selects the principle pool |
| enhanced_prompt | Plain text string | Presented inline for user approval |
| rationale_table | Markdown table, one row per principle | Shown alongside enhanced prompt |
| approval_gate | `AskUserQuestion` dialog | User approves or rejects the rewrite |
| run_choice | `AskUserQuestion` dialog | User runs the enhanced prompt or terminates |

## Step-by-step protocol

Follow `refs/protocol.md` end-to-end. A preliminary Step 0 scans `pref.json` for the run mode and applies any `--flash` / `--comprehensive` switch. The seven numbered steps are: classify prompt, detect prompt type, load principles, select top 2–3 principles, rewrite prompt, present for approval, run or terminate. Emit `Step X/7 — <title>` at the start of each numbered step, unconditionally. In flash mode, Steps 6 and 7 collapse to an immediate run with no gates.

## Caching

Principles are loaded lazily and cached **per file** across the session, so each prompt reads only what isn't already in context. Two layers:

1. **Split by type.** Principles live in `refs/principles/`: `principles-global.md` (always loaded) plus one file per `prompt_type` (`principles-code.md`, `principles-question.md`, `principles-text-gen.md`). A run reads the global base + at most one type file — never the whole pool. Worked examples and the authoring guide live in `examples.md`, which is **never read at runtime**.

2. **Read each file at most once per session.** Step 3 keeps a session `loaded` set and skips the `Read` for any file already in context. The global base is read on the first substantive prompt and reused; each type file is read lazily, only the first time that type appears. `principles_list` is **rebuilt per run** from the cached parses (`global base ∪ rows for this run's type`) — not frozen — so a session whose `prompt_type` switches (code → question → code) stays correct while still reading each file only once.

Claude Code applies ephemeral prompt-caching to the stable conversation prefix automatically; keeping the principle files unchanged within a session lets those reads bill at cache rates. The skill does not set `cache_control` itself — it has no control over the API call; it minimises tokens by *not re-reading* files instead.

## References

- `refs/init.md` — Bootstrap protocol for `--init`: asks local vs. global scope, installs the pref file and wires the `UserPromptSubmit` hook accordingly
- `pref.json` — Bundled default template (`{"mode": "comprehensive"}`); init copies it to the local `.claude/wdym/pref.json` or global `~/.claude/wdym/pref.json` that is scanned first on every run
- `refs/detect.md` — Prompt detection protocol: hook consumption, `--global` handling, type taxonomy, resolution algorithm
- `refs/categories.json` — Single source of truth for the type taxonomy and signal cues; shared by the hook and detect.md
- `hooks/prompt-detect.py` — Deterministic `UserPromptSubmit` pre-scorer; wired by `--init` into `.claude/settings.local.json` (local) or `~/.claude/settings.json` (global)
- `refs/protocol.md` — Execution protocol (Step 0 preference scan + seven numbered steps) the skill follows end-to-end
- `refs/principles/` — Principle tables split by type: `principles-global.md` (always loaded) + `principles-code.md` / `principles-question.md` / `principles-text-gen.md` (one per run, lazily). `examples.md` holds worked examples and the authoring guide (documentation only, never read at runtime). User-editable to add custom principles.
