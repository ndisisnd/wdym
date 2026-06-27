# Changelog

All notable changes to this project will be documented here.

## 2026-06-27 (2)

Add dedication line to README and drop "(prompt-engineer)" qualifier from the install script banner text. Cosmetic only — no behaviour changes.

## 2026-06-27

Merged the standalone `refs/principles/examples.md` into the principle files and made worked examples a first-class, parsed input. Each principle file now ends with a **Worked examples** section: the five original multi-principle rewrites moved into `principles-global.md`, and a worked example was authored for every previously-uncovered principle across the global base (21 principles), code (6), question (5), and text-gen (5) files. The short authoring guide relocated into `principles-global.md`. Worked examples are no longer reference-only — protocol Step 3 now parses each `### heading` block, keys it to its principle (extending the tuple with a `worked_example` field, with a family-showcase fallback for the combined subtractive example), and Step 5 uses it alongside the row Exemplar as a rewrite pattern. Updated `SKILL.md` and `ARCHITECTURE.md` to match and removed all references to the deleted `examples.md`. Also includes a pre-existing staged change to `refs/detect.md` and the newly tracked `ARCHITECTURE.md`.

## 2026-06-26

Rebranded the skill from `prompt-engineer` to `wdym` and added two reliability features. **Self-healing** (protocol Step 0.5) runs once per session: it verifies the install against a known-good `refs/manifest.json` and applies a `sense → repair → escalate` policy — restoring a corrupt `pref.json`, recreating a missing `categories.json` from the pristine `refs/categories.default.json`, and re-wiring a stale hook path — while escalating (never clobbering) present-but-invalid files that may hold user edits. **Telemetry** adds a local, append-only `telemetry.jsonl`: `hooks/prompt-detect.py` writes one `src:"hook"` line per submission, protocol Step 8 writes one `src:"skill"` line per transformed run, and the new `hooks/telemetry-stats.py` renders a styled `/wdym --status` report (color on a TTY, monochrome when captured). The protocol grew from seven to eight steps. Added an `install.sh` installer and a real `README.md` with `asset/readme.jpg`. The hook now emits `verdict: degraded` when its config is unusable so the self-check can distinguish a broken config from a hook that never ran.

Added a `--init` mode (`refs/init.md`) that bootstraps the skill so it fires automatically — it installs the pref file and wires the `UserPromptSubmit` hook (absolute path to `prompt-detect.py`). Init now asks (via `AskUserQuestion`) whether to scope the install **locally** (`.claude/wdym/pref.json` + `.claude/settings.local.json` in the current directory) or **globally** (`~/.claude/wdym/pref.json` + `~/.claude/settings.json`, applying to every project); `--init --local` / `--init --global` skip the prompt. Step 0 resolves the pref file local-first, then global. Idempotent: never overwrites an existing pref or duplicates the hook. The skill-root `pref.json` is the bundled default template init copies. Added `Write`, `Edit`, and `Bash` to the skill's allowed tools.

Added `comprehensive` and `flash` run modes to the `wdym` skill. The mode is stored permanently as a key-value pair in `pref.json`, which the protocol now scans first (Step 0) on every run. Comprehensive mode (the default) presents the transformed prompt for approval and then asks whether to run it; flash mode rewrites and runs immediately with no gates. The mode switches permanently via `/wdym --set-mode --flash` / `--comprehensive` (or inline `--flash` / `--comprehensive` flags). Steps 6 and 7 are now mode-aware. When a comprehensive-mode session ends in terminate, the skill now emits a hint suggesting flash mode.

Added an empty `README.md` placeholder at the repo root.

Added prompt-type detection routing to the `wdym` skill. A deterministic `UserPromptSubmit` pre-scorer (`hooks/prompt-detect.py`) scores each prompt against a shared type taxonomy (`refs/categories.json`) and injects a `<prompt-detect>` block; the new detection protocol (`refs/detect.md`) consumes it, handles the `--global` escape hatch, and resolves a `prompt_type` (code, creative-writing, image-gen, question, text-gen, or none). Principles now layer a global base plus type-specific sections, and the protocol expands from six to seven steps. Detection hook wired in `.claude/settings.json`.

## 2026-06-24

Initialized the `wdym` skill — a `UserPromptSubmit` hook that automatically classifies, rewrites, and presents enhanced versions of user prompts before execution. Ships with a principles table (additive and subtractive) and a six-step protocol driving the full classify → select → rewrite → approve flow. Kermit changelog tooling also initialized.
