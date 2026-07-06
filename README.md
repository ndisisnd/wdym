<div align="center">
<img src="asset/readme.jpg"/>

# wdym 🗣️❓

_What are you even saying bruh_

Your brain's rampaging with ideas. You write your prompt. But you think: am I missing something? Is this written properly? Will my LLM think that I'm stupid? _(no it won't)_

Introducing `wdym`: a robust, comprehensive skill that translates your blabber into the best possible slop that your LLM can understand without having a token aneurysm.

</div>

## ⚒️ Installation

```bash
git clone https://github.com/ndisisnd/wdym.git
cd wdym
./install.sh     # global by default; prefix CLAUDE_CONFIG_DIR=… or SKILL_NAME=… to override
```

`./install.sh` only puts the files on disk. `wdym --init` is what arms it — and it asks one thing: **local or global?**

```bash
wdym --init
```

- **Local** — wires the hook and pref into _this_ project's `.claude/`. Only this repo gets the treatment.
- **Global** — wires it into `~/.claude/`, so every project you touch gets it.

Local always wins over global when both exist, so you can run it globally and still override per-project. `--init` writes your `pref.json` (where your run mode lives) and hooks up the `UserPromptSubmit` detector. It's idempotent — run it again any time and it won't clobber your edits.

## ❓ How it works

Just write, and `wdym` translates it for you:

1. **Catches it** — a `UserPromptSubmit` hook intercepts the prompt. Slash commands, ≤5-word prompts, and "thanks"/"ok"/"continue" follow-ups wave straight through untouched — no ceremony for small talk.
2. **Figures out what you meant** — classifies the prompt as `code`, `question`, `text-gen`, or `none`. ~95% of real prompts resolve deterministically in the hook (zero tokens); only genuinely mixed signals go to the LLM to adjudicate.
3. **Loads the right playbook** — pulls the global principles plus the ones for your prompt type, then picks the top 2–3 that actually apply. It strips noise (politeness, threats, bribes, hedging) _before_ adding structure (specificity, goals, format).
4. **Rewrites it** — turns your blabber into something your LLM can actually chew on, and shows you _why_ each change was made.
5. **Ships it** — how it submits depends on your run mode (see below). Either way your prompt always runs; rejecting the glow-up never eats your question.

That's it. You write like a human, your LLM reads like it's being respected.

## 🌟 Modes

`wdym` runs in two persistent **run modes** and takes a handful of **flags**. Drop any of these into a prompt _(or run them standalone)_:

| Mode / Flag | What it does |
|---|---|
| `comprehensive` _(default)_ | Shows you the original, the rationale, and the enhanced prompt — then one 3-way gate: **run enhanced · run original · edit**. Cautious by design, but your prompt always runs. |
| `flash` | Skips the gate entirely. Rewrites your prompt and fires it off immediately — and never inserts `[fill-this-in]` placeholders, since nothing would fill them. |
| `--flash` / `--comprehensive` | Permanently switch your stored run mode (add `--set-mode` to switch _without_ touching the current prompt). |
| `--global` | Forces the universal principle base and skips type detection for this run. Good for one-off, type-agnostic prompts. |
| `--init` | Bootstraps the skill — writes `pref.json` and wires the hook, asking local vs. global scope. |
| `--status` _(alias `--stats`)_ | Prints a styled usage report — prompts seen, transform rate, a ranked by-type breakdown. Telemetry stays 100% local. |
| `--help` | Lists all commands, modes, and prompt types with one-liners. |

---

_Dedicated to my love JC who runs 10x more prompts than I do._
