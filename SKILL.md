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
  terminate in comprehensive mode, hints the user toward flash mode.
model: claude-sonnet-4-6
allowed_tools:
  - AskUserQuestion
  - Read
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

Run `/wdym --init` in any directory to install the skill there. It is **scoped to that local directory only** — it never touches global `~/.claude` settings. Init:

1. Writes the local pref file at `.claude/wdym/pref.json` (default `{"mode": "comprehensive"}`).
2. Wires the `UserPromptSubmit` hook into `.claude/settings.local.json` with an absolute path to `hooks/prompt-detect.py`, so the skill fires automatically on every prompt.

Init is idempotent: it never overwrites an existing `pref.json` and never duplicates the hook. See `refs/init.md` for the full bootstrap protocol.

## Run modes

The skill **always scans the local pref file first** (Step 0) to read the persistent run mode. The pref file is `$CLAUDE_PROJECT_DIR/.claude/wdym/pref.json` — local to the directory the user works in. The mode controls the approval gates, not which principles are loaded.

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
| run_mode | `comprehensive` / `flash` | Local pref file `.claude/wdym/pref.json` `mode` key (scanned first, Step 0) |
| raw_prompt | Plain text string | `UserPromptSubmit` hook payload |
| detect | Markdown protocol | `refs/detect.md` |
| principles | Markdown tables (global base + type sections) | `refs/principles.md` |

## Outputs

| Name | Format | Destination |
|------|--------|-------------|
| run_mode | `comprehensive` / `flash` | Read from `.claude/wdym/pref.json` at Step 0; gates Steps 6–7 |
| prompt_type | Enum string | Cached; routes principle loading |
| mode | `global` / `typed:<prompt_type>` | Cached; selects the principle pool |
| enhanced_prompt | Plain text string | Presented inline for user approval |
| rationale_table | Markdown table, one row per principle | Shown alongside enhanced prompt |
| approval_gate | `AskUserQuestion` dialog | User approves or rejects the rewrite |
| run_choice | `AskUserQuestion` dialog | User runs the enhanced prompt or terminates |

## Step-by-step protocol

Follow `refs/protocol.md` end-to-end. A preliminary Step 0 scans `pref.json` for the run mode and applies any `--flash` / `--comprehensive` switch. The seven numbered steps are: classify prompt, detect prompt type, load principles, select top 2–3 principles, rewrite prompt, present for approval, run or terminate. Emit `Step X/7 — <title>` at the start of each numbered step, unconditionally. In flash mode, Steps 6 and 7 collapse to an immediate run with no gates.

## Caching

Load `refs/principles.md` once at Step 3. Cache `prompt_type`, `mode`, and `principles_list` for the session. Place the global base table in the cached prefix of Anthropic API calls — it is loaded on every run. Place the variable `raw_prompt` (and the per-run type section) after the cache breakpoint. Mark the prefix with `cache_control: {"type": "ephemeral"}`.

## References

- `refs/init.md` — Local bootstrap protocol for `--init`: installs the pref file and wires the `UserPromptSubmit` hook, scoped to the current directory only
- `pref.json` — Bundled default template (`{"mode": "comprehensive"}`); init copies it to the local `.claude/wdym/pref.json` that is scanned first on every run
- `refs/detect.md` — Prompt detection protocol: hook consumption, `--global` handling, type taxonomy, resolution algorithm
- `refs/categories.json` — Single source of truth for the type taxonomy and signal cues; shared by the hook and detect.md
- `hooks/prompt-detect.py` — Deterministic `UserPromptSubmit` pre-scorer; wired into the local `.claude/settings.local.json` by `--init`
- `refs/protocol.md` — Execution protocol (Step 0 preference scan + seven numbered steps) the skill follows end-to-end
- `refs/principles.md` — Global base + type-specific principle tables; user-editable to add custom principles
