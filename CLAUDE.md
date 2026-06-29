# wdym Auto-Invoke

When your context contains a `<prompt-detect>` block injected by the UserPromptSubmit hook:

- **`verdict: clear` or `verdict: ambiguous`** — invoke the `wdym` skill via the Skill tool **before** processing the user's prompt.
- **`verdict: global`** — invoke `wdym` with `--global`.
- **`verdict: degraded`** — invoke `wdym` (self-check will heal the config).
- **Passthrough signals** (`verdict` absent, prompt is a slash command, ≤5 words, or conversational follow-up) — respond normally; do not invoke wdym.
