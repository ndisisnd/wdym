# Architecture

## User Flow

```
User types a prompt and submits
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  UserPromptSubmit Hook  (prompt-detect.py — deterministic)      │
│                                                                 │
│  Passthrough (slash/≤5 words/follow-up)?                        │
│    → NO block emitted; telemetry line only. Prompt runs as-is.  │
│  Otherwise:                                                     │
│    Score prompt against categories.json (keyword/regex)         │
│    Emit minimal <prompt-detect> block: verdict (+ type on       │
│      clear, + scores/candidates on ambiguous)                   │
│    Block is a signal; host's trust contract → invoke skill      │
│    Append src:"hook" line → telemetry.jsonl                     │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  SKILL.md execution begins                                      │
│                                                                 │
│  Step 0    Read pref.json → run_mode                           │
│          │ /wdym command flags → refs/commands.md, terminate    │
│          ▼                                                      │
│  Step 0.5  Self-check (ls existence probe;                     │
│          │ manifest.json read only on a failed check)           │
│          │ Heal missing / corrupt files silently                │
│          ▼                                                      │
│  Step 1    Passthrough check (no-hook fallback only —           │
│          │ block present ⇒ substantive, skip to Step 2)         │
│          ├── passthrough ──────────────────────────────────────►│ (no-op, terminate)
│          │                                                      │
│          ▼                                                      │
│  Step 2    Classify prompt type                                │
│          │ Adopt <prompt-detect> verdict from hook              │
│          │ • clear    → trust directly (detect.md NOT read)     │
│          │ • global   → universal base (zero signal / --global) │
│          │ • ambiguous→ read detect.md, adjudicate candidates   │
│          │ • degraded/no block → read detect.md, manual LLM     │
│          │ Output: prompt_type (code|question|                  │
│          │         text-gen|none) + mode                        │
│          ▼                                                      │
│  Step 3    Load principles (lazy, cached per session)          │
│          │ Always: principles-global.md                         │
│          │ If typed: principles-<type>.md                       │
│          ▼                                                      │
│  Step 4    Score & select top 2–3 principles                   │
│          │ Subtractive > Additive > type-specific               │
│          ▼                                                      │
│  Step 5    Rewrite prompt                                      │
│          │ Output: enhanced_prompt + rationale_table            │
│          ▼                                                      │
│  Step 6    [comprehensive mode only]                           │
│          │ Show original → rationale → enhanced                 │
│          │ Ask step — present options and stop:                 │
│          │   Run enhanced | Run original | Edit                 │
│          │   AskUserQuestion when that tool exists,             │
│          │   otherwise plain text + end of turn                 │
│          │                                                      │
│          ├── cancel (via "Other") ────────────────────────────►│ (terminate + hint)
│          │                                                      │
│          ▼                                                      │
│  Step 7    Submit chosen prompt                                │
│          │ Flash: enhanced, immediately (no placeholders)       │
│          │ Comprehensive: whatever the gate resolved            │
│          ▼                                                      │
│  Step 8    Append src:"skill" line → telemetry.jsonl          │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
    Enhanced prompt sent to the model
```

