# wdym Auto-Invoke

The hook's `<prompt-detect>` block now carries its own ACTION line instructing invocation, and it is suppressed entirely for passthrough prompts. This file restates the contract as defense-in-depth:

- **`<prompt-detect>` block present** (any verdict: `clear`, `ambiguous`, `global`, `degraded`) — invoke the `wdym` skill via the Skill tool **before** processing the user's prompt. A `global` verdict means detection resolved to the universal base (the skill handles it; no flag needed).
- **No block** — the prompt is passthrough (slash command, ≤5 words, or conversational follow-up) or the hook is not installed; respond normally, do not invoke wdym.
