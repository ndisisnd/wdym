---
name: wdym
description: >
  Rewrite, improve, or enhance a prompt. Runs on /wdym, on any request to
  improve/enhance/rewrite a prompt, and on a UserPromptSubmit <prompt-detect>
  block. Detects prompt type (code, question, text-gen) and rewrites using 2–3
  matched principles; flash mode rewrites immediately, comprehensive mode
  presents the rewrite and waits for approval. Manage with /wdym --init,
  --status, --set-mode, --help.
---

# wdym

**Host portability.** wdym runs on any agent host with a `UserPromptSubmit`
hook. Two things vary by host while the skill is running (a third set — where
installed files land — is resolved by `refs/init.md`, and only during `--init`):

- **Command prefix** — `/wdym` on Claude Code, `$wdym` on Codex. This skill
  writes `/wdym` throughout; use the running host's prefix in anything shown to
  the user.
- **Asking the user** — the *ask step* in `refs/protocol.md`. Use the
  `AskUserQuestion` tool when it is available, otherwise ask in plain text and
  end the turn. Choose by whether that tool is available, never by guessing
  which host you are on.

**Activation** is set by `pref.json`'s `activation` key and chosen at
`/wdym --init`:

- `hook` — fires on `UserPromptSubmit`. `<prompt-detect>` block present ⇒ run
  this skill; absent ⇒ respond normally.
- `on-demand` — no hook fires; prompts arrive with no block, which the protocol
  handles via its no-hook fallback paths.

Either way, an explicit `/wdym <prompt>` or a request to "improve / enhance /
rewrite this prompt" runs the skill.

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