The flow above is host-independent. What differs between Claude Code and Codex is
plumbing only — see [Two-host model](#two-host-model).

## File Map

```
wdym/
├── SKILL.md                        Thin dispatcher → refs/protocol.md
├── pref.json                       Default mode template
├── package.json                    npm package `wdym-prompt` (bin, files allowlist)
├── install.sh                      Shell installer — Claude Code only, frozen
├── agents/
│   └── openai.yaml                 Codex skill manifest (display name, invocation policy)
├── bin/
│   └── wdym-prompt.js              npx installer — both hosts, no dependencies
├── hooks/
│   ├── prompt-detect.py            UserPromptSubmit pre-scorer
│   └── telemetry-stats.py          --status report renderer
├── tests/
│   ├── detect_bench.py             Detection regression bench (expected verdicts)
│   └── token_bench.py              Token-cost bench for the common path
└── refs/
    ├── protocol.md                 Step-by-step execution reference (Steps 0–8, ask step)
    ├── commands.md                 /wdym command handling (--init/--help/--status/--set-mode)
    ├── help.txt                    Verbatim --help text (printed via cat)
    ├── detect.md                   Manual type-detection path (ambiguous/absent only)
    ├── init.md                     --init bootstrap protocol (host resolution, scope, activation)
    ├── heal.md                     Self-check repair playbook (Step 0.5 escalation)
    ├── manifest.json               Self-check & repair definitions (read only on a failed check)
    ├── categories.json             Type taxonomy (user-editable)
    ├── categories.default.json     Pristine restore copy
    ├── authoring.md                How to add custom principles (not loaded at runtime)
    └── principles/
        ├── principles-global.md    Universal principles (always loaded)
        ├── principles-code.md      Code-specific principles
        ├── principles-question.md  Question-specific principles
        └── principles-text-gen.md  Text-gen principles
                                    (each file ends with worked examples, parsed and attached per principle)
```

## Design Notes

**Token budget.** SKILL.md is a thin dispatcher, not the protocol — its body is
re-injected on every skill invocation, so operational detail lives in `refs/*` that
load only on the paths that need them. On the common path (hook verdict `clear`/`global`,
healthy install) a run reads only `protocol.md` + `principles-global.md` (+ one type
file, once per session); `detect.md`, `manifest.json`, `commands.md`, and `help.txt`
stay off the hot path.

**Per-file principle caching.** A session's `prompt_type` changes between prompts (a
code edit, then a conceptual question). Caching one fixed principle list would serve the
wrong pool after a switch; caching *per file* rebuilds `principles_list = global base ∪
this run's type` from cache each run while still reading each file only once. A
code→question→code session reads `global`, `code`, `question` once each — the second
code prompt reads nothing.

**Degrade, then heal.** The skill degrades gracefully through any single wound (dead
hook → LLM detection, missing pref → comprehensive, missing type file → global base).
Degradation keeps a run alive but never closes the wound — it would run degraded forever,
silently. The Step 0.5 self-check adds the missing half (sense → repair → escalate) once
per session so the skill recovers. The telemetry stream is deliberately outside this
layer: append-only, best-effort, never healed, so it can never block or alter a run.

**Trust anchor, not injection.** The `<prompt-detect>` block arrives through the hook's
`additionalContext` channel — the same low-trust surface as tool output and retrieved
text. An override-shaped imperative there (`ACTION: invoke … BEFORE processing`) reads as
a prompt injection and was sometimes refused, silently skipping the skill. So the block
carries only a neutral classification *signal* — host-neutral wording, naming no host's
files — while the invoke instruction lives in the host's own instruction file, which the
model treats as trusted user configuration. Both installers write a marker-delimited,
idempotent contract there at the install scope: `~/.claude/CLAUDE.md` or the local project
root on Claude Code, `$CODEX_HOME/AGENTS.md` on Codex. A fresh install therefore carries
the same authority the dev repo does rather than leaving the block to fend for itself.

## Two-host model

wdym runs on Claude Code and on Codex. The engine — hook scoring, classification,
principle selection, rewriting, telemetry — is identical on both. Only the plumbing is
host-specific, and it is enumerated in one place so the rest of the system never has to
know which host it is on. Four of these matter at runtime — trust contract, skill path,
hook file, and the ask step — and those are the four the README's diagram note names.

| | Claude Code | Codex |
|---|---|---|
| Host evidence | `CLAUDE_PROJECT_DIR` set, or `~/.claude/` exists | `CODEX_HOME` set, or `~/.codex/` exists |
| Skill path | `~/.claude/skills/wdym` (canonical), or `<project>/.claude/skills/wdym` | `~/.agents/skills/wdym` |
| Hook file | `~/.claude/settings.json`, or `<project>/.claude/settings.local.json` | `$CODEX_HOME/hooks.json` |
| Trust contract | `~/.claude/CLAUDE.md`, or `<project>/CLAUDE.md` | `$CODEX_HOME/AGENTS.md` |
| Ask step | `AskUserQuestion` | plain-text options, end of turn |
| Command prefix | `/wdym` | `$wdym` |
| Scopes | global and local | global only |

**One canonical copy, exposed twice.** The skill tree is installed once, under
`~/.claude/skills/wdym`. Codex only scans `~/.agents/skills`, so the installer exposes the
same tree there as a symlink rather than copying it. Two independent copies would drift the
moment one host updated and the other didn't, and drift in a skill body is invisible until
behaviour diverges. Where symlinks are unavailable (or `--copy` is passed) the installer
copies instead and records which it did in `pref.json` as `codex_skill_mode`, so
`--doctor` knows whether it needs to check the two paths for drift.

