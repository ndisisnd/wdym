# Architecture

## User Flow

```
User types a prompt and submits
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  UserPromptSubmit Hook  (prompt-detect.py — deterministic)      │
│                                                                 │
│  Score prompt against categories.json (keyword/regex)          │
│  Flag passthrough (slash/≤5 words/follow-up) in telemetry      │
│  Emit <prompt-detect> block: verdict + scores + candidates      │
│  Append src:"hook" line → telemetry.jsonl                       │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  SKILL.md execution begins                                      │
│                                                                 │
│  Step 0    Read pref.json → run_mode                           │
│          │ Handle --init / --status / --set-mode flags          │
│          ▼                                                      │
│  Step 0.5  Self-check against manifest.json                    │
│          │ Heal missing / corrupt files silently                │
│          ▼                                                      │
│  Step 1    Check passthrough conditions                        │
│          │                                                      │
│          ├── passthrough ──────────────────────────────────────►│ (no-op, terminate)
│          │                                                      │
│          ▼                                                      │
│  Step 2    Classify prompt type                                │
│          │ Read <prompt-detect> verdict from hook               │
│          │ • clear    → trust directly                          │
│          │ • ambiguous→ adjudicate among candidates             │
│          │ • degraded → run manual LLM algorithm                │
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
│          │ AskUserQuestion: Approve | Reject                    │
│          │                                                      │
│          ├── Reject ──────────────────────────────────────────►│ (terminate)
│          │                                                      │
│          ▼                                                      │
│  Step 7    Submit enhanced_prompt                              │
│          │ Flash: immediate                                      │
│          │ Comprehensive: Run | Terminate                        │
│          ▼                                                      │
│  Step 8    Append src:"skill" line → telemetry.jsonl          │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
    Enhanced prompt sent to Claude
```

## File Map

```
wdym/
├── SKILL.md                        Execution protocol (Steps 0–8)
├── pref.json                       Default mode template
├── install.sh                      Installation helper
├── hooks/
│   ├── prompt-detect.py            UserPromptSubmit pre-scorer
│   └── telemetry-stats.py          --status report renderer
└── refs/
    ├── protocol.md                 Step-by-step reference
    ├── detect.md                   Type detection algorithm
    ├── init.md                     --init bootstrap protocol
    ├── manifest.json               Self-check & repair definitions
    ├── categories.json             Type taxonomy (user-editable)
    ├── categories.default.json     Pristine restore copy
    └── principles/
        ├── principles-global.md    21 universal principles (always loaded)
        ├── principles-code.md      Code-specific principles
        ├── principles-question.md  Question-specific principles
        └── principles-text-gen.md  Text-gen principles
                                    (each file ends with worked examples, parsed and attached per principle; global base also carries the authoring guide)
```

## Run Modes

| Mode          | Step 6 (approval) | Step 7 (submit)     |
|---------------|--------------------|---------------------|
| comprehensive | Show diff, ask     | Ask Run / Terminate |
| flash         | Skipped            | Immediate           |

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

**Tier 3 — threshold scoring.** Winner must reach `min_score` (default 2) with a lead of at least `min_lead` (default 1) over the runner-up. Ties or weak signals fall back to `verdict: ambiguous`.

The `question` category uses two `force_regex` patterns — `^(is|are|do|does|did|should|will|...)\\b` and `\\?\\s*$` — with the full negative list (`write`, `draft`, `function`, `summarize`, …) acting as the cancellation guard. `can`/`could`/`would` are intentionally excluded from the interrogative pattern because they double as polite-request starters for code and text-gen tasks.
