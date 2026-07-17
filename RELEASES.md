# Releases

What's new for you, release by release.

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
