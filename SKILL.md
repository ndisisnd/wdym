---
name: prompt-engineer
description: >
  Fires on UserPromptSubmit. Skips slash commands, ≤5-word prompts, and
  conversational follow-ups. For substantive prompts, routes through a
  prompt-detect protocol that sets prompt_type (code, creative-writing, image-gen,
  question, text-gen, or none), loads the global base plus any matching type-specific
  principles, selects top 2–3, rewrites the prompt, and presents the enhanced
  version for user approval before executing. Supports a --global flag that
  forces the universal base and skips detection.
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

`prompt_type` ∈ `code` · `creative-writing` · `image-gen` · `question` · `text-gen` · `none`.

A `UserPromptSubmit` hook (`hooks/prompt-detect.py`) deterministically pre-scores the prompt against `refs/categories.json` and injects a `<prompt-detect>` block. The skill trusts a `clear`/`global` verdict and only adjudicates `ambiguous` cases — keeping the common path deterministic and token-free.

## Inputs

| Name | Format | Source |
|------|--------|--------|
| raw_prompt | Plain text string | `UserPromptSubmit` hook payload |
| detect | Markdown protocol | `refs/detect.md` |
| principles | Markdown tables (global base + type sections) | `refs/principles.md` |

## Outputs

| Name | Format | Destination |
|------|--------|-------------|
| prompt_type | Enum string | Cached; routes principle loading |
| mode | `global` / `typed:<prompt_type>` | Cached; selects the principle pool |
| enhanced_prompt | Plain text string | Presented inline for user approval |
| rationale_table | Markdown table, one row per principle | Shown alongside enhanced prompt |
| approval_gate | `AskUserQuestion` dialog | User approves or rejects the rewrite |
| run_choice | `AskUserQuestion` dialog | User runs the enhanced prompt or terminates |

## Step-by-step protocol

Follow `refs/protocol.md` end-to-end. It defines seven steps: classify prompt, detect prompt type, load principles, select top 2–3 principles, rewrite prompt, present for approval, run or terminate. Emit `Step X/7 — <title>` at the start of each step, unconditionally.

## Caching

Load `refs/principles.md` once at Step 3. Cache `prompt_type`, `mode`, and `principles_list` for the session. Place the global base table in the cached prefix of Anthropic API calls — it is loaded on every run. Place the variable `raw_prompt` (and the per-run type section) after the cache breakpoint. Mark the prefix with `cache_control: {"type": "ephemeral"}`.

## References

- `refs/detect.md` — Prompt detection protocol: hook consumption, `--global` handling, type taxonomy, resolution algorithm
- `refs/categories.json` — Single source of truth for the type taxonomy and signal cues; shared by the hook and detect.md
- `hooks/prompt-detect.py` — Deterministic `UserPromptSubmit` pre-scorer; wired in `.claude/settings.json`
- `refs/protocol.md` — Seven-step execution protocol the skill follows end-to-end
- `refs/principles.md` — Global base + type-specific principle tables; user-editable to add custom principles
