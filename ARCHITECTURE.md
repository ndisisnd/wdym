# Architecture

## User Flow

```
User types a prompt and submits
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  UserPromptSubmit Hook  (prompt-detect.py — deterministic)      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Passthrough check                                       │   │
│  │  • starts with "/"  → verdict: global                   │   │
│  │  │ ≤ 5 words        → verdict: global                   │   │
│  │  └ follow-up phrase → verdict: global                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                    │                                            │
│                    ▼                                            │
│  Score prompt against categories.json (keyword/regex)          │
│  Emit <prompt-detect> block: verdict + scores + candidates      │
│  Append src:"hook" line → telemetry.jsonl                       │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  SKILL.md execution begins                                      │
│                                                                 │
│  Step 0  (Haiku)   Read pref.json → run_mode                   │
│          │         Handle --init / --status / --set-mode flags  │
│          ▼                                                      │
│  Step 0.5 (Haiku)  Self-check against manifest.json            │
│          │         Heal missing / corrupt files silently        │
│          ▼                                                      │
│  Step 1  (Haiku)   Re-check passthrough conditions             │
│          │                                                      │
│          ├── passthrough ──────────────────────────────────────►│ (no-op, terminate)
│          │                                                      │
│          ▼                                                      │
│  Step 2  (Haiku)   Classify prompt type                        │
│          │         Read <prompt-detect> verdict from hook       │
│          │         • clear    → trust directly                  │
│          │         • ambiguous→ adjudicate among candidates     │
│          │         • degraded → run manual LLM algorithm        │
│          │         Output: prompt_type (code|question|          │
│          │                 text-gen|none) + mode                │
│          ▼                                                      │
│  Step 3  (Haiku)   Load principles (lazy, cached per session)  │
│          │         Always: principles-global.md                 │
│          │         If typed: principles-<type>.md               │
│          ▼                                                      │
│  Step 4  (Sonnet)  Score & select top 2–3 principles           │
│          │         Subtractive > Additive > type-specific       │
│          ▼                                                      │
│  Step 5  (Sonnet)  Rewrite prompt                              │
│          │         Output: enhanced_prompt + rationale_table    │
│          ▼                                                      │
│  Step 6  (Haiku)   [comprehensive mode only]                   │
│          │         Show original → rationale → enhanced         │
│          │         AskUserQuestion: Approve | Reject            │
│          │                                                      │
│          ├── Reject ──────────────────────────────────────────►│ (terminate)
│          │                                                      │
│          ▼                                                      │
│  Step 7  (Haiku)   Submit enhanced_prompt                      │
│          │         Flash: immediate                             │
│          │         Comprehensive: Run | Terminate               │
│          ▼                                                      │
│  Step 8  (Haiku)   Append src:"skill" line → telemetry.jsonl  │
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
        ├── principles-global.md    17 universal principles (always loaded)
        ├── principles-code.md      Code-specific principles
        ├── principles-question.md  Question-specific principles
        └── principles-text-gen.md  Text-gen principles
                                    (each file ends with worked examples, parsed and attached per principle; global base also carries the authoring guide)
```

## Model Assignment

| Steps       | Model  | Reason                                     |
|-------------|--------|--------------------------------------------|
| 0, 0.5, 1–3 | Haiku  | Lightweight reads, deterministic checks    |
| 4–5         | Sonnet | Principle scoring and prompt rewriting     |
| 6–8         | Haiku  | Approval UI and telemetry                  |

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
