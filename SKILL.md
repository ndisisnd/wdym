---
name: wdym
description: >
  Prompt rewriter that fires automatically on UserPromptSubmit via a hook-injected
  <prompt-detect> block. Detects prompt type (code, question, text-gen) and rewrites
  using 2–3 matched principles; flash mode runs immediately, comprehensive gates for
  approval. Manage with /wdym --init, --status, --set-mode, --help.
allowed-tools:
  - AskUserQuestion
  - Read
  - Write
  - Edit
  - Bash
---

# wdym

Fires automatically on `UserPromptSubmit`: `<prompt-detect>` block present ⇒ run
this skill; absent ⇒ respond normally. Also triggers on "improve / enhance /
rewrite this prompt".

**Follow `refs/protocol.md` end-to-end** (Steps 0–8). If the prompt carries a
`/wdym` command flag (`--init` / `--help` / `--status` / `--set-mode`), follow
`refs/commands.md` instead and terminate — never enhance a prompt. Inline
`--flash` / `--comprehensive` / `--global` flags are handled inside the protocol.

**Output discipline:** no step markers, no original prompt, no principles or
rationale. Visible output is only the self-check repair line (when something was
healed) and, in comprehensive mode, the rewritten prompt plus its gate. Flash mode
emits nothing extra.

**Caching:** read each ref/principle file at most once per session; rebuild the
working principle pool per run from cached parses.