**One pref file, both hosts.** `~/.claude/wdym/pref.json` is canonical for Claude Code and
Codex alike, even though the rest of the Codex wiring lives under `~/.codex`. Splitting it
would let a user set flash mode in one host and comprehensive in the other and then wonder
which one they were talking to. Local scope still overrides global — but local scope is a
Claude Code concept, so the override applies there only.

**Ask step, not a tool call.** `AskUserQuestion` is a Claude Code tool and does not exist
in Codex, and it was the one hard dependency that made the approval gate and `--init`
unrunnable there. Both now route through a single documented interaction step — present
options, stop, read the next message as the answer — with the implementation picked by
*tool availability*, never by guessing the host. That way a host that gains or loses the
tool needs no code change.

**Trust lifecycle differs.** Claude Code approves a hook once. Codex trusts hooks by file
contents, so any install, update, or re-run invalidates the previous approval and the hook
goes silent until the user runs `/hooks` in Codex and approves it again — with no warning
that it stopped firing. Codex also records approval outside any file this tool can read, so
there is neither a programmatic approval path nor a readable trust state. Both are handled
by documentation loudness instead: the installer prints an action-required notice last on
every Codex-touching run, `--doctor` reports trust as `unknown` and points at `/hooks`,
`refs/heal.md` knows the "wired but silent" failure mode, and the README repeats it in the
Codex notes.

**Codex is global-scope only.** A repo-scoped Codex hook would live in a committed file,
so every teammate pulling the repo would get an approval prompt for a tool they never
installed. Repo scope also collides with Codex sessions that start below the repo root.
`--codex --local` therefore refuses cleanly and writes nothing rather than half-wiring.

## Run Modes

| Mode          | Step 6 (gate)                              | Step 7 (submit)          |
|---------------|--------------------------------------------|--------------------------|
| comprehensive | Run enhanced · Run original · Edit         | Whatever the gate chose  |
| flash         | Skipped                                    | Enhanced, immediate      |

Switch with `/wdym --set-mode --flash` or `/wdym --set-mode --comprehensive`. Persisted in `pref.json`.

## Telemetry Streams

Two append-only streams merge into `wdym/telemetry.jsonl`:

- `src:"hook"` — written by `prompt-detect.py` on every submission (provisional verdict)
- `src:"skill"` — written by Step 8 on every substantive run (final outcome)

View with `/wdym --status`.

## Detection Scoring

The hook scores the prompt against every category in `categories.json` and resolves a verdict in three tiers:

**Tier 1 — `--global` flag.** Present anywhere in the prompt → `verdict: global`, skip scoring.

**Tier 2 — `force_regex` (structural overrides).** Each category may carry `force_regex` patterns for signals that are structurally unambiguous (e.g. a fenced code block forces `code`). A category is treated as *forced* only when:
1. At least one `force_regex` pattern matches, **and**
2. Its net score (after the `negative` list is applied) is **> 0** — negatives can cancel a force signal entirely.

When one or more categories are forced, forced resolution applies: the top-scoring forced category wins **only if its score ≥ the top non-forced category score**. If a non-forced category outscores all forced ones, the forced signal is overridden and normal threshold scoring (Tier 3) takes over. This prevents a weak interrogative match from hijacking a clearly code or text-gen prompt.

**Tier 3 — threshold scoring.** Four deterministic outcomes:
1. Winner reaches `min_score` (default 2) with a `min_lead` (default 1) margin → `verdict: clear`.
2. Winner has any signal (≥1) and every other category scored 0 → `verdict: clear` — a single cue with zero competitors is unambiguous.
3. All categories scored 0 → `verdict: global` — zero signal deterministically falls back to the universal base.
4. Competing non-zero scores with no clear winner → `verdict: ambiguous`, tied leaders listed as `candidates` for LLM adjudication. This is the only non-deterministic path (~5% of realistic prompts; see `tests/detect_bench.py`).

The `question` category uses two `force_regex` patterns — `^(is|are|do|does|did|should|will|...)\\b` and `\\?\\s*$` — with the full negative list (`write`, `draft`, `function`, `summarize`, …) acting as the cancellation guard. `can`/`could`/`would` are intentionally excluded from the interrogative pattern because they double as polite-request starters for code and text-gen tasks.
