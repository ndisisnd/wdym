# Releases

What's new for you, release by release.

## v1.2.0 — 2026-08-09

> wdym is no longer a Claude Code tool. It runs on Codex too, and one command —
> `npx wdym-prompt` — now installs and wires it on either host, or both at once. The README
> finally shows you the whole flow in a single picture instead of describing it in prose.

### ✨ New
- **Codex support.** wdym classifies, rewrites, and gates prompts in Codex the same way it
  does in Claude Code. Install it with `npx wdym-prompt --codex`, or `--both` to cover both
  hosts at once.
- **One install command.** `npx wdym-prompt` detects which hosts you have, lays down the
  skill, wires the hook, writes the trust contract, and creates your preferences — no
  follow-up step. Re-run it any time to update.
- **`--doctor`.** Ask wdym what is actually installed: which hosts are wired and whether
  the two skill copies agree. Codex keeps hook approval to itself, so `--doctor` reminds
  you to confirm it with `/hooks` rather than pretending to know.
- **`--uninstall`.** Removes the skill, the hook entry, and the contract block, and leaves
  your preferences and usage history alone unless you pass `--force`.
- **A flow diagram in the README.** One picture covering both activation modes, the
  prompts that pass straight through, and both run modes — with a short table naming the
  four things that differ between Claude Code and Codex.

### 📈 Improved
- The approval gate and `--init` now ask their questions in whatever way the host you are
  on supports, so they work everywhere instead of only where Claude Code's question tool
  exists.
- One preferences file serves both hosts, so your run mode can never disagree between
  Claude Code and Codex.
- Your Codex copy of the skill is a link to the Claude Code copy, so updating one updates
  the other and the two cannot quietly drift apart.
- Re-running an installer over an install that ended up with two wdym hooks now collapses
  them back to one, which stops the double rewrite and double usage counting that caused.

### 🐛 Fixed
- Launching your agent inside a subfolder of a project no longer misses that project's
  local wdym settings.
- The one-line signal wdym emits no longer names a Claude-specific file, so it reads
  correctly on any host.

### ⚠️ Known limitations
- **Codex asks you to approve the hook after every install or update.** Codex trusts hooks
  by their contents, so any change invalidates the previous approval. Run `/hooks` in Codex
  and approve the wdym hook, or wdym stays silent without telling you. The installer says
  so at the end of every Codex run.
- **Codex shows wdym's classification line.** Codex currently renders hook context as a
  visible message ([openai/codex#16933](https://github.com/openai/codex/issues/16933)), so
  you will see a one-line signal above each answer. Cosmetic only.
- **Codex is global-only.** wdym applies to every project there; per-repo Codex installs
  are deliberately refused.
- **The shell installer is frozen and stays Claude Code only.** `curl … install.sh` keeps
  working exactly as it did; it will not gain Codex support. Use `npx wdym-prompt` for
  that.

## v1.1.0 — 2026-07-30

> You now control when wdym fires — on every prompt automatically, or only when you ask —
> and its rewriting playbook has been rebuilt around what actually improves results with
> today's AI models, dropping folklore that no longer helps.

### ✨ New
- Choose your activation style at install time or with `/wdym --init`: have wdym fire on
  every prompt automatically, or keep it silent until you call `/wdym` yourself.

### 📈 Improved
- Rewrites are modernised for current AI models: tricks that no longer help (role-play
  openers, worked examples, "think step by step" prodding, threats and bribes) are gone,
  and change requests now get clear boundaries so the agent touches only what you asked for.
- When you say "this" or "that", the rewrite now fills in what you meant from the
  conversation instead of leaving a blank for you to complete.

### 🐛 Fixed
- wdym now fires reliably — previously the assistant could mistake wdym's own trigger
  signal for a suspicious injected instruction and refuse to run it.
- Writing and business prompts are no longer treated as coding tasks just because they
  contain a word like "script" or "compile" — a video script or a compiled list of
  competitors now gets writing guidance, not code guidance.

## v1.0.0 — 2026-07-18

> The first public release of wdym. Install with one command, and it now covers every
> project by default; prompt rewriting costs about half what it used to, and a prompt
> that's already clear and well-structured skips the rewrite entirely instead of being
> shown a diff for no reason.

### ✨ New
- wdym now recognizes a prompt that's already clear and well-structured and leaves it
  alone — no rewrite, no diff to review, nothing shown.
- Public documentation: an MIT license, a security policy for reporting issues privately,
  and an `llms.txt` index so AI agents landing in the repo know what to read first.

### 📈 Improved
- Rewriting a prompt now costs roughly half the tokens and round trips it used to on the
  common path, so the gate between "you typed something" and "your prompt runs" is faster.
- Re-running the installer is safe at any time — it won't duplicate the hook or overwrite
  your saved mode preference.

### 🐛 Fixed
- A local and a global install no longer both fire on the same prompt — previously this
  could score and rewrite a single prompt twice.

### ⚠️ Breaking
- Installing wdym now defaults to a **global** setup (`~/.claude/skills/wdym`) covering
  every project you touch, after briefly defaulting to a per-project install. Pass
  `--local` to scope it to just the current project instead.
