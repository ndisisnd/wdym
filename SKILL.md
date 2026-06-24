---
name: prompt-engineer
description: >
  Fires on UserPromptSubmit. Skips slash commands, ≤5-word prompts, and
  conversational follow-ups. For substantive prompts, selects top 2–3
  principles from refs/principles.md, rewrites the prompt, and presents
  the enhanced version for user approval before executing.
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

## Inputs

| Name | Format | Source |
|------|--------|--------|
| raw_prompt | Plain text string | `UserPromptSubmit` hook payload |
| principles | Markdown table | `refs/principles.md` |

## Outputs

| Name | Format | Destination |
|------|--------|-------------|
| enhanced_prompt | Plain text string | Presented inline for user approval |
| rationale_table | Markdown table, one row per principle | Shown alongside enhanced prompt |
| approval_gate | `AskUserQuestion` dialog | User approves or rejects the rewrite |
| run_choice | `AskUserQuestion` dialog | User runs the enhanced prompt or terminates |

## Step-by-step protocol

Follow `refs/protocol.md` end-to-end. It defines six steps: classify prompt, load principles, select top 2–3 principles, rewrite prompt, present for approval, run or terminate. Emit `Step X/6 — <title>` at the start of each step, unconditionally.

## Caching

Load `refs/principles.md` once at Step 2. Cache `principles_list` for the session. Place the principles table in the cached prefix of Anthropic API calls. Place the variable `raw_prompt` after the cache breakpoint. Mark the prefix with `cache_control: {"type": "ephemeral"}`.

## References

- `refs/protocol.md` — Six-step execution protocol the skill follows end-to-end
- `refs/principles.md` — Prompt engineering principles table; user-editable to add custom principles
