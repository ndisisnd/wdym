# Releases

What's new for you, release by release.

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
