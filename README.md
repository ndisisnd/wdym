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
./install.sh
```

Installing elsewhere:

```bash
CLAUDE_CONFIG_DIR=~/.config/claude ./install.sh   # different config dir
SKILL_NAME=wdym ./install.sh                       # different skill name
```

Once it's installed, run:

```bash
wdym --init
```

## ❓ How it works

### The usual run

Just write and `wdym` will translate it for you.

1. **Catches it** — a `UserPromptSubmit` hook intercepts the prompt. Slash commands, tiny ≤5-word prompts, and "thanks"/"ok"/"continue"-style follow-ups get waved straight through untouched. No ceremony for small talk.
2. **Figures out what you meant** — classifies the prompt as `code`, `question`, `text-gen`, or `none`.
3. **Loads the right playbook** — pulls the global principles plus the ones specific to your prompt type, then picks the top 2–3 that actually apply. It strips noise (politeness, threats, bribes, hedging) _before_ it adds structure (specificity, goals, format).
4. **Rewrites it** — turns your blabber into something your LLM can actually chew on, and shows you _why_ each change was made.
5. **Ships it** — in **comprehensive** mode it shows you the before/after and waits for your nod; in **flash** mode it just sends the polished version and gets out of the way.

That's it. You write like a human, your LLM reads like it's being respected.

### Initialising

`./install.sh` only puts the files on disk. `wdym --init` is what actually arms it:

```bash
wdym --init
```

It asks one thing: **local or global?**

- **Local** — wires the hook and pref into _this_ project's `.claude/`. Only this repo gets the treatment.
- **Global** — wires it into `~/.claude/`, so every project you touch gets it.

Local always wins over global when both exist, so you can run it globally and still override per-project. `--init` writes your `pref.json` (where your run mode lives) and hooks up the `UserPromptSubmit` detector. Run it again any time — it's idempotent and won't clobber your edits.

## 🌟 Modes

`wdym` runs in two persistent **run modes** and takes a handful of **flags** to switch behaviour. Drop any of these into a prompt _(or run them standalone)_:

| Mode / Flag | What it does |
|---|---|
| `comprehensive` _(default)_ | Shows you the original, the rationale, and the enhanced prompt — then waits for your approval before running. Cautious by design. |
| `flash` | Skips the approval gate entirely. Rewrites your prompt and fires it off immediately. For when you trust the glow-up. |
| `--comprehensive` / `--flash` | Permanently switches your stored run mode and continues with this run. |
| `--set-mode --flash` / `--set-mode --comprehensive` | Switches the stored mode _without_ touching the current prompt — pure mode management, then exits. |
| `--global` | Forces the universal principle base and skips type detection for this run. Good for one-off, type-agnostic prompts. |
| `--init` | Bootstraps the skill — writes `pref.json` and wires the hook, asking local vs. global scope. |
| `--status` _(alias `--stats`)_ | Prints a styled usage report — prompts seen, transform rate, a ranked by-type breakdown. Telemetry stays 100% local. |

---

_Dedicated to my love Joan Chiang who runs 10x more prompts than I do._